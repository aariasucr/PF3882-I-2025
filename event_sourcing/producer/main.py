
from flask import Flask, request, jsonify
import pika
import json
import psycopg2
from datetime import datetime

app = Flask(__name__)

conn = psycopg2.connect(
    "dbname=events user=postgres password=postgres host=localhost")
cur = conn.cursor()


def publish_event(event_type, payload):
    payload_json = json.dumps(payload)
    cur.execute("INSERT INTO events (type, payload) VALUES (%s, %s)",
                (event_type, payload_json))
    conn.commit()

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange='events', exchange_type='fanout')
    channel.basic_publish(exchange='events', routing_key='', body=json.dumps({
        "type": event_type,
        "payload": payload,
        "created_at": str(datetime.utcnow())
    }))
    connection.close()


@app.route('/cart', methods=['POST'])
def create_cart():
    data = request.get_json()
    publish_event("CartCreated", {"cart_id": str(data["cart_id"])})
    return jsonify({"status": "Cart created"}), 201


@app.route('/cart/<cart_id>/item', methods=['POST'])
def add_item(cart_id):
    data = request.get_json()
    publish_event("ItemAdded", {
        "cart_id": cart_id,
        "item_id": data["item_id"],
        "quantity": data["quantity"]
    })
    return jsonify({"status": "Item added"}), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0')
