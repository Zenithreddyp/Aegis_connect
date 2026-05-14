from concurrent.futures import ThreadPoolExecutor
import os
import time

import pika

from engine.orchestrator import analyze_logs

RETRY_DELAY_SECONDS = 5
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
QUEUE_NAME = "ternary_logs"

executor = ThreadPoolExecutor(max_workers=5)


def ack_message(channel, delivery_tag):
    if channel.is_open:
        channel.basic_ack(delivery_tag)


def nack_message(channel, delivery_tag):
    if channel.is_open:
        channel.basic_nack(delivery_tag, requeue=True)


def process_message(connection, channel, delivery_tag, body):
    """
    Runs inside worker thread.
    """

    try:
        analyze_logs(body)

        connection.add_callback_threadsafe(lambda: ack_message(channel, delivery_tag))

    except Exception as error:
        print(f"[Worker] Processing failed: {error}")

        connection.add_callback_threadsafe(lambda: nack_message(channel, delivery_tag))


def start_consumer():
    connection = None

    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)

            channel.basic_qos(prefetch_count=5)

            def callback(ch, method, properties, body):

                executor.submit(process_message, connection, ch, method.delivery_tag, body)

            channel.basic_consume(queue=QUEUE_NAME, auto_ack=False, on_message_callback=callback)

            print(f"[RabbitMQ] Connected to {RABBITMQ_HOST}. Waiting for messages...")
            channel.start_consuming()

        except Exception as error:
            print(f"[RabbitMQ] Connection error: {error}. Reconnecting in {RETRY_DELAY_SECONDS}s...")
            try:
                if connection and not connection.is_closed:
                    connection.close()
            except Exception:
                pass
            time.sleep(RETRY_DELAY_SECONDS)

        finally:
            connection = None
