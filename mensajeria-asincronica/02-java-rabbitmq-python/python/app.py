from flask import Flask, jsonify, request
from flasgger import Swagger
import pika
from dotenv import load_dotenv
import os
import logging

app = Flask(__name__)
swagger = Swagger(app)

load_dotenv("config.env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        # logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)


@app.route('/echo', methods=['GET'])
def echo():
    """
    Responde con un saludo
    ---
    responses:
      200:
        description: Un saludo
    """

    data = {}
    data['title'] = "Cien años de soledad"
    data['author'] = "Gabriel García Márquez"

    rabbitmq_host = os.getenv("RABBITMQ_HOST")

    # Conectarse a RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(rabbitmq_host))

    # Crear un canal
    channel = connection.channel()
    channel.queue_declare(queue='cola-de-libros')

    # Publicar un mensaje
    channel.basic_publish(exchange='', routing_key='cola-de-libros',
                          body=str(data))
    # Cerrar la conexión
    connection.close()

    return jsonify("Hola hola gavilán sin cola"), 200


def callback_rabbitmq(ch, method, properties, body):
    app.logger.info(f"Llego esto de rabbitmq: {body.decode()}")


rabbitmq_host = os.getenv("RABBITMQ_HOST")

connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
channel = connection.channel()
channel.queue_declare(queue='cola-de-libros')

channel.basic_consume(
    queue='cola-de-libros', on_message_callback=callback_rabbitmq, auto_ack=True)
app.logger.info("Esperando mensajes...")
channel.start_consuming()

# Iniciar la aplicación
if __name__ == '__main__':
    app.run(debug=True)
