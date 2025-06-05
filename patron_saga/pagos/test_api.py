import pytest
import json
from app import create_app
from models import db


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'


def test_create_payment(client):
    """Test payment creation"""
    payment_data = {
        "merchant_id": "test_merchant",
        "order_id": "test_order_123",
        "amount": 99.99,
        "currency": "USD",
        "payment_method": "credit_card",
        "customer_email": "test@example.com",
        "customer_name": "Test Customer",
        "card_number": "4111111111111111",
        "card_expiry_month": 12,
        "card_expiry_year": 2025,
        "card_cvv": "123",
        "description": "Test payment"
    }

    response = client.post('/api/v1/payments',
                           data=json.dumps(payment_data),
                           content_type='application/json')

    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['merchant_id'] == 'test_merchant'
    assert data['amount'] == '99.99'
    assert data['status'] == 'pending'


def test_get_payment(client):
    """Test getting payment details"""
    # First create a payment
    payment_data = {
        "merchant_id": "test_merchant",
        "order_id": "test_order_456",
        "amount": 50.00,
        "payment_method": "credit_card",
        "customer_email": "test@example.com",
        "customer_name": "Test Customer",
        "card_number": "4111111111111111",
        "card_expiry_month": 12,
        "card_expiry_year": 2025,
        "card_cvv": "123"
    }

    create_response = client.post('/api/v1/payments',
                                  data=json.dumps(payment_data),
                                  content_type='application/json')

    assert create_response.status_code == 201
    payment_id = json.loads(create_response.data)['id']

    # Get the payment
    get_response = client.get(f'/api/v1/payments/{payment_id}')
    assert get_response.status_code == 200

    data = json.loads(get_response.data)
    assert data['id'] == payment_id
    assert data['amount'] == '50.00'


def test_invalid_payment(client):
    """Test creating payment with invalid data"""
    invalid_data = {
        "merchant_id": "",  # Invalid: empty string
        "amount": "invalid",  # Invalid: not a number
        "payment_method": "invalid_method"  # Invalid: not in enum
    }

    response = client.post('/api/v1/payments',
                           data=json.dumps(invalid_data),
                           content_type='application/json')

    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == 'Validation Error'


def test_payment_not_found(client):
    """Test getting non-existent payment"""
    response = client.get('/api/v1/payments/non-existent-id')
    assert response.status_code == 404

    data = json.loads(response.data)
    assert data['error'] == 'Not Found'
