"""
Test script to publish a test message to the RabbitMQ queue
Usage: python test_publisher.py
"""
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.rabbitmq_client import RabbitMQClient

# Configuration
RABBITMQ_CONFIG = {
    "Host": os.getenv("RABBITMQ_HOST", "chameleon-01.lmq.cloudamqp.com"),
    "Username": os.getenv("RABBITMQ_USERNAME", "odgfvgev"),
    "Password": os.getenv("RABBITMQ_PASSWORD", "ElA8Lhgv15r8Y0IR6n0S5bMLxGRmUmgg"),
    "VirtualHost": os.getenv("RABBITMQ_VHOST", "odgfvgev")
}

QUEUE_NAME = "pdf_jobs_queue"

def main():
    """Publish a test message to the queue"""
    
    # Sample test message
    test_message = {
        "jobId": f"test-job-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "workspaceId": "test-workspace-4", 
        "filePaths": [
            "https://sg.object.ncloudstorage.com/navnexus/SAGSINs.pdf"
        ]
    }
    
    print("\n" + "="*60)
    print("📤 Publishing test message to RabbitMQ")
    print("="*60)
    print(f"Queue: {QUEUE_NAME}")
    print(f"Message: {test_message}")
    print("="*60 + "\n")
    
    try:
        # Connect to RabbitMQ
        client = RabbitMQClient(RABBITMQ_CONFIG)
        client.connect()
        client.declare_queue(QUEUE_NAME)
        
        # Publish message
        client.publish_message(QUEUE_NAME, test_message)
        
        print("\n✅ Test message published successfully!")
        print("\nYou should see a worker pick up and process this message.")
        print("Check worker logs for processing details.\n")
        
        # Close connection
        client.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
