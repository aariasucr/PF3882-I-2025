from flask import Flask, jsonify, request
from flasgger import Swagger
import logging
import requests

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
        "title": "API de Libros",
        "version": "1.0",
        "description": "Para manejar libros.",
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

libros = [
    {"id": 1, "titulo": "1984", "autor_id": 1},
    {"id": 2, "titulo": "La casa de los espíritus", "autor_id": 2},
    {"id": 3, "titulo": "Concherías", "autor_id": 3},
    {"id": 4, "titulo": "The Catcher in the Rye", "autor_id": 4},
    {"id": 5, "titulo": "Cuentos de angustias y paisajes", "autor_id": 5},
    {"id": 6, "titulo": "The Great Gatsby", "autor_id": 6},
    {"id": 7, "titulo": "Cien años de soledad", "autor_id": 7}
]

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
          id: Libro
          properties:
            id:
              type: integer
            titulo:
              type: string
            autor:
              type: string
      404:
        description: Libro no encontrado
        schema:
          id: Error
          properties:
            error:
              type: string
    """
    libro = find_book(libro_id)
    if libro:
        app.logger.info("Libro con id %d encontrado", libro_id)
        return jsonify(libro), 200
    app.logger.info("Libro con id %d NO encontrado", libro_id)
    return jsonify({"error": "Libro no encontrado"}), 404

def find_book(libro_id):
    # usando for
    for libro in libros:
        if libro["id"] == libro_id:
            autor = find_author_from_book(libro["autor_id"])
            new_libro = {
                "id": libro["id"],
                "titulo": libro["titulo"],
                "autor": autor["nombre"] if autor else "Desconocido",
            }
            return new_libro
    return None


def find_author_from_book(autor_id):
    autores_service = "http://localhost:5002"

    app.logger.info("Servicio de autores: %s", autores_service)

    response = requests.get(f"{autores_service}/autores/{autor_id}")
    if response.status_code == 200:
        return response.json()
    return None


if __name__ == '__main__':
    app.run(debug=True, port=5001)
