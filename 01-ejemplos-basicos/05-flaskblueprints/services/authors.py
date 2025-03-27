from flask import Blueprint, jsonify

authors_bp = Blueprint("authors", __name__, url_prefix="/authors")

authors = [
    {"id": 1, "name": "Ana Banana"},
    {"id": 2, "name": "Juan Vainas"}
]


@authors_bp.route("/", methods=["GET"])
def get_authors():
    """
    Get all authors
    ---
    tags:
      - authors
    responses:
      200:
        description: A list of authors
        schema:
          type: array
          items:
            id: Author
            properties:
              id:
                type: integer
              name:
                type: string
    """
    return jsonify(authors), 200
