from flask import Flask, jsonify, request
from flasgger import Swagger
# from faker import Faker

app = Flask(__name__)
# app.config['SWAGGER'] = {
#     'title': 'Books API',
#     'version': '1.0',
#     'description': 'Un API para manejar libros.',
#     'termsOfService': 'https://www.ucr.ac.cr/acerca-u/',
# }
# swagger = Swagger(app)
swagger_template = {
    "info": {
        "title": "Books API",
        "version": "1.0",
        "description": "Un API para manejar libros.",
        "termsOfService": "https://www.lospatitos.com/tos/",
        "version": "2.0",
        "contact": {
            "responsibleOrganization": "Los Patitos",
            "responsibleDeveloper": "Patito",
            "email": "patito@lospatitos.com",
            "url": "https://www.lospatitos.com",
        },
    }
}
swagger = Swagger(app, template=swagger_template)

books = [
    {"id": 1, "title": "1984", "author": "George Orwell"},
    {"id": 2, "title": "La casa de los espíritus", "author": "Isabel Allende"},
    {"id": 3, "title": "Concherías", "author": "Aquileo Echeverría"},
    {"id": 4, "title": "The Catcher in the Rye", "author": "J.D. Salinger"},
    {"id": 5, "title": "Cuentos de angustias y paisajes", "author": "Carlos Salazar"},
    {"id": 6, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
    {"id": 7, "title": "Cien años de soledad", "author": "Gabriel García Márquez"}
]

# fake = Faker()
# books = []
# for i in range(10):
#     book = {
#         "id": i + 1,
#         "title": fake.sentence(),
#         "author": fake.name(),
#     }
#     books.append(book)


@app.route('/books', methods=['GET'])
def get_books():
    """
    Get all books
    ---
    responses:
      200:
        description: A list of books
    """
    return jsonify(books), 200


@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """
    Get a book by ID
    ---
    parameters:
      - name: book_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Book found
      404:
        description: Book not found
    """
    book = find_book(book_id)
    if book:
        return jsonify(book), 200
    return jsonify({"error": "Libro no encontrado"}), 404


@app.route('/books', methods=['POST'])
def add_book():
    """
    Add a new book
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
            author:
              type: string
    responses:
      201:
        description: Book added
    """
    data = request.get_json()
    new_book = {
        "id": len(books) + 1,
        "title": data["title"],
        "author": data["author"],
    }
    books.append(new_book)
    return jsonify(new_book), 201


@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    """
    Update a book
    ---
    parameters:
      - name: book_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
            author:
              type: string
    responses:
      200:
        description: Book updated
      404:
        description: Book not found
    """
    book = find_book(book_id)
    if not book:
        return jsonify({"error": "Libro no encontrado"}), 404

    data = request.get_json()
    book["title"] = data["title"]
    book["author"] = data["author"]
    return jsonify(book), 200


@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    """
    Delete a book
    ---
    parameters:
      - name: book_id
        in: path
        type: integer
        required: true
    responses:
      204:
        description: Book deleted
      404:
        description: Book not found
    """
    # si no usamos global, python asume que books es variable local
    global books
    # creamos una nueva lista sin el libro que queremos eliminar
    books = [b for b in books if b["id"] != book_id]
    return "", 204


def find_book(book_id):
    # usando for
    for book in books:
        if book["id"] == book_id:
            return book
    return None
    # usando next()
    # return next((b for b in books if b["id"] == book_id), None)


if __name__ == '__main__':
    app.run(debug=True)
