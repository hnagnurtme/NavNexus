#!/usr/bin/env python3
"""
Test script for recursive expansion integration in worker.py

This tests the new process_pdf_with_recursive_expansion function.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('TestRecursiveWorker')

# Import worker components
from worker import (
    process_pdf_with_recursive_expansion,
    NEO4J_URL,
    NEO4J_USER,
    NEO4J_PASSWORD
)
from neo4j import GraphDatabase


async def test_recursive_expansion():
    """
    Test the recursive expansion pipeline with a sample PDF
    """
    logger.info("=" * 80)
    logger.info("🧪 TESTING RECURSIVE EXPANSION INTEGRATION")
    logger.info("=" * 80)

    # Test configuration
    workspace_id = f"test-workspace-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Use a small test PDF (you can replace with your own)
    test_pdfs = [
        "https://arxiv.org/pdf/2103.14030.pdf",  # Small ML paper
        # Add more test URLs here
    ]

    # Connect to Neo4j
    logger.info("🔌 Connecting to Neo4j...")
    neo4j_driver = GraphDatabase.driver(
        NEO4J_URL,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
        max_connection_lifetime=3600
    )
    logger.info("✓ Neo4j connected")

    results = []

    for pdf_url in test_pdfs:
        file_name = pdf_url.split('/')[-1]
        logger.info(f"\n{'='*80}")
        logger.info(f"📄 Testing with: {file_name}")
        logger.info(f"{'='*80}\n")

        try:
            result = await process_pdf_with_recursive_expansion(
                workspace_id=workspace_id,
                pdf_url=pdf_url,
                file_name=file_name,
                neo4j_driver=neo4j_driver,
                job_id=f"test-job-{datetime.now().strftime('%H%M%S')}"
            )

            results.append(result)

            # Print results
            logger.info("\n" + "=" * 80)
            logger.info("📊 PROCESSING RESULTS")
            logger.info("=" * 80)
            logger.info(f"Status: {result.get('status')}")
            logger.info(f"Processing Mode: {result.get('processing_mode')}")
            logger.info(f"Nodes Created: {result.get('nodes_created')}")
            logger.info(f"Evidence Created: {result.get('evidences_created')}")
            logger.info(f"Gap Suggestions: {result.get('gaps_created')}")
            logger.info(f"Language: {result.get('language')}")

            if 'quality_metrics' in result:
                metrics = result['quality_metrics']
                logger.info("\n📈 Quality Metrics:")
                logger.info(f"  - Total nodes: {metrics.get('total_nodes')}")
                logger.info(f"  - LLM calls: {metrics.get('llm_calls')}")
                logger.info(f"  - Max depth achieved: {metrics.get('max_depth_achieved')}")
                logger.info(f"  - Paragraphs processed: {metrics.get('paragraphs_processed')}")
                logger.info(f"  - Expansions stopped: {metrics.get('expansions_stopped')}")
                logger.info(f"  - Errors: {metrics.get('errors')}")

            if result.get('status') != 'success':
                logger.error(f"❌ Error: {result.get('error')}")
                if 'traceback' in result:
                    logger.error(f"Traceback:\n{result['traceback']}")

        except Exception as e:
            logger.error(f"❌ Test failed: {e}", exc_info=True)
            results.append({
                "status": "failed",
                "error": str(e),
                "file_name": file_name
            })

    # Cleanup (optional - comment out to keep test data)
    # logger.info("\n🧹 Cleaning up test data...")
    # with neo4j_driver.session() as session:
    #     session.run(
    #         "MATCH (n:KnowledgeNode {workspace_id: $workspace_id}) DETACH DELETE n",
    #         workspace_id=workspace_id
    #     )

    neo4j_driver.close()
    logger.info("\n✅ Test completed")

    return results


def main():
    """Run the test"""
    results = asyncio.run(test_recursive_expansion())

    # Summary
    print("\n" + "=" * 80)
    print("📋 TEST SUMMARY")
    print("=" * 80)

    successful = sum(1 for r in results if r.get('status') == 'success')
    failed = len(results) - successful

    print(f"Total tests: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print("=" * 80)


if __name__ == "__main__":
    main()
