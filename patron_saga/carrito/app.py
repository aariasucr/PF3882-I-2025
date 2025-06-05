from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flasgger import Swagger, swag_from
from marshmallow import Schema, fields, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
import requests
import os
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration - support both PostgreSQL and SQLite
DATABASE_URL = os.getenv(
    'DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/saga')

# Fallback to SQLite if PostgreSQL is not available
if DATABASE_URL.startswith('postgresql://'):
    try:
        import psycopg2
        app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    except ImportError:
        print("PostgreSQL adapter not available, falling back to SQLite...")
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carrito.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
swagger = Swagger(app, template_file='swagger_config.yaml')

# External services URLs (you can configure these as environment variables)
INVENTARIO_SERVICE_URL = os.getenv(
    'INVENTARIO_SERVICE_URL', 'http://localhost:3001')
PAGOS_SERVICE_URL = os.getenv('PAGOS_SERVICE_URL', 'http://localhost:3002')

# Models - Use String for UUID when using SQLite


def get_uuid_column():
    return db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))


class Cart(db.Model):
    __tablename__ = 'carts'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False,
                       default='active')  # active, checked_out
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('CartItem', backref='cart',
                            lazy=True, cascade='all, delete-orphan')


class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cart_id = db.Column(db.String(36), db.ForeignKey(
        'carts.id'), nullable=False)
    product_id = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cart_id = db.Column(db.String(36), db.ForeignKey(
        'carts.id'), nullable=False)
    user_id = db.Column(db.String(100), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_id = db.Column(db.String(100))
    status = db.Column(db.String(20), nullable=False,
                       default='pending')  # pending, paid, failed
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)

# Schemas


class CartItemSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CartItem
        load_instance = True


class CartSchema(SQLAlchemyAutoSchema):
    items = fields.Nested(CartItemSchema, many=True, dump_only=True)

    class Meta:
        model = Cart
        load_instance = True


class OrderSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        load_instance = True


class AddItemSchema(Schema):
    product_id = fields.Str(required=True)
    quantity = fields.Int(required=True, validate=lambda x: x > 0)


class UpdateItemSchema(Schema):
    quantity = fields.Int(required=True, validate=lambda x: x > 0)


class CheckoutSchema(Schema):
    payment_method = fields.Str(required=True)
    billing_address = fields.Dict(required=True)


# Initialize schemas
cart_schema = CartSchema()
carts_schema = CartSchema(many=True)
order_schema = OrderSchema()
add_item_schema = AddItemSchema()
update_item_schema = UpdateItemSchema()
checkout_schema = CheckoutSchema()

# External service functions


def get_product_info(product_id):
    """Get product information from inventory service"""
    try:
        response = requests.get(
            f"{INVENTARIO_SERVICE_URL}/products/{product_id}")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        # For demo purposes, return mock data if service is not available
        return {
            'id': product_id,
            'name': f'Product {product_id}',
            'price': 29.99,
            'description': 'Demo product'
        }


def check_product_availability(product_id, quantity):
    """Check if product is available in inventory"""
    try:
        response = requests.get(
            f"{INVENTARIO_SERVICE_URL}/products/{product_id}/availability")
        if response.status_code == 200:
            data = response.json()
            return data.get('available_quantity', 0) >= quantity
        return False
    except requests.exceptions.RequestException:
        # For demo purposes, assume products are available
        return True


def process_payment(amount, payment_method, billing_address):
    """Process payment through payment gateway"""
    try:
        payload = {
            'amount': float(amount),
            'payment_method': payment_method,
            'billing_address': billing_address
        }
        response = requests.post(f"{PAGOS_SERVICE_URL}/payments", json=payload)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        # For demo purposes, return mock successful payment
        return {
            'payment_id': f'pay_{uuid.uuid4().hex[:8]}',
            'status': 'success',
            'amount': float(amount),
            'transaction_id': f'txn_{uuid.uuid4().hex[:12]}'
        }

# Routes


@app.route('/')
def index():
    db_type = 'PostgreSQL' if app.config['SQLALCHEMY_DATABASE_URI'].startswith(
        'postgresql://') else 'SQLite'
    return jsonify({
        'message': 'Shopping Cart API',
        'version': '1.0.0',
        'database': db_type,
        'endpoints': {
            'swagger': '/apidocs',
            'carts': '/carts',
            'items': '/carts/{cart_id}/items',
            'checkout': '/carts/{cart_id}/checkout',
            'orders': '/orders/{order_id}'
        }
    })


@app.route('/carts', methods=['POST'])
@swag_from({
    'tags': ['Cart'],
    'summary': 'Create a new cart',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'User ID'}
                },
                'required': ['user_id']
            }
        }
    ],
    'responses': {
        201: {'description': 'Cart created successfully'},
        400: {'description': 'Invalid input'}
    }
})
def create_cart():
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400

        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()

        return cart_schema.dump(cart), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/carts/<cart_id>', methods=['GET'])
@swag_from({
    'tags': ['Cart'],
    'summary': 'Get cart by ID',
    'parameters': [
        {
            'name': 'cart_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Cart ID'
        }
    ],
    'responses': {
        200: {'description': 'Cart retrieved successfully'},
        404: {'description': 'Cart not found'}
    }
})
def get_cart(cart_id):
    cart = Cart.query.get_or_404(cart_id)
    return cart_schema.dump(cart)


@app.route('/carts/<cart_id>/items', methods=['POST'])
@swag_from({
    'tags': ['Cart Items'],
    'summary': 'Add item to cart',
    'parameters': [
        {
            'name': 'cart_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Cart ID'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'product_id': {'type': 'string'},
                    'quantity': {'type': 'integer', 'minimum': 1}
                },
                'required': ['product_id', 'quantity']
            }
        }
    ],
    'responses': {
        201: {'description': 'Item added to cart'},
        400: {'description': 'Invalid input'},
        404: {'description': 'Cart or product not found'}
    }
})
def add_item_to_cart(cart_id):
    try:
        cart = Cart.query.get_or_404(cart_id)

        if cart.status != 'active':
            return jsonify({'error': 'Cannot modify inactive cart'}), 400

        data = add_item_schema.load(request.get_json())
        product_id = data['product_id']
        quantity = data['quantity']

        # Get product info from inventory service
        product_info = get_product_info(product_id)
        if not product_info:
            return jsonify({'error': 'Product not found'}), 404

        # Check availability
        if not check_product_availability(product_id, quantity):
            return jsonify({'error': 'Insufficient inventory'}), 400

        # Check if item already exists in cart
        existing_item = CartItem.query.filter_by(
            cart_id=cart_id, product_id=product_id).first()

        if existing_item:
            new_quantity = existing_item.quantity + quantity
            if not check_product_availability(product_id, new_quantity):
                return jsonify({'error': 'Insufficient inventory for total quantity'}), 400
            existing_item.quantity = new_quantity
        else:
            cart_item = CartItem(
                cart_id=cart_id,
                product_id=product_id,
                quantity=quantity,
                unit_price=product_info['price']
            )
            db.session.add(cart_item)

        cart.updated_at = datetime.utcnow()
        db.session.commit()

        return cart_schema.dump(cart), 201

    except ValidationError as e:
        return jsonify({'error': e.messages}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/carts/<cart_id>/items/<item_id>', methods=['PUT'])
@swag_from({
    'tags': ['Cart Items'],
    'summary': 'Update item quantity in cart',
    'parameters': [
        {
            'name': 'cart_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Cart ID'
        },
        {
            'name': 'item_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Item ID'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'quantity': {'type': 'integer', 'minimum': 1}
                },
                'required': ['quantity']
            }
        }
    ],
    'responses': {
        200: {'description': 'Item updated successfully'},
        400: {'description': 'Invalid input'},
        404: {'description': 'Cart or item not found'}
    }
})
def update_cart_item(cart_id, item_id):
    try:
        cart = Cart.query.get_or_404(cart_id)

        if cart.status != 'active':
            return jsonify({'error': 'Cannot modify inactive cart'}), 400

        cart_item = CartItem.query.filter_by(
            id=item_id, cart_id=cart_id).first_or_404()

        data = update_item_schema.load(request.get_json())
        new_quantity = data['quantity']

        # Check availability
        if not check_product_availability(cart_item.product_id, new_quantity):
            return jsonify({'error': 'Insufficient inventory'}), 400

        cart_item.quantity = new_quantity
        cart.updated_at = datetime.utcnow()
        db.session.commit()

        return cart_schema.dump(cart)

    except ValidationError as e:
        return jsonify({'error': e.messages}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/carts/<cart_id>/items/<item_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Cart Items'],
    'summary': 'Remove item from cart',
    'parameters': [
        {
            'name': 'cart_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Cart ID'
        },
        {
            'name': 'item_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Item ID'
        }
    ],
    'responses': {
        200: {'description': 'Item removed successfully'},
        404: {'description': 'Cart or item not found'}
    }
})
def remove_cart_item(cart_id, item_id):
    try:
        cart = Cart.query.get_or_404(cart_id)

        if cart.status != 'active':
            return jsonify({'error': 'Cannot modify inactive cart'}), 400

        cart_item = CartItem.query.filter_by(
            id=item_id, cart_id=cart_id).first_or_404()

        db.session.delete(cart_item)
        cart.updated_at = datetime.utcnow()
        db.session.commit()

        return cart_schema.dump(cart)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/carts/<cart_id>/checkout', methods=['POST'])
@swag_from({
    'tags': ['Checkout'],
    'summary': 'Checkout cart and process payment',
    'parameters': [
        {
            'name': 'cart_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Cart ID'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'payment_method': {'type': 'string'},
                    'billing_address': {
                        'type': 'object',
                        'properties': {
                            'street': {'type': 'string'},
                            'city': {'type': 'string'},
                            'country': {'type': 'string'},
                            'postal_code': {'type': 'string'}
                        }
                    }
                },
                'required': ['payment_method', 'billing_address']
            }
        }
    ],
    'responses': {
        200: {'description': 'Checkout successful'},
        400: {'description': 'Invalid input or empty cart'},
        404: {'description': 'Cart not found'}
    }
})
def checkout_cart(cart_id):
    try:
        cart = Cart.query.get_or_404(cart_id)

        if cart.status != 'active':
            return jsonify({'error': 'Cart is not active'}), 400

        if not cart.items:
            return jsonify({'error': 'Cart is empty'}), 400

        data = checkout_schema.load(request.get_json())

        # Calculate total amount
        total_amount = sum(
            item.quantity * item.unit_price for item in cart.items)

        # Verify inventory availability for all items
        for item in cart.items:
            if not check_product_availability(item.product_id, item.quantity):
                return jsonify({'error': f'Insufficient inventory for product {item.product_id}'}), 400

        # Process payment
        payment_result = process_payment(
            total_amount,
            data['payment_method'],
            data['billing_address']
        )

        if not payment_result:
            return jsonify({'error': 'Payment processing failed'}), 400

        # Create order
        order = Order(
            cart_id=cart_id,
            user_id=cart.user_id,
            total_amount=total_amount,
            payment_id=payment_result.get('payment_id'),
            status='paid' if payment_result.get(
                'status') == 'success' else 'failed'
        )

        # Update cart status
        cart.status = 'checked_out'

        db.session.add(order)
        db.session.commit()

        return {
            'order': order_schema.dump(order),
            'payment': payment_result
        }

    except ValidationError as e:
        return jsonify({'error': e.messages}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/orders/<order_id>', methods=['GET'])
@swag_from({
    'tags': ['Orders'],
    'summary': 'Get order by ID',
    'parameters': [
        {
            'name': 'order_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Order ID'
        }
    ],
    'responses': {
        200: {'description': 'Order retrieved successfully'},
        404: {'description': 'Order not found'}
    }
})
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    return order_schema.dump(order)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=3000)
