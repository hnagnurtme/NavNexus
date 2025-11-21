"""
TEST PUBLISHER for new_worker.py
=================================

This script publishes test messages to RabbitMQ to test the new_worker.py

Usage:
    python test_publisher.py
"""

import os
import sys
import json
import uuid
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.rabbitmq_client import RabbitMQClient

# RabbitMQ Configuration (same as new_worker.py)
RABBITMQ_CONFIG = {
    "Host": os.getenv("RABBITMQ_HOST", "chameleon-01.lmq.cloudamqp.com"),
    "Username": os.getenv("RABBITMQ_USERNAME", "odgfvgev"),
    "Password": os.getenv("RABBITMQ_PASSWORD", "ElA8Lhgv15r8Y0IR6n0S5bMLxGRmUmgg"),
    "VirtualHost": os.getenv("RABBITMQ_VHOST", "odgfvgev")
}

QUEUE_NAME = os.getenv("QUEUE_NAME", "pdf_jobs_queue")


def publish_test_message(workspace_id: str, file_paths: list, job_id: str = None):
    """
    Publish a test message to RabbitMQ queue

    Args:
        workspace_id: The workspace ID
        file_paths: List of PDF URLs or paths to process
        job_id: Optional job ID (will generate if not provided)
    """
    if not job_id:
        job_id = f"test_job_{uuid.uuid4().hex[:8]}"

    # Create test message matching new_worker.py expected format
    message = {
        "jobId": job_id,
        "workspaceId": workspace_id,
        "filePaths": file_paths,
        "timestamp": datetime.now().isoformat()
    }

    print("\n" + "="*80)
    print("📤 Publishing Test Message to RabbitMQ")
    print("="*80)
    print(f"Queue: {QUEUE_NAME}")
    print(f"Job ID: {job_id}")
    print(f"Workspace ID: {workspace_id}")
    print(f"Files: {len(file_paths)}")
    print("\nMessage Content:")
    print(json.dumps(message, indent=2))
    print("="*80 + "\n")

    try:
        # Connect to RabbitMQ
        print("🔌 Connecting to RabbitMQ...")
        rabbitmq_client = RabbitMQClient(RABBITMQ_CONFIG)
        rabbitmq_client.connect()

        # Declare queue (ensure it exists)
        rabbitmq_client.declare_queue(QUEUE_NAME)
        print(f"✓ Connected to queue: {QUEUE_NAME}")

        # Publish message
        rabbitmq_client.publish_message(QUEUE_NAME, message)
        print("✅ Message published successfully!")
        print(f"\n👉 Check new_worker.py logs for processing status")
        print(f"👉 Check Firebase Realtime Database at: jobs/{job_id}")

        # Close connection
        rabbitmq_client.close()
        print("\n✓ Connection closed")

    except Exception as e:
        print(f"\n❌ Error publishing message: {e}")
        import traceback
        traceback.print_exc()


def publish_single_file_test():
    """Test with a single PDF file"""
    print("\n🧪 TEST 1: Single PDF File")
    publish_test_message(
        workspace_id="test_workspace_001",
        file_paths=[
            "https://sg.object.ncloudstorage.com/navnexus/KOREA.pdf"
        ],
        job_id="single_file_test"
    )


def publish_multiple_files_test():
    """Test with multiple PDF files"""
    print("\n🧪 TEST 2: Multiple PDF Files")
    publish_test_message(
        workspace_id="test_workspace_005",
        file_paths=[
            "https://sg.object.ncloudstorage.com/navnexus/KOREA.pdf",
            "https://arxiv.org/pdf/2301.12345.pdf",
        ],
        job_id="multiple_files_test"
    )


def publish_custom_message():
    """Publish a custom message with user input"""
    print("\n🧪 CUSTOM TEST: Enter your own values")
    print("="*80)

    workspace_id = input("Enter Workspace ID (default: test_workspace): ").strip() or "test_workspace"

    file_paths = []
    print("\nEnter PDF URLs (one per line, empty line to finish):")
    while True:
        url = input("PDF URL: ").strip()
        if not url:
            break
        file_paths.append(url)

    if not file_paths:
        print("❌ No PDF URLs provided, using default test URL")
        file_paths = ["https://sg.object.ncloudstorage.com/navnexus/SAGSINs.pdf"]

    job_id = input("\nEnter Job ID (leave empty for auto-generate): ").strip() or None

    publish_test_message(workspace_id, file_paths, job_id)


def publish_existing_workspace_test():
    """Test with workspace-4 (matching the old test)"""
    print("\n🧪 TEST 3: Existing Workspace (test-workspace-)")
    publish_test_message(
        workspace_id="test-workspace-",
        file_paths=[
            "https://sg.object.ncloudstorage.com/navnexus/SAGSINs.pdf"
        ],
        job_id=f"test-job-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )


def main():
    """Main menu"""
    print("\n" + "="*80)
    print("🧪 NEW_WORKER.PY TEST PUBLISHER")
    print("="*80)
    print("\nSelect a test scenario:")
    print("1. Single PDF file test (test_workspace_001)")
    print("2. Multiple PDF files test (test_workspace_002)")
    print("3. Existing workspace test (test-workspace-4)")
    print("4. Custom message")
    print("5. Exit")
    print("="*80)

    choice = input("\nEnter your choice (1-5): ").strip()

    if choice == "1":
        publish_single_file_test()
    elif choice == "2":
        publish_multiple_files_test()
    elif choice == "3":
        publish_existing_workspace_test()
    elif choice == "4":
        publish_custom_message()
    elif choice == "5":
        print("\n👋 Goodbye!")
        return
    else:
        print("\n❌ Invalid choice, please try again")
        main()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
