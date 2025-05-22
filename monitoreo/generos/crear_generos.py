# seed_data.py
from faker import Faker
from models import db, Genero
from app import app
import random

fake = Faker()


def seed_data(generos_count=10):
    with app.app_context():
        db.drop_all()
        db.create_all()

        for _ in range(generos_count):
            nombre = fake.catch_phrase()
            description = fake.paragraph(nb_sentences=3)
            genero = Genero(nombre=nombre, description=description)
            db.session.add(genero)
            db.session.flush()
        db.session.commit()
        print(f"Se crearon {generos_count} generos.")


if __name__ == '__main__':
    seed_data()
