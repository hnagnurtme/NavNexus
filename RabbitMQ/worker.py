"""
Enhanced RabbitMQ Worker for processing PDF jobs
Integrates with main_pipeline.py for consistent processing logic

IMPROVEMENTS:
- ✅ Processes ALL files in batch (no data loss)
- ✅ Proper error handling and retry logic
- ✅ Uses main_pipeline.py for consistency
- ✅ Health checks and monitoring
- ✅ Graceful shutdown
- ✅ Progress tracking per file
- ✅ Structured logging
- ✅ Connection pooling
"""
import os
import sys
import json
import time
import signal
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# RabbitMQ and Firebase clients
from src.rabbitmq_client import RabbitMQClient
from src.handler.firebase import FirebaseClient

# Main pipeline - SINGLE SOURCE OF TRUTH
from src.pipeline.main_pipeline import process_pdf_to_knowledge_graph

# Database connections
from neo4j import GraphDatabase
from qdrant_client import QdrantClient

# ================================
# CONFIGURATION
# ================================

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('PDFWorker')

# RabbitMQ Configuration
RABBITMQ_CONFIG = {
    "Host": os.getenv("RABBITMQ_HOST", "chameleon-01.lmq.cloudamqp.com"),
    "Username": os.getenv("RABBITMQ_USERNAME", "odgfvgev"),
    "Password": os.getenv("RABBITMQ_PASSWORD", "ElA8Lhgv15r8Y0IR6n0S5bMLxGRmUmgg"),
    "VirtualHost": os.getenv("RABBITMQ_VHOST", "odgfvgev")
}

QUEUE_NAME = os.getenv("QUEUE_NAME", "pdf_jobs_queue")

# Database Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "https://4d5d9646-deff-46bb-82c5-1322542a487e.eu-west-2-0.aws.cloud.qdrant.io")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwiZXhwIjoxNzY4MjE5NzE1fQ.A-Ma6ZzfzR1EYnf3_YuUWPhXmAU-xJU2ZA-OL6oECJw")

NEO4J_URL = os.getenv("NEO4J_URL", "neo4j+s://daa013e6.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "DTG0IyhifivaD2GwRoyIz4VPapRF0JdjoVsMfT9ggiY")

# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT = os.getenv("FIREBASE_SERVICE_ACCOUNT", "serviceAccountKey.json")
FIREBASE_DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL", "https://navnexus-default-rtdb.firebaseio.com/")

# Worker Configuration
MAX_CONCURRENT_FILES = int(os.getenv("MAX_CONCURRENT_FILES", "3"))
MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))  # seconds

# Graceful shutdown flag
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ================================
# DATABASE CLIENT INITIALIZATION
# ================================

class DatabaseClients:
    """Singleton for database clients with connection pooling"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseClients, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not DatabaseClients._initialized:
            self._initialize_clients()
            DatabaseClients._initialized = True

    def _initialize_clients(self):
        """Initialize database clients with proper configuration"""
        logger.info("🔧 Initializing database clients...")

        try:
            # Neo4j with connection pooling
            self.neo4j_driver = GraphDatabase.driver(
                NEO4J_URL,
                auth=(NEO4J_USER, NEO4J_PASSWORD),
                max_connection_lifetime=3600,  # 1 hour
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )

            # Test Neo4j connection
            with self.neo4j_driver.session() as session:
                session.run("RETURN 1")
            logger.info("✓ Neo4j connected")

            # Qdrant client
            self.qdrant_client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY,
                timeout=60
            )
            logger.info("✓ Qdrant connected")

            # Firebase client
            if not os.path.exists(FIREBASE_SERVICE_ACCOUNT):
                raise FileNotFoundError(
                    f"Firebase service account key not found: {FIREBASE_SERVICE_ACCOUNT}"
                )

            self.firebase_client = FirebaseClient(
                FIREBASE_SERVICE_ACCOUNT,
                FIREBASE_DATABASE_URL
            )
            logger.info("✓ Firebase connected")

            logger.info("✅ All database clients initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize database clients: {e}")
            raise

    def close(self):
        """Close all database connections"""
        logger.info("🔌 Closing database connections...")

        try:
            if hasattr(self, 'neo4j_driver'):
                self.neo4j_driver.close()
                logger.info("✓ Neo4j connection closed")
        except Exception as e:
            logger.error(f"Error closing Neo4j: {e}")

        logger.info("✅ All connections closed")


# ================================
# FILE PROCESSING WITH RETRY
# ================================

def process_single_file_with_retry(
    workspace_id: str,
    pdf_url: str,
    job_id: str,
    db_clients: DatabaseClients,
    attempt: int = 1
) -> Dict[str, Any]:
    """
    Process a single PDF file with retry logic

    Args:
        workspace_id: Workspace identifier
        pdf_url: URL of PDF to process
        job_id: Job identifier
        db_clients: Database clients instance
        attempt: Current attempt number

    Returns:
        Processing result dictionary
    """
    file_name = pdf_url.split('/')[-1]

    logger.info(f"📄 Processing file {file_name} (attempt {attempt}/{MAX_RETRY_ATTEMPTS})")

    try:
        # Call main pipeline (SINGLE SOURCE OF TRUTH)
        result = process_pdf_to_knowledge_graph(
            workspace_id=workspace_id,
            pdf_url=pdf_url,
            file_name=file_name,
            job_id=f"{job_id}_file_{file_name}",
            neo4j_driver=db_clients.neo4j_driver,
            qdrant_client=db_clients.qdrant_client,
            config=None  # Use default config from main_pipeline
        )

        # Add file-specific metadata
        result['pdf_url'] = pdf_url
        result['file_name'] = file_name
        result['attempts'] = attempt

        logger.info(f"✅ Successfully processed {file_name}")
        return result

    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Error processing {file_name} (attempt {attempt}): {error_msg}")

        # Retry logic
        if attempt < MAX_RETRY_ATTEMPTS:
            wait_time = RETRY_DELAY * (2 ** (attempt - 1))  # Exponential backoff
            logger.info(f"⏳ Retrying in {wait_time}s...")
            time.sleep(wait_time)

            return process_single_file_with_retry(
                workspace_id, pdf_url, job_id, db_clients, attempt + 1
            )
        else:
            logger.error(f"❌ Failed to process {file_name} after {MAX_RETRY_ATTEMPTS} attempts")
            return {
                "status": "failed",
                "pdf_url": pdf_url,
                "file_name": file_name,
                "error": error_msg,
                "attempts": attempt,
                "traceback": traceback.format_exc()
            }


def process_files_batch(
    workspace_id: str,
    file_paths: List[str],
    job_id: str,
    db_clients: DatabaseClients
) -> Dict[str, Any]:
    """
    Process multiple files with concurrent execution

    Args:
        workspace_id: Workspace identifier
        file_paths: List of PDF URLs to process
        job_id: Job identifier
        db_clients: Database clients instance

    Returns:
        Batch processing results
    """
    start_time = datetime.now()

    logger.info(f"\n{'='*80}")
    logger.info(f"🚀 BATCH PROCESSING STARTED")
    logger.info(f"📦 Job ID: {job_id}")
    logger.info(f"🔖 Workspace: {workspace_id}")
    logger.info(f"📄 Files: {len(file_paths)}")
    logger.info(f"{'='*80}\n")

    results = []
    successful = 0
    failed = 0

    # Process files concurrently (with limit)
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_FILES) as executor:
        # Submit all files for processing
        future_to_url = {
            executor.submit(
                process_single_file_with_retry,
                workspace_id, pdf_url, job_id, db_clients
            ): pdf_url
            for pdf_url in file_paths
        }

        # Collect results as they complete
        for future in as_completed(future_to_url):
            pdf_url = future_to_url[future]

            try:
                result = future.result()
                results.append(result)

                if result.get('status') == 'completed':
                    successful += 1
                else:
                    failed += 1

            except Exception as e:
                logger.error(f"❌ Unexpected error processing {pdf_url}: {e}")
                failed += 1
                results.append({
                    "status": "failed",
                    "pdf_url": pdf_url,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })

    # Calculate final statistics
    processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

    logger.info(f"\n{'='*80}")
    logger.info(f"✅ BATCH PROCESSING COMPLETED")
    logger.info(f"⏱️  Total time: {processing_time}ms ({processing_time/1000:.1f}s)")
    logger.info(f"📊 Results:")
    logger.info(f"   ├─ Successful: {successful}/{len(file_paths)}")
    logger.info(f"   └─ Failed: {failed}/{len(file_paths)}")
    logger.info(f"{'='*80}\n")

    return {
        "status": "completed" if failed == 0 else "partial",
        "jobId": job_id,
        "workspaceId": workspace_id,
        "totalFiles": len(file_paths),
        "successful": successful,
        "failed": failed,
        "processingTimeMs": processing_time,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }


# ================================
# MESSAGE HANDLER
# ================================

def handle_job_message(message: Dict[str, Any], db_clients: DatabaseClients):
    """
    Handle incoming job message from RabbitMQ

    Args:
        message: Job message from queue
        db_clients: Database clients instance
    """
    try:
        logger.info(f"\n📥 Received job message")
        logger.debug(f"Message: {json.dumps(message, indent=2)}")

        # Extract and validate message fields
        workspace_id = message.get("workspaceId") or message.get("WorkspaceId")
        file_paths = message.get("filePaths") or message.get("FilePaths", [])
        job_id = message.get("jobId") or message.get("JobId")

        # Validation
        if not workspace_id:
            raise ValueError("Missing workspaceId in message")

        if not file_paths or len(file_paths) == 0:
            raise ValueError("Missing or empty filePaths in message")

        if not job_id:
            logger.warning("No jobId provided, generating one")
            import uuid
            job_id = f"job_{uuid.uuid4().hex[:8]}"

        logger.info(f"✓ Valid message: {len(file_paths)} files to process")

        # Process ALL files in batch
        batch_result = process_files_batch(
            workspace_id=workspace_id,
            file_paths=file_paths,
            job_id=job_id,
            db_clients=db_clients
        )

        # Push result to Firebase
        logger.info(f"🔥 Pushing batch result to Firebase...")
        try:
            db_clients.firebase_client.push_job_result(job_id, batch_result)
            logger.info(f"✅ Result pushed to Firebase for job {job_id}")
        except Exception as fb_error:
            logger.error(f"⚠️  Failed to push to Firebase: {fb_error}")
            # Don't fail the entire job if Firebase push fails

        return batch_result

    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Error handling job: {error_msg}")
        logger.error(traceback.format_exc())

        # Try to push error to Firebase
        try:
            job_id = message.get("jobId") or message.get("JobId") or "unknown"
            error_result = {
                "status": "failed",
                "jobId": job_id,
                "error": error_msg,
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now().isoformat()
            }

            db_clients.firebase_client.push_job_result(job_id, error_result)
            logger.info(f"✓ Error pushed to Firebase")
        except:
            logger.error("Failed to push error to Firebase")


# ================================
# HEALTH CHECK
# ================================

def health_check(db_clients: DatabaseClients) -> Dict[str, Any]:
    """
    Check health of all database connections

    Returns:
        Health status dictionary
    """
    health = {
        "timestamp": datetime.now().isoformat(),
        "neo4j": "unknown",
        "qdrant": "unknown",
        "firebase": "unknown",
        "overall": "unknown"
    }

    # Check Neo4j
    try:
        with db_clients.neo4j_driver.session() as session:
            session.run("RETURN 1")
        health["neo4j"] = "healthy"
    except Exception as e:
        health["neo4j"] = f"unhealthy: {str(e)}"

    # Check Qdrant
    try:
        db_clients.qdrant_client.get_collections()
        health["qdrant"] = "healthy"
    except Exception as e:
        health["qdrant"] = f"unhealthy: {str(e)}"

    # Check Firebase (simple check)
    try:
        if db_clients.firebase_client:
            health["firebase"] = "healthy"
    except Exception as e:
        health["firebase"] = f"unhealthy: {str(e)}"

    # Overall status
    if all(status == "healthy" for status in [health["neo4j"], health["qdrant"], health["firebase"]]):
        health["overall"] = "healthy"
    else:
        health["overall"] = "degraded"

    return health


# ================================
# MAIN WORKER LOOP
# ================================

def main():
    """Main worker loop with graceful shutdown"""
    logger.info("\n" + "="*80)
    logger.info("🤖 PDF PROCESSING WORKER - ENHANCED VERSION")
    logger.info("="*80)

    db_clients = None
    rabbitmq_client = None

    try:
        # Initialize database clients
        db_clients = DatabaseClients()

        # Health check on startup
        health = health_check(db_clients)
        logger.info(f"🏥 Health check: {health['overall']}")
        if health['overall'] != "healthy":
            logger.warning(f"⚠️  System health degraded: {health}")

        # Connect to RabbitMQ
        rabbitmq_client = RabbitMQClient(RABBITMQ_CONFIG)
        rabbitmq_client.connect()
        rabbitmq_client.declare_queue(QUEUE_NAME)

        logger.info(f"\n✅ Worker ready and listening to queue: {QUEUE_NAME}")
        logger.info(f"⚙️  Configuration:")
        logger.info(f"   ├─ Max concurrent files: {MAX_CONCURRENT_FILES}")
        logger.info(f"   ├─ Max retry attempts: {MAX_RETRY_ATTEMPTS}")
        logger.info(f"   └─ Retry delay: {RETRY_DELAY}s")
        logger.info("="*80 + "\n")

        # Start consuming messages
        def message_callback(msg):
            if shutdown_requested:
                logger.info("⚠️  Shutdown requested, skipping new messages")
                return False  # Stop consuming

            handle_job_message(msg, db_clients)
            return True  # Continue consuming

        rabbitmq_client.consume_messages(QUEUE_NAME, message_callback)

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Worker interrupted by user")
    except Exception as e:
        logger.error(f"\n\n❌ Worker error: {e}")
        logger.error(traceback.format_exc())
    finally:
        logger.info("\n🔌 Shutting down gracefully...")

        # Close RabbitMQ connection
        if rabbitmq_client:
            try:
                rabbitmq_client.close()
                logger.info("✓ RabbitMQ connection closed")
            except Exception as e:
                logger.error(f"Error closing RabbitMQ: {e}")

        # Close database connections
        if db_clients:
            try:
                db_clients.close()
            except Exception as e:
                logger.error(f"Error closing database clients: {e}")

        logger.info("✅ Worker shut down gracefully")
        logger.info("="*80 + "\n")


# ================================
# ENTRY POINT
# ================================

if __name__ == "__main__":
    main()
