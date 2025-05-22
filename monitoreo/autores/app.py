from flask import Flask, jsonify, request, g

from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger
from models import db, Autor
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from log_utils import init_logging, CORRELATION_ID_HEADER
import uuid

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
    'title': 'API de Autores',
    'uiversion': 3
}

swagger = Swagger(app)
db.init_app(app)

init_logging()


@app.before_request
def set_correlation_id():
    g.correlation_id = request.headers.get(
        CORRELATION_ID_HEADER, str(uuid.uuid4()))


@app.after_request
def add_correlation_id_to_response(response):
    response.headers[CORRELATION_ID_HEADER] = g.correlation_id
    return response


@app.route('/autores', methods=['GET'])
def get_autores():
    """
    Obtener todos los autores
    ---
    tags:
      - Autores
    responses:
      200:
        description: Lista de autores
        schema:
          type: array
          items:
            properties:
              id:
                type: integer
              nombre:
                type: string
              email:
                type: string
    """
    app.logger.info("Obteniendo lista de autores")
    autores = Autor.query.all()
    return jsonify([autor.to_dict() for autor in autores])


@app.route('/autores/<int:autor_id>', methods=['GET'])
def get_autor_by_id(autor_id):
    """
    Obtener un autor por su ID
    ---
    tags:
      - Autores
    parameters:
      - name: autor_id
        in: path
        type: integer
        required: true
        description: ID del autor
    responses:
      200:
        description: Autor encontrado
        schema:
          properties:
            id:
              type: integer
            nombre:
              type: string
            email:
              type: string
      404:
        description: Autor no encontrado
    """
    app.logger.info(f"Buscando autor con ID: {autor_id}")
    autor = Autor.query.get(autor_id)
    if autor is None:
        return jsonify({'error': 'Autor no encontrado'}), 404
    return jsonify(autor.to_dict())


@app.route('/autores', methods=['POST'])
def create_autor():
    """
    Crear un nuevo autor
    ---
    tags:
      - Autores
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            nombre:
              type: string
            email:
              type: string
    responses:
      201:
        description: Autor creado
        schema:
          properties:
            id:
              type: integer
            nombre:
              type: string
            email:
              type: string
      400:
        description: Datos incorrectos o email ya existe
    """
    app.logger.info("Creando nuevo autor")
    data = request.get_json()
    nombre = data.get('nombre')
    email = data.get('email')
    if not nombre or not email:
        return jsonify({'error': 'Nombre, email requeridos'}), 400
    if Autor.query.filter_by(email=email).first():
        return jsonify({'error': 'Email ya existe'}), 400
    autor = Autor(nombre=nombre, email=email)
    db.session.add(autor)
    db.session.commit()
    return jsonify(autor.to_dict()), 201


@app.route('/autores/<int:autor_id>', methods=['PUT'])
def update_autor(autor_id):
    """
    Actualizar Autor
    ---
    tags:
      - Autores
    parameters:
      - name: autor_id
        in: path
        type: integer
        required: true
        description: ID del autor
      - name: body
        in: body
        required: true
        schema:
          properties:
            nombre:
              type: string
            email:
              type: string
    responses:
      200:
        description: Autor actualizado
        schema:
          properties:
            id:
              type: integer
            nombre:
              type: string
            email:
              type: string
      400:
        description: Datos incorrectos o email ya existe
      404:
        description: Autor no encontrado
    """
    app.logger.info(f"Actualizando autor con ID: {autor_id}")
    autor = Autor.query.get(autor_id)
    if autor is None:
        return jsonify({'error': 'Autor no encontrado'}), 404
    data = request.get_json()
    nombre = data.get('nombre')
    email = data.get('email')
    if not nombre or not email:
        return jsonify({'error': 'Nombre, email requeridos'}), 400
    if autor.email != email and Autor.query.filter_by(email=email).first():
        return jsonify({'error': 'Email ya existe'}), 400
    autor.nombre = nombre
    autor.email = email
    db.session.commit()
    return jsonify(autor.to_dict()), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)
