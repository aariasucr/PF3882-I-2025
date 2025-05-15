import pytest
from biz_logic import *
from models import db
from app import app


@pytest.fixture
def client_app():
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


def test_create_task_list(client_app):
    with client_app.app_context():
        tl = create_task_list("Mi Lista")
        assert tl.name == "Mi Lista"


def test_create_task(client_app):
    with client_app.app_context():
        tl = create_task_list("Mi Lista")
        task = create_task("Mi tarea", tl.id)
        assert task.title == "Mi tarea"
        assert task.task_list.id == tl.id
