# routes.py
import configcatclient
from flasgger import swag_from
from flask import Blueprint, jsonify, request

from biz_logic import (
    create_task,
    create_task_list,
    get_all_task_lists,
    get_tasks,
    update_task,
)
from schemas import TaskListSchema, TaskSchema

# Cliente para Feature Flags de ConfigCat
configcat_client = configcatclient.get(
    # <-- This is the actual SDK Key for your Test Environment environment.
    "configcat-sdk-1/Qa3dCJKDvEuFMc04-qIUiQ/CBBdcEoSiEuvlUN2W7s1SA"
)

task_blueprint = Blueprint("tasks", __name__)
task_list_schema = TaskListSchema()
task_schema = TaskSchema()
task_list_schema_many = TaskListSchema(many=True)
task_schema_many = TaskSchema(many=True)

# --- Task Lists ---


@task_blueprint.route("/lists", methods=["GET"])
@swag_from(
    {
        "tags": ["Task Lists"],
        "summary": "Obtener todas las listas de tareas",
        "responses": {
            200: {
                "description": "Lista de listas de tareas",
                "schema": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/TaskList"},
                },
            }
        },
    }
)
def list_task_lists():
    # Obtener el valor de la feature flag desde ConfigCat
    isMyFirstFeatureEnabled = configcat_client.get_value(
        "isMyFirstFeatureEnabled", False
    )

    # print('isMyFirstFeatureEnabled\'s value from ConfigCat: ' +
    #       str(isMyFirstFeatureEnabled))

    # Si la feature flag está habilitada, retornamos las listas de tareas
    # de lo contrario, retornamos un mensaje 404
    if isMyFirstFeatureEnabled:
        return jsonify(task_list_schema_many.dump(get_all_task_lists()))
    else:
        return jsonify({"message": "Nada por aca..."}), 404


@task_blueprint.route("/lists", methods=["POST"])
@swag_from(
    {
        "tags": ["Task Lists"],
        "summary": "Crear una nueva lista de tareas",
        "parameters": [
            {
                "name": "body",
                "in": "body",
                "required": True,
                "schema": {"$ref": "#/definitions/TaskList"},
            }
        ],
        "responses": {
            201: {
                "description": "Lista creada exitosamente",
                "schema": {"$ref": "#/definitions/TaskList"},
            },
            400: {"description": "Error de validación"},
        },
    }
)
def add_task_list():
    data = request.get_json()
    errors = task_list_schema.validate(data)
    print(data)
    if errors:
        return jsonify(errors), 400
    return jsonify(task_list_schema.dump(create_task_list(data["name"]))), 200


# --- Tasks (nested under lists) ---


@task_blueprint.route("/lists/<int:list_id>/tasks", methods=["GET"])
@swag_from(
    {
        "tags": ["Tasks"],
        "summary": "Obtener todas las tareas de una lista específica",
        "parameters": [
            {"name": "list_id", "in": "path", "type": "integer", "required": True}
        ],
        "responses": {
            200: {
                "description": "Tareas obtenidas exitosamente",
                "schema": {"type": "array", "items": {"$ref": "#/definitions/Task"}},
            }
        },
    }
)
def list_tasks(list_id):
    return jsonify(task_schema_many.dump(get_tasks(list_id)))


@task_blueprint.route("/lists/<int:list_id>/tasks", methods=["POST"])
@swag_from(
    {
        "tags": ["Tasks"],
        "summary": "Crear una nueva tarea en una lista",
        "parameters": [
            {"name": "list_id", "in": "path", "type": "integer", "required": True},
            {
                "name": "body",
                "in": "body",
                "required": True,
                "schema": {"$ref": "#/definitions/Task"},
            },
        ],
        "responses": {
            201: {
                "description": "Tarea creada exitosamente",
                "schema": {"$ref": "#/definitions/Task"},
            },
            400: {"description": "Error de validación"},
        },
    }
)
def add_task(list_id):
    data = request.get_json()
    data["task_list_id"] = list_id
    errors = task_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    return jsonify(task_schema.dump(create_task(data))), 201


@task_blueprint.route("/lists/<int:list_id>/tasks/<int:task_id>", methods=["PUT"])
@swag_from(
    {
        "tags": ["Tasks"],
        "summary": "Actualizar una tarea existente",
        "parameters": [
            {"name": "list_id", "in": "path", "type": "integer", "required": True},
            {"name": "task_id", "in": "path", "type": "integer", "required": True},
            {
                "name": "body",
                "in": "body",
                "required": True,
                "schema": {"$ref": "#/definitions/Task"},
            },
        ],
        "responses": {
            200: {
                "description": "Tarea actualizada",
                "schema": {"$ref": "#/definitions/Task"},
            },
            400: {"description": "Error de validación"},
        },
    }
)
def edit_task(list_id, task_id):
    data = request.get_json()
    data["task_list_id"] = list_id
    errors = task_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    return jsonify(task_schema.dump(update_task(task_id, data)))
