import pytest
import requests
from pact import Consumer, Provider

PACT_MOCK_HOST = 'localhost'
PACT_MOCK_PORT = 1234
PACT_URL = f'http://{PACT_MOCK_HOST}:{PACT_MOCK_PORT}'


@pytest.fixture(scope='module')
def pact():
    pact = Consumer('TaskConsumer').has_pact_with(
        Provider('TaskProvider'),
        host_name=PACT_MOCK_HOST,
        port=PACT_MOCK_PORT,
        log_dir='./logs',
        pact_dir='./pacts'
    )
    pact.start_service()
    yield pact
    pact.stop_service()


def test_create_list_contract(pact):
    expected = {
        "name": "Lista nueva"
    }

    # Definimos el comportamiento esperado del MOCK
    (pact
     .given("La lista no existe")
     .upon_receiving("una solicitud para crear una lista")
     .with_request("POST", "/api/lists", body={"name": "Lista nueva"}, headers={"Content-Type": "application/json"})
     .will_respond_with(201, body=expected))

    # Aquí se ejecuta el código que hace la solicitud a la API
    # y genera el PACT en JSON que luego se puede verificar
    with pact:
        response = requests.post(
            f"{PACT_URL}/api/lists", json={"name": "Lista nueva"})
        assert response.status_code == 201
        assert response.json() == expected
