from flask import Flask, jsonify, request

app = Flask(__name__)

books = [
    {"id": 1, "title": "1984", "author": "George Orwell"},
    {"id": 2, "title": "La casa de los espíritus", "author": "Isabel Allende"},
    {"id": 3, "title": "Concherías", "author": "Aquileo Echeverría"},
    {"id": 4, "title": "The Catcher in the Rye", "author": "J.D. Salinger"},
    {"id": 5, "title": "Cuentos de angustias y paisajes", "author": "Carlos Salazar"},
    {"id": 6, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
    {"id": 7, "title": "Cien años de soledad", "author": "Gabriel García Márquez"}
]


# @app.route('/patito/saludito', methods=['GET'])
# def get_mensaje_con_get():
#     return jsonify("Hola hola gavilan sin cola con GET")


# @app.route('/patito/saludito', methods=['POST'])
# def get_mensaje_con_post():
#     return jsonify("Hola hola gavilan sin cola con POST")

@app.route('/books', methods=['GET'])
def get_books():
    return jsonify(books)


@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = find_book(book_id)
    if book:
        return jsonify(book)
    return jsonify({"message": "Libro no encontrado"}), 404


@app.route('/books', methods=['POST'])
def add_book():
    book = request.get_json()
    # validacion manual
    if not book or 'title' not in book or 'author' not in book:
        return jsonify({"message": "Falta el título o el autor"}), 400
    book['id'] = len(books) + 1

    books.append(book)
    return jsonify({"message": "Libro agregado"}), 201


@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    # validamos el input
    data = request.get_json()
    if not data or 'title' not in data or 'author' not in data:
        return jsonify({"message": "Falta el título o el autor"}), 400

    # buscamos el libro
    book = find_book(book_id)
    if not book:
        return jsonify({"message": "Libro no encontrado"}), 404

    book["title"] = data['title']
    book["author"] = data['author']
    return jsonify({"message": "Libro actualizado"})


@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
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
