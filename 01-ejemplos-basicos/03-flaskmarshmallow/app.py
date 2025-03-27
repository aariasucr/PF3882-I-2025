from flask import Flask, jsonify, request
from faker import Faker
from flasgger import Swagger
from marshmallow import Schema, fields, ValidationError

app = Flask(__name__)

swagger_template = {
    "info": {
        "title": "Books API",
        "version": "1.0",
        "description": "Un API para manejar libros.",
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

# books = [
#     {"id": 1, "title": "1984", "author": "George Orwell"},
#     {"id": 2, "title": "La casa de los espíritus", "author": "Isabel Allende"},
#     {"id": 3, "title": "Concherías", "author": "Aquileo Echeverría"},
#     {"id": 4, "title": "The Catcher in the Rye", "author": "J.D. Salinger"},
#     {"id": 5, "title": "Cuentos de angustias y paisajes", "author": "Carlos Salazar"},
#     {"id": 6, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
#     {"id": 7, "title": "Cien años de soledad", "author": "Gabriel García Márquez"}
# ]

fake = Faker()
books = []
for i in range(1, 51):
    books.append({
        "id": i,
        "title": fake.catch_phrase(),
        "author": fake.name()
    })


# Definimos el esquema de validación
class BookSchema(Schema):
    title = fields.Str(required=True)
    author = fields.Str(required=True)


# Instanciamos el esquema para usarlo para validar mas adelante
book_schema = BookSchema()


# @app.route('/patito/saludito', methods=['GET'])
# def get_mensaje_con_get():
#     return jsonify("Hola hola gavilan sin cola con GET")


# @app.route('/patito/saludito', methods=['POST'])
# def get_mensaje_con_post():
#     return jsonify("Hola hola gavilan sin cola con POST")

@app.route('/books', methods=['GET'])
def get_books():
    """
    Obtiene todos los libros
    ---
    responses:
      200:
        description: Lista de libros
    """
    return jsonify(books)


@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """
    Obtiene un libro por su ID
    ---
    parameters:
      - name: book_id
        in: path
        type: integer
        required: true
        description: ID del libro
    responses:
      200:
        description: Un libro
      404:
        description: Libro no encontrado
    """
    book = find_book(book_id)
    if book:
        return jsonify(book)
    return jsonify({"message": "Libro no encontrado"}), 404


@app.route('/books', methods=['POST'])
def add_book():
    """
    Agrega un libro
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
              example: Rebelión en la granja
            author:
              type: string
              example: George Orwell
    responses:
      201:
        description: Libro agregado
      400:
        description: Faltan datos
    """
    # # validacion manual
    # book = request.get_json()
    # if not book or 'title' not in book or 'author' not in book:
    #     return jsonify({"message": "Falta el título o el autor"}), 400

    try:
        book = book_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify(err.messages), 400

    book['id'] = len(books) + 1

    books.append(book)
    return jsonify({"message": "Libro agregado"}), 201


@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    """
    Actualiza un libro
    ---
    parameters:
      - name: book_id
        in: path
        type: integer
        required: true
        description: ID del libro
      - name: body
        required: true
        in: body
        schema:
          type: object
          properties:
            title:
              type: string
              example: Rebelión en la granja
            author:
              type: string
              example: George Orwell
    responses:
      200:
        description: Libro actualizado
      400:
        description: Faltan datos
      404:
        description: Libro no encontrado

    """
    # validamos el input
    # data = request.get_json()
    # if not data or 'title' not in data or 'author' not in data:
    #     return jsonify({"message": "Falta el título o el autor"}), 400
    try:
        data = book_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify(err.messages), 400

    # buscamos el libro
    book = find_book(book_id)
    if not book:
        return jsonify({"message": "Libro no encontrado"}), 404

    book["title"] = data['title']
    book["author"] = data['author']
    return jsonify({"message": "Libro actualizado"})


@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    """
    Elimina un libro
    ---
    parameters:
      - name: book_id
        in: path
        type: integer
        required: true
        description: ID del libro
    responses:
      200:
        description: Libro eliminado
      404:
        description: Libro no encontrado
    """
    book = find_book(book_id)
    if not book:
        return jsonify({"message": "Libro no encontrado"}), 404

    books.remove(book)
    return jsonify({"message": "Libro eliminado"})


def find_book(book_id):
    # usando un for
    for book in books:
        if book['id'] == book_id:
            return book
    return None

    # usando una función lambda next()
    # return next((book for book in books if book['id'] == book_id), None)


# Iniciar la aplicación
if __name__ == '__main__':
    app.run(debug=True)
