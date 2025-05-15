import pytest
from app import app, db


@pytest.fixture
def client():
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


def test_create_list(client):
    response = client.post(
        '/api/lists', json={"name": "List1"}, headers={"Content-Type": "application/json"})

    assert response.status_code == 201
    assert "List1" in response.get_data(as_text=True)
