import pika

connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()

channel.queue_declare(queue="scan_results", durable=True)


def addScantoResult(payload):

    channel.basic_publish(
        exchange="",
        routing_key="scan_results",
        body=payload,
    )


