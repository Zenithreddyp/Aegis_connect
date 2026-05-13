import time
import os

import pika

from engine.orchestrator import analyze_logs

RETRY_DELAY_SECONDS = 5
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
QUEUE_NAME = "ternary_logs"


def start_consumer():
    connection = None

    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(RABBITMQ_HOST)
            )
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)

            def callback(ch, method, properties, body):
                analyze_logs(body)

            channel.basic_consume(
                queue=QUEUE_NAME, auto_ack=True, on_message_callback=callback
            )

            print(f"[RabbitMQ] Connected to {RABBITMQ_HOST}. Waiting for messages...")
            channel.start_consuming()

        except Exception as error:
            print(
                f"[RabbitMQ] Connection error: {error}. Reconnecting in {RETRY_DELAY_SECONDS}s..."
            )
            try:
                if connection and not connection.is_closed:
                    connection.close()
            except Exception:
                pass
            time.sleep(RETRY_DELAY_SECONDS)

        finally:
            connection = None
