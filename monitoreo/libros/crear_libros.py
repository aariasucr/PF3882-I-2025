# seed_data.py
from faker import Faker
from models import db, Libro
from app import app
import random

fake = Faker()


def seed_data(libros_count=10):
    with app.app_context():
        db.drop_all()
        db.create_all()

        for _ in range(libros_count):
            titulo = fake.catch_phrase()
            descripcion = fake.paragraph(nb_sentences=3)
            genero_id = random.randint(1, 10)
            genero = fake.word()
            autor_id = random.randint(1, 10)
            autor = fake.name()
            libro = Libro(
                titulo=titulo,
                descripcion=descripcion,
                genero_id=genero_id,
                genero=genero,
                autor_id=autor_id,
                autor=autor
            )
            db.session.add(libro)
            db.session.flush()
        db.session.commit()
        print(f"Se crearon {libros_count} libros.")


if __name__ == '__main__':
    seed_data()
