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
        "title": "API de Autores",
        "version": "1.0",
        "description": "Para manejar autores.",
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


autores = [
    {"id": 1, "nombre": "George Orwell"},
    {"id": 2, "nombre": "Isabel Allende"},
    {"id": 3, "nombre": "Aquileo Echeverría"},
    {"id": 4, "nombre": "J.D. Salinger"},
    {"id": 5, "nombre": "Carlos Salazar"},
    {"id": 6, "nombre": "F. Scott Fitzgerald"},
    {"id": 7, "nombre": "Gabriel García Márquez"}
]


@app.route('/autores', methods=['GET'])
def get_autores():
    """
    Obtener todos los autores
    ---
    responses:
      200:
        description: lista de autores
    """
    app.logger.info("Retornando lista de autores con tamaño: %d", len(autores))
    return jsonify(autores), 200


@app.route('/autores/<int:autor_id>', methods=['GET'])
def get_autor(autor_id):
    """
    Obtener autor por ID
    ---
    parameters:
      - name: autor_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Autor encontrado
        schema:
          id: Autor
          properties:
            id:
              type: integer
            nombre:
              type: string
      404:
        description: Autor no encontrado
        schema:
          id: Error
          properties:
            error:
              type: string
    """
    autor = find_autor(autor_id)
    if autor:
        app.logger.info("Autor con id %d encontrado", autor_id)
        return jsonify(autor), 200
    app.logger.info("Autor con id %d NO encontrado", autor_id)
    return jsonify({"error": "Autor no encontrado"}), 404


def find_autor(autor_id):
    # usando for
    for autor in autores:
        if autor["id"] == autor_id:
            return autor
    return None


if __name__ == '__main__':
    app.run(debug=True, port=5002)
