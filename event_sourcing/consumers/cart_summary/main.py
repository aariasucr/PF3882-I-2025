
import pika
import json

summary = {}


def callback(ch, method, properties, body):
    event = json.loads(body)
    if event["type"] == "ItemAdded":
        cart = event['payload']['cart_id']
        summary.setdefault(cart, 0)
        summary[cart] += event['payload']['quantity']
        print(f"[CartSummary] {cart} has {summary[cart]} items")


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

queue_name = 'cart_summary_queue'  # or 'cart_summary_queue', etc.
channel.queue_declare(queue=queue_name)
channel.queue_bind(exchange='events', queue=queue_name)

channel.basic_consume(
    queue=queue_name, on_message_callback=callback, auto_ack=True)
print("Cart Summary consumer started")
channel.start_consuming()
