# seed_data.py
from faker import Faker
from models import db, TaskList, Task
from app import app
import random

fake = Faker()


def seed_data(task_list_count=5, tasks_per_list=10):
    with app.app_context():
        db.drop_all()
        db.create_all()

        for _ in range(task_list_count):
            list_name = fake.bs().capitalize()
            task_list = TaskList(name=list_name)
            db.session.add(task_list)
            db.session.flush()

            for _ in range(tasks_per_list):
                task = Task(
                    title=fake.sentence(nb_words=5),
                    completed=random.choice([True, False]),
                    task_list_id=task_list.id
                )
                db.session.add(task)

        db.session.commit()
        print(
            f"Se crearon {task_list_count} listas de tareas con {tasks_per_list} tareas cada una.")


if __name__ == '__main__':
    seed_data()
