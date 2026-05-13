import pika

connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()

channel.queue_declare(queue="ternary_logs", durable=True)


def addScantoResult(payload):

    channel.basic_publish(
        exchange="",
        routing_key="ternary_logs",
        body=payload,
    )
