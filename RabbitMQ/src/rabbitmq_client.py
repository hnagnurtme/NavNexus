# src/rabbitmq_client.py
import pika
import json
import logging
from typing import Callable, Any, Optional, Union
import pika
from typing import Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class RabbitMQClient:
    def __init__(self, config: Union[str, dict]):
        """
        config: 
            - str: amqp://username:password@host/vhost
            - dict: {"Host":..., "Username":..., "Password":..., "VirtualHost":...}
        """
        self.config = config
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel = None  

    def connect(self):
        """Tạo kết nối và channel"""
        try:
            if isinstance(self.config, str):
                # dùng URL
                params = pika.URLParameters(self.config)
            elif isinstance(self.config, dict):
                # dùng dict cấu hình
                credentials = pika.PlainCredentials(
                    self.config["Username"], self.config["Password"]
                )
                params = pika.ConnectionParameters(
                    host=self.config["Host"],
                    virtual_host=self.config.get("VirtualHost", "/"),
                    credentials=credentials
                )
            else:
                raise ValueError("config phải là str hoặc dict")
            
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.exception(f"Failed to connect to RabbitMQ: {e}")
            raise

    def declare_queue(self, queue_name: str):
        """Declare queue durable"""
        if not self.channel:
            raise RuntimeError("Channel not initialized. Call connect() first.")
        self.channel.queue_declare(queue=queue_name, durable=True)
        logger.info(f"Queue declared: {queue_name}")

    def publish_message(self, queue_name: str, message: dict):
        """Publish message as JSON"""
        if not self.channel:
            raise RuntimeError("Channel not initialized. Call connect() first.")
        body = json.dumps(message)
        self.channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type='application/json',
            )
        )
        logger.info(f"Message published to {queue_name}: {message}")

    def consume_messages(self, queue_name: str, callback: Callable[[dict], Any]):
        """Lắng nghe queue và xử lý message"""
        if not self.channel:
            raise RuntimeError("Channel not initialized. Call connect() first.")

        def _callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                callback(message)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.exception(f"Failed to process message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=queue_name, on_message_callback=_callback)
        logger.info(f"Start consuming messages from {queue_name}")
        self.channel.start_consuming()

    def close(self):
        """Đóng channel và connection"""
        if self.channel:
            self.channel.close()
        if self.connection:
            self.connection.close()
        logger.info("RabbitMQ connection closed")
