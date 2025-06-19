from flasgger import Swagger
from flask import Flask

from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS
from models import db
from routes import task_blueprint
from schemas import ma

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = SQLALCHEMY_TRACK_MODIFICATIONS

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Task List API",
        "description": "API para gestionar listas de tareas y tareas",
        "version": "1.0.0",
    },
    "basePath": "/",
    "schemes": ["http"],
    "definitions": {
        "TaskList": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "readOnly": True},
                "name": {"type": "string"},
            },
            "required": ["name"],
        },
        "Task": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "readOnly": True},
                "title": {"type": "string"},
                "completed": {"type": "boolean"},
                "task_list_id": {"type": "integer"},
            },
            "required": ["title", "task_list_id"],
        },
    },
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,  # all endpoints
            "model_filter": lambda tag: True,  # all models
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    # "specs_route": "/swagger/"
}

Swagger(app, template=swagger_template, config=swagger_config)
db.init_app(app)
ma.init_app(app)

# Esto crea la base de datos si no existe
with app.app_context():
    db.create_all()

app.register_blueprint(task_blueprint, url_prefix="/api")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
