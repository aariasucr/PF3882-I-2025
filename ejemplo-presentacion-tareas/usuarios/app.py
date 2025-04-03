from marshmallow import Schema, fields, ValidationError
from flask import Flask, jsonify, request
from flasgger import Swagger
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        # logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

swagger_template = {
    "info": {
        "title": "API de Usuarios",
        "version": "1.0",
        "description": "Para manejar usuarios.",
        "termsOfService": "https://www.lospatitos.com/tos/",
        "contact": {
            "responsibleOrganization": "Los Patitos",
            "responsibleDeveloper": "Patito",
            "email": "patito@lospatitos.com",
            "url": "https://www.lospatitos.com",
        },
    }
}
swagger = Swagger(app, template=swagger_template)


class UsuarioSchema(Schema):
    nombre = fields.String(required=True)
    apellidos = fields.String(required=True)
    email = fields.String(required=True)


usuario_schema = UsuarioSchema()

usuarios = [
    {"id": 1, "nombre": "Elena", "apellidos": "Nito Blanco", "email": "elena@mail.com"},
    {"id": 2, "nombre": "Elsa", "apellidos": "Patito Blanco", "email": "elsa@mail.com"},
    {"id": 3, "nombre": "Armando", "apellidos": "Paredes Rojas",
        "email": "armando@mail.com"},
    {"id": 4, "nombre": "Marco", "apellidos": "Safea", "email": "marco@mail.com"},
    {"id": 5, "nombre": "Aquiles", "apellidos": "Bailo", "email": "aquiles@mail.com"}
]


@app.route('/usuarios', methods=['GET'])
def get_usuarios():
    """
    Obtener todos los usuarios
    ---
    responses:
      200:
        description: lista de usuarios
    """
    app.logger.info(
        "Retornando lista de usuarios con tamaño: %d", len(usuarios))
    return jsonify(usuarios), 200


@app.route('/usuarios/<int:usuario_id>', methods=['GET'])
def get_usuario(usuario_id):
    """
    Obtener usuario por ID
    ---
    parameters:
      - name: usuario_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Usuario encontrado
        schema:
          id: Usuario
          properties:
            id:
              type: integer
            nombre:
              type: string
            apellidos:
              type: string
            email:
              type: string
      404:
        description: Usuario no encontrado
        schema:
          id: Error
          properties:
            error:
              type: string
    """
    usuario = find_usuario(usuario_id)
    if usuario:
        app.logger.info("Usuario con id %d encontrado", usuario_id)
        return jsonify(usuario), 200
    app.logger.info("Usuario con id %d NO encontrado", usuario_id)
    return jsonify({"error": "Usuario no encontrado"}), 404


@app.route('/usuarios', methods=['POST'])
def add_usuario():
    """
    Agregar usuario
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nombre:
              type: string
            apellidos:
              type: string
            email:
              type: string
    responses:
      201:
        description: Book added
      400:
        description: Datos incorrectos
    """

    # data = request.get_json()

    try:
        data = usuario_schema.load(request.get_json())
    except ValidationError as err:
        app.logger.info("Datos de usuario invalidos: %s", err.messages)
        return jsonify(err.messages), 400

    app.logger.info("Agregando nuevo usuario: %s", data)
    new_usuario = {
        "id": len(usuarios) + 1,
        "nombre": data["nombre"],
        "apellidos": data["apellidos"],
        "email": data["email"]
    }
    usuarios.append(new_usuario)
    return jsonify(new_usuario), 201


@app.route('/usuarios/<int:usuario_id>', methods=['PUT'])
def update_usuario(usuario_id):
    """
    Actualizar Usuario
    ---
    parameters:
      - name: usuario_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          id: Usuario
          type: object
          properties:
            nombre:
              type: string
            apellidos:
              type: string
            email:
              type: string
    responses:
      200:
        description: Book updated
      404:
        description: Book not found
    """
    usuario = find_usuario(usuario_id)
    if not usuario:
        app.logger.info("Usuario con ID %d no encotrado", usuario_id)
        return jsonify({"error": "Usuario no encontrado"}), 404

    try:
        data = usuario_schema.load(request.get_json())
    except ValidationError as err:
        app.logger.info("Datos de usuario invalidos: %s", err.messages)
        return jsonify(err.messages), 400

    app.logger.info("Actualizando usuario %d con datos: %s", usuario_id, data)
    usuario["nombre"] = data["nombre"]
    usuario["apellidos"] = data["apellidos"]
    usuario["email"] = data["email"]
    return jsonify(usuario), 200


@app.route('/usuarios/<int:usuario_id>', methods=['DELETE'])
def delete_usuario(usuario_id):
    """
    Borrar un usuario
    ---
    parameters:
      - name: usuario_id
        in: path
        type: integer
        required: true
    responses:
      204:
        description: Usuario borrado
      404:
        description: Usuario no encontrado
    """
    app.logger.info("Borrando usuario con ID %d", usuario_id)
    # si no usamos global, python asume que usuarios es variable local
    global usuarios
    # creamos una nueva lista sin el usuario que queremos eliminar
    usuarios = [b for b in usuarios if b["id"] != usuario_id]
    return "", 204


def find_usuario(usuario_id):
    # usando for
    for usuario in usuarios:
        if usuario["id"] == usuario_id:
            return usuario
    return None


if __name__ == '__main__':
    app.run(debug=True, port=5003)
