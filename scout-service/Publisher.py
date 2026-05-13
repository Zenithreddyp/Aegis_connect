import pika
import os

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
channel = connection.channel()

channel.queue_declare(queue="ternary_logs", durable=True)


def addScantoResult(payload):

    channel.basic_publish(
        exchange="",
        routing_key="ternary_logs",
        body=payload,
    )
