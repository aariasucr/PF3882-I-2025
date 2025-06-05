import pytest
import json
from app import app, db
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_create_cart(client):
    """Test creating a new cart"""
    response = client.post('/carts', 
                          json={'user_id': 'test_user'})
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['user_id'] == 'test_user'
    assert data['status'] == 'active'
    assert 'id' in data

def test_get_cart(client):
    """Test getting a cart by ID"""
    # First create a cart
    create_response = client.post('/carts', 
                                 json={'user_id': 'test_user'})
    cart_data = json.loads(create_response.data)
    cart_id = cart_data['id']
    
    # Get the cart
    response = client.get(f'/carts/{cart_id}')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['id'] == cart_id
    assert data['user_id'] == 'test_user'

@patch('app.get_product_info')
@patch('app.check_product_availability')
def test_add_item_to_cart(mock_availability, mock_product_info, client):
    """Test adding an item to cart"""
    # Mock external service responses
    mock_product_info.return_value = {
        'id': 'prod123',
        'name': 'Test Product',
        'price': 29.99
    }
    mock_availability.return_value = True
    
    # Create a cart
    create_response = client.post('/carts', 
                                 json={'user_id': 'test_user'})
    cart_data = json.loads(create_response.data)
    cart_id = cart_data['id']
    
    # Add item to cart
    response = client.post(f'/carts/{cart_id}/items',
                          json={
                              'product_id': 'prod123',
                              'quantity': 2
                          })
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert len(data['items']) == 1
    assert data['items'][0]['product_id'] == 'prod123'
    assert data['items'][0]['quantity'] == 2

@patch('app.check_product_availability')
def test_update_cart_item(mock_availability, client):
    """Test updating cart item quantity"""
    # Setup mocks and create cart with item
    mock_availability.return_value = True
    
    with patch('app.get_product_info') as mock_product_info:
        mock_product_info.return_value = {
            'id': 'prod123',
            'name': 'Test Product',
            'price': 29.99
        }
        
        # Create cart and add item
        create_response = client.post('/carts', json={'user_id': 'test_user'})
        cart_data = json.loads(create_response.data)
        cart_id = cart_data['id']
        
        client.post(f'/carts/{cart_id}/items',
                   json={'product_id': 'prod123', 'quantity': 2})
    
    # Get the cart to find the item ID
    cart_response = client.get(f'/carts/{cart_id}')
    cart_data = json.loads(cart_response.data)
    item_id = cart_data['items'][0]['id']
    
    # Update item quantity
    response = client.put(f'/carts/{cart_id}/items/{item_id}',
                         json={'quantity': 5})
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['items'][0]['quantity'] == 5

def test_remove_cart_item(client):
    """Test removing an item from cart"""
    with patch('app.get_product_info') as mock_product_info:
        with patch('app.check_product_availability') as mock_availability:
            mock_product_info.return_value = {
                'id': 'prod123',
                'name': 'Test Product',
                'price': 29.99
            }
            mock_availability.return_value = True
            
            # Create cart and add item
            create_response = client.post('/carts', json={'user_id': 'test_user'})
            cart_data = json.loads(create_response.data)
            cart_id = cart_data['id']
            
            client.post(f'/carts/{cart_id}/items',
                       json={'product_id': 'prod123', 'quantity': 2})
    
    # Get the cart to find the item ID
    cart_response = client.get(f'/carts/{cart_id}')
    cart_data = json.loads(cart_response.data)
    item_id = cart_data['items'][0]['id']
    
    # Remove item
    response = client.delete(f'/carts/{cart_id}/items/{item_id}')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['items']) == 0

def test_create_cart_missing_user_id(client):
    """Test creating cart without user_id"""
    response = client.post('/carts', json={})
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_get_nonexistent_cart(client):
    """Test getting a cart that doesn't exist"""
    response = client.get('/carts/nonexistent-id')
    assert response.status_code == 404 