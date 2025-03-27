from flask import Flask
from services.books import books_bp
from services.authors import authors_bp
# from services import books_bp, authors_bp

from flasgger import Swagger

app = Flask(__name__)

swagger_template = {
    "info": {
        "title": "Library API",
        "version": "1.0",
        "description": "Un API para manejar libros y autores.",
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

app.register_blueprint(books_bp)
app.register_blueprint(authors_bp)


if __name__ == "__main__":
    app.run(debug=True)
