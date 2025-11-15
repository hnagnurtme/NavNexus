from src.rabbitmq_client import RabbitMQClient

# Cấu hình RabbitMQ dạng dict (thay cho URL)
RABBITMQ_CONFIG = {
    "Host": "chameleon-01.lmq.cloudamqp.com",
    "Username": "odgfvgev",
    "Password": "ElA8Lhgv15r8Y0IR6n0S5bMLxGRmUmgg",
    "VirtualHost": "odgfvgev"
}

QUEUE_NAME = "pdf_jobs_queue"

def handle_job(message: dict):
    """Xử lý job từ queue"""
    print("Processing job:", message)
    # TODO: xử lý PDF, NLP, etc.

# Khởi tạo client
client = RabbitMQClient(RABBITMQ_CONFIG)
client.connect()
client.declare_queue(QUEUE_NAME)

# Publish ví dụ
client.publish_message(QUEUE_NAME, {"JobId": "1234", "Data": "Test payload"})

# Consume messages
client.consume_messages(QUEUE_NAME, handle_job)


