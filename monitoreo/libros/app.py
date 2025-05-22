from flasgger import Schema, fields
from flask import Flask, request, jsonify, g
from flasgger import Swagger
from models import db, Libro
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, AUTORES_URL, GENEROS_URL
import requests
from log_utils import init_logging, CORRELATION_ID_HEADER
import uuid

# Logging basico, sin Correlation ID
# import logging

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s",
#     handlers=[
#         # logging.FileHandler("app.log"),
#         logging.StreamHandler()
#     ]
# )

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SWAGGER'] = {
    'title': 'API de Libros',
    'uiversion': 3
}

Swagger(app)
db.init_app(app)

# Inicializamos el logger que incluye Correlation ID
init_logging()


# Antes de cada request, se genera un Correlation ID si no existe
@app.before_request
def set_correlation_id():
    g.correlation_id = request.headers.get(
        CORRELATION_ID_HEADER, str(uuid.uuid4()))


@app.after_request
def add_correlation_id_to_response(response):
    response.headers[CORRELATION_ID_HEADER] = g.correlation_id
    return response


@app.route('/libros', methods=['GET'])
def get_libros():
    """
    Obtener todos los libros
    ---
    responses:
      200:
        description: Lista de libros
        schema:
          type: array
          items:
            properties:
              id:
                type: integer
              titulo:
                type: string
              descripcion:
                type: string
              genero_id:
                type: integer
              genero:
                type: string
              autor_id:
                type: integer
              autor:
                type: string
    """
    app.logger.info("Obteniendo todos los libros")
    libros = Libro.query.all()
    return jsonify([libro.to_dict() for libro in libros])


@app.route('/libros/<int:libro_id>', methods=['GET'])
def get_libro(libro_id):
    """
    Obtener libro por ID
    ---
    parameters:
      - name: libro_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Libro encontrado
        schema:
          properties:
              id:
                type: integer
              titulo:
                type: string
              descripcion:
                type: string
              genero_id:
                type: integer
              genero:
                type: string
              autor_id:
                type: integer
              autor:
                type: string
      404:
        description: Libro no encontrado
    """
    app.logger.info(f"Obteniendo libro con ID: {libro_id}")
    libro = Libro.query.get(libro_id)
    if libro:
        return jsonify(libro.to_dict())
    return jsonify({'error': 'Libro no encontrado'}), 404


@app.route('/libros', methods=['POST'])
def create_libro():
    """
    Crear un nuevo libro
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
              titulo:
                type: string
              descripcion:
                type: string
              genero_id:
                type: integer
              autor_id:
                type: integer
    responses:
      201:
        description: Libro creado
        schema:
          properties:
              id:
                type: integer
              titulo:
                type: string
              descripcion:
                type: string
              genero_id:
                type: integer
              genero:
                type: string
              autor_id:
                type: integer
              autor:
                type: string
      400:
        description: Datos incorrectos
    """
    # logging.info("Creando un nuevo libro")
    data = request.get_json()
    try:
        app.logger.info(f"Datos recibidos: {data}")
        # app.logger.info(
        #     f"Llamando a {AUTORES_URL}/autores/{data['autor_id']}")
        # headers = {CORRELATION_ID_HEADER: g.correlation_id}
        # autor_resp = requests.get(
        #     f"{AUTORES_URL}/autores/{data['autor_id']}", headers=headers)
        autor_resp = get_api_externo(
            f"{AUTORES_URL}/autores/{data['autor_id']}")
        # autor_resp = requests.get(
        #     f"{AUTORES_URL}/autores/{data['autor_id']}")
        # app.logger.info(
        #     f"Llamando a {GENEROS_URL}/generos/{data['autor_id']}")
        # genero_resp = requests.get(
        #     f"{GENEROS_URL}/generos/{data['genero_id']}", headers=headers)
        # genero_resp = requests.get(
        #     f"{GENEROS_URL}/generos/{data['genero_id']}")
        genero_resp = get_api_externo(
            f"{GENEROS_URL}/generos/{data['genero_id']}")

        if autor_resp.status_code != 200 or genero_resp.status_code != 200:
            return jsonify({'error': 'Autor o género no encontrado'}), 400
        autor_data = autor_resp.json()
        genero_data = genero_resp.json()
        libro = Libro(
            titulo=data['titulo'],
            descripcion=data.get('descripcion'),
            genero_id=data['genero_id'],
            genero=genero_data.get('nombre', ''),
            autor_id=data['autor_id'],
            autor=autor_data.get('nombre', '')
        )
        db.session.add(libro)
        db.session.commit()
        return jsonify(libro.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/libros/<int:libro_id>', methods=['PUT'])
def update_libro(libro_id):
    """
    Actualizar un libro existente
    ---
    parameters:
      - name: libro_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          properties:
              titulo:
                type: string
              descripcion:
                type: string
              genero_id:
                type: integer
              autor_id:
                type: integer
    responses:
      200:
        description: Libro actualizado
        schema:
          properties:
              id:
                type: integer
              titulo:
                type: string
              descripcion:
                type: string
              genero_id:
                type: integer
              genero:
                type: string
              autor_id:
                type: integer
              autor:
                type: string
      404:
        description: Libro no encontrado
    """
    app.logger.info(f"Actualizando libro con ID: {libro_id}")
    libro = Libro.query.get(libro_id)
    if not libro:
        return jsonify({'error': 'Libro no encontrado'}), 404
    data = request.get_json()
    try:
        # If autor_id or genero_id are updated, fetch new data
        if 'autor_id' in data and data['autor_id'] != libro.autor_id:
            # headers = {CORRELATION_ID_HEADER: g.correlation_id}
            # autor_resp = requests.get(
            #     f"{AUTORES_URL}/autores/{data['autor_id']}", headers=headers)
            # autor_resp = requests.get(
            #     f"{AUTORES_URL}/autores/{data['autor_id']}")
            autor_resp = get_api_externo(
                f"{AUTORES_URL}/autores/{data['autor_id']}")
            if autor_resp.status_code != 200:
                return jsonify({'error': 'Autor no encontrado'}), 400
            autor_data = autor_resp.json()
            libro.autor_id = data['autor_id']
            libro.autor = autor_data.get('nombre', '')

        if 'genero_id' in data and data['genero_id'] != libro.genero_id:
            # genero_resp = requests.get(
            #     f"{GENEROS_URL}/generos/{data['genero_id']}", headers=headers)
            # genero_resp = requests.get(
            #     f"{GENEROS_URL}/generos/{data['genero_id']}")
            genero_resp = get_api_externo(
                f"{GENEROS_URL}/generos/{data['genero_id']}")

            if genero_resp.status_code != 200:
                return jsonify({'error': 'Género no encontrado'}), 400
            genero_data = genero_resp.json()
            libro.genero_id = data['genero_id']
            libro.genero = genero_data.get('nombre', '')
        libro.titulo = data.get('titulo', libro.titulo)
        libro.descripcion = data.get('descripcion', libro.descripcion)
        db.session.commit()
        return jsonify(libro.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 400


def get_api_externo(url):
    headers = {CORRELATION_ID_HEADER: g.correlation_id}
    app.logger.info(f"Llamando a {url}")
    respuesta = requests.get(f"{url}", headers=headers)
    return respuesta


if __name__ == '__main__':
    app.run(debug=True, port=5002)
