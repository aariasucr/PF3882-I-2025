from locust import HttpUser, task, between
import json
import random
from faker import Faker


class LibrosTest(HttpUser):
    wait_time = between(1, 3)

    @task
    def get_libros(self):

        response = self.client.get("/libros")
        if response.status_code == 200:
            libros = json.loads(response.text)
            print(f"Obtuvimos una lista con {len(libros)} libros.")
        else:
            print("Failed to fetch books.")

    @task
    def get_random_libro(self):
        random_id = random.randint(1, 10)
        response = self.client.get(f"/libros/{random_id}")
        if response.status_code == 200:
            print(f"Libro encontrado con ID {random_id}:")
        else:
            print(
                f"Error al buscar el libro con ID {random_id}: {response.status_code}")

    @task
    def create_libro(self):
        fake = Faker()
        libro_data = {
            "descripcion": fake.sentence(),
            "titulo": fake.name(),
            "autor_id": random.randint(1, 20),
            "genero_id": random.randint(1, 20)
        }
        response = self.client.post("/libros", json=libro_data)
        if response.status_code == 201:
            print("Libro creado exitosamente.")
        else:
            print(f"Error al crear el libro: {response.status_code}")
