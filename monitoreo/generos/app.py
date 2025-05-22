import os
from flask import Flask, request, jsonify, g
from flasgger import Swagger, swag_from
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from models import db, Genero
from log_utils import init_logging, CORRELATION_ID_HEADER
import uuid

# Logging basico sin Correlation ID
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
    'title': 'API de Generos',
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


@app.route('/generos/<int:genero_id>', methods=['GET'])
@swag_from({
    'responses': {
        200: {
            'description': 'Genero encontrado',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'nombre': {'type': 'string'},
                    'description': {'type': 'string'}
                }
            }
        },
        404: {'description': 'Genero not found'}
    }
})
def get_genero(genero_id):
    app.logger.info(f"Obteniendo genero con ID: {genero_id}")
    genero = db.session.get(Genero, genero_id)
    if genero:
        return jsonify(genero.to_dict()), 200
    return jsonify({'error': 'Genero not found'}), 404


@app.route('/generos', methods=['GET'])
@swag_from({
    'responses': {
        200: {
            'description': 'Lista de generos',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'nombre': {'type': 'string'},
                        'description': {'type': 'string'}
                    }
                }
            }
        }
    }
})
def get_generos():
    app.logger.info("Obteniendo lista de generos")
    generos = Genero.query.all()
    return jsonify([g.to_dict() for g in generos]), 200


@app.route('/generos', methods=['POST'])
@swag_from({
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'nombre': {'type': 'string'},
                    'description': {'type': 'string'}
                },
                'required': ['nombre']
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Genero creado',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'nombre': {'type': 'string'},
                    'description': {'type': 'string'}
                }
            }
        },
        400: {'description': 'Datos inválidos'}
    }
})
def create_genero():
    app.logger.info("Creando nuevo genero")
    data = request.get_json()
    if not data or 'nombre' not in data:
        return jsonify({'error': 'Invalid input'}), 400
    genero = Genero(nombre=data['nombre'], description=data.get('description'))
    db.session.add(genero)
    db.session.commit()
    return jsonify(genero.to_dict()), 201


@app.route('/generos/<int:genero_id>', methods=['PUT'])
@swag_from({
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'nombre': {'type': 'string'},
                    'description': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Genero actualizado',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'nombre': {'type': 'string'},
                    'description': {'type': 'string'}
                }
            }
        },
        404: {'description': 'Genero no encontrado'},
    }
})
def update_genero(genero_id):
    app.logger.info(f"Actualizando genero con ID: {genero_id}")
    genero = Genero.query.get(genero_id)
    if not genero:
        return jsonify({'error': 'Genero no encontrado'}), 404
    data = request.get_json()
    if 'nombre' in data:
        genero.nombre = data['nombre']
    if 'description' in data:
        genero.description = data['description']
    db.session.commit()
    return jsonify(genero.to_dict()), 200


if __name__ == '__main__':
    app.run(debug=True, port=5001)
