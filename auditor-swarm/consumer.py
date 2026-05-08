import pika
from agents.sentry import analyze_logs


connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
channel = connection.channel()
channel.queue_declare(queue="ternary_logs", durable=True)

def callback(ch, method, properties, body):
    analyze_logs(body)
    

channel.basic_consume(queue="ternary_logs", auto_ack=True, on_message_callback=callback)
channel.start_consuming()