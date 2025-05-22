# seed_data.py
from faker import Faker
from models import db, Autor
from app import app
import random

fake = Faker()


def seed_data(autores_count=10):
    with app.app_context():
        db.drop_all()
        db.create_all()

        for _ in range(autores_count):
            nombre = fake.name()
            email = fake.email()
            autor = Autor(nombre=nombre, email=email)
            db.session.add(autor)
            db.session.flush()
        db.session.commit()
        print(f"Se crearon {autores_count} autores.")


if __name__ == '__main__':
    seed_data()
