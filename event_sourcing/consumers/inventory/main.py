
import pika
import json


def callback(ch, method, properties, body):
    event = json.loads(body)
    if event["type"] == "ItemAdded":
        print(
            f"[Inventory] Decrease stock for item: {event['payload']['item_id']}")


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()


queue_name = 'inventory_queue'  # or 'cart_summary_queue', etc.
channel.queue_declare(queue=queue_name)
channel.queue_bind(exchange='events', queue=queue_name)

channel.basic_consume(
    queue=queue_name, on_message_callback=callback, auto_ack=True)
print("Inventory consumer started")
channel.start_consuming()
