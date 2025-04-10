from flask import Flask, jsonify, request
from flasgger import Swagger
import pika
from dotenv import load_dotenv
import os

app = Flask(__name__)
swagger = Swagger(app)

load_dotenv("config.env")


@app.route('/rabbitmq', methods=['GET'])
def rabbitmq():
    """
    Mandar mensaje a RabbitMQ
    ---
    responses:
      200:
        description: Mensaje enviado
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

    return jsonify("Mensaje enviado a RabbitMQ"), 200


# Iniciar la aplicación
if __name__ == '__main__':
    app.run(debug=True)
