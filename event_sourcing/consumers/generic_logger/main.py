
import pika
import json


def callback(ch, method, properties, body):
    event = json.loads(body)
    print(f"[Logger] Received event: {event['type']} at {event['created_at']}")


# connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
# channel.queue_declare(queue='events')
# channel.basic_consume(
#     queue='events', on_message_callback=callback, auto_ack=True)
# print("Generic Logger started")
# channel.start_consuming()

queue_name = 'logging_queue'  # or 'cart_summary_queue', etc.
channel.queue_declare(queue=queue_name)
channel.queue_bind(exchange='events', queue=queue_name)

channel.basic_consume(
    queue=queue_name, on_message_callback=callback, auto_ack=True)
print("Generic Logger started")
channel.start_consuming()
