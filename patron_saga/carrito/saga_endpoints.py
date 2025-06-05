from flask import Blueprint, request, jsonify
from app import db, Order, Cart
import uuid
from datetime import datetime
import sys
import os

# Add the saga_choreography directory to the path to import event_bus
sys.path.append(os.path.join(os.path.dirname(
    __file__), '..', 'saga_choreography'))

try:
    from event_bus import (
        event_bus, SagaEvent,
        publish_order_created, publish_order_create_failed,
        publish_order_cancelled
    )
    CHOREOGRAPHY_ENABLED = True
except ImportError:
    CHOREOGRAPHY_ENABLED = False
    print("Warning: Choreography event bus not available")

saga_bp = Blueprint('saga', __name__)

# Models for Saga support


class SagaOrder(db.Model):
    __tablename__ = 'saga_orders'

    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    cart_id = db.Column(db.String(36), nullable=False)
    saga_id = db.Column(db.String(36))
    user_id = db.Column(db.String(100), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_id = db.Column(db.String(100))
    payment_method = db.Column(db.String(50))
    # pending, confirmed, cancelled
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Orchestrated Saga Endpoints


@saga_bp.route('/orders', methods=['POST'])
def create_saga_order():
    """Create order for orchestrated saga"""
    try:
        data = request.json
        cart_id = data['cart_id']
        user_id = data['user_id']
        total_amount = data['total_amount']
        payment_method = data.get('payment_method')
        payment_id = data.get('payment_id')
        saga_id = data.get('saga_id')

        # Check if cart exists
        cart = Cart.query.get(cart_id)
        if not cart:
            return jsonify({'error': 'Cart not found'}), 404

        # Create saga order
        order = SagaOrder(
            cart_id=cart_id,
            saga_id=saga_id,
            user_id=user_id,
            total_amount=total_amount,
            payment_id=payment_id,
            payment_method=payment_method,
            status='pending'
        )

        db.session.add(order)

        # Update cart status
        cart.status = 'checked_out'

        db.session.commit()

        return jsonify({
            'order_id': order.id,
            'cart_id': cart_id,
            'user_id': user_id,
            'total_amount': str(total_amount),
            'payment_id': payment_id,
            'status': 'pending'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@saga_bp.route('/orders/<order_id>/cancel', methods=['POST'])
def cancel_saga_order(order_id):
    """Cancel order for orchestrated saga compensation"""
    try:
        data = request.json or {}
        reason = data.get('reason', 'Saga compensation')

        order = SagaOrder.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        # Cancel order
        order.status = 'cancelled'

        # Restore cart status if needed
        cart = Cart.query.get(order.cart_id)
        if cart:
            cart.status = 'active'

        db.session.commit()

        return jsonify({
            'order_id': order_id,
            'status': 'cancelled',
            'reason': reason
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@saga_bp.route('/orders/<order_id>/confirm', methods=['POST'])
def confirm_saga_order(order_id):
    """Confirm order for orchestrated saga"""
    try:
        order = SagaOrder.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404

        # Confirm order
        order.status = 'confirmed'

        db.session.commit()

        return jsonify({
            'order_id': order_id,
            'status': 'confirmed'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Choreographed Saga Event Handlers


class CartSagaHandler:
    def __init__(self):
        if CHOREOGRAPHY_ENABLED:
            self.setup_event_handlers()

    def setup_event_handlers(self):
        """Setup event handlers for choreographed saga"""

        # Subscribe to order create request
        event_bus.subscribe_to_event(
            SagaEvent.ORDER_CREATE_REQUESTED,
            self.handle_order_create_requested,
            "cart_order_create_requested"
        )

        # Subscribe to order cancel request (compensation)
        event_bus.subscribe_to_event(
            SagaEvent.ORDER_CANCEL_REQUESTED,
            self.handle_order_cancel_requested,
            "cart_order_cancel_requested"
        )

    def handle_order_create_requested(self, event):
        """Handle order creation request"""
        data = event['data']
        saga_id = data['saga_id']
        cart_id = data['cart_id']
        user_id = data['user_id']
        total_amount = data['total_amount']
        payment_id = data['payment_id']

        try:
            # Check if cart exists
            cart = Cart.query.get(cart_id)
            if not cart:
                publish_order_create_failed(saga_id, 'Cart not found')
                return

            # Create saga order
            order = SagaOrder(
                cart_id=cart_id,
                saga_id=saga_id,
                user_id=user_id,
                total_amount=total_amount,
                payment_id=payment_id,
                status='pending'
            )

            db.session.add(order)

            # Update cart status
            cart.status = 'checked_out'

            db.session.commit()

            # Publish success event
            publish_order_created(saga_id, order.id)

        except Exception as e:
            db.session.rollback()
            publish_order_create_failed(saga_id, str(e))

    def handle_order_cancel_requested(self, event):
        """Handle order cancellation request for compensation"""
        data = event['data']
        saga_id = data['saga_id']
        order_id = data['order_id']

        try:
            order = SagaOrder.query.filter_by(
                id=order_id,
                saga_id=saga_id
            ).first()

            if not order:
                print(f"Order {order_id} not found for saga {saga_id}")
                return

            # Cancel order
            order.status = 'cancelled'

            # Restore cart status
            cart = Cart.query.get(order.cart_id)
            if cart:
                cart.status = 'active'

            db.session.commit()

            # Publish success event
            publish_order_cancelled(saga_id, order_id)

        except Exception as e:
            db.session.rollback()
            print(f"Error cancelling order: {str(e)}")

# Status endpoints


@saga_bp.route('/orders/saga/<cart_id>', methods=['GET'])
def get_saga_orders_by_cart(cart_id):
    """Get saga orders for a cart"""
    orders = SagaOrder.query.filter_by(cart_id=cart_id).all()

    return jsonify({
        'cart_id': cart_id,
        'orders': [
            {
                'id': o.id,
                'saga_id': o.saga_id,
                'user_id': o.user_id,
                'total_amount': str(o.total_amount),
                'payment_id': o.payment_id,
                'payment_method': o.payment_method,
                'status': o.status,
                'created_at': o.created_at.isoformat(),
                'updated_at': o.updated_at.isoformat()
            }
            for o in orders
        ]
    })


@saga_bp.route('/orders/saga/<saga_id>/status', methods=['GET'])
def get_saga_order_by_saga_id(saga_id):
    """Get saga order by saga ID"""
    order = SagaOrder.query.filter_by(saga_id=saga_id).first()

    if not order:
        return jsonify({'error': 'Order not found'}), 404

    return jsonify({
        'order_id': order.id,
        'saga_id': order.saga_id,
        'cart_id': order.cart_id,
        'user_id': order.user_id,
        'total_amount': str(order.total_amount),
        'payment_id': order.payment_id,
        'payment_method': order.payment_method,
        'status': order.status,
        'created_at': order.created_at.isoformat(),
        'updated_at': order.updated_at.isoformat()
    })

# Enhanced checkout endpoint that can trigger saga


@saga_bp.route('/checkout/saga', methods=['POST'])
def saga_checkout():
    """Enhanced checkout that can work with both saga patterns"""
    try:
        data = request.json
        cart_id = data['cart_id']
        user_id = data['user_id']
        payment_method = data['payment_method']
        billing_address = data['billing_address']
        # orchestrated or choreographed
        saga_pattern = data.get('saga_pattern', 'orchestrated')

        # Check if cart exists and has items
        cart = Cart.query.get(cart_id)
        if not cart:
            return jsonify({'error': 'Cart not found'}), 404

        if not cart.items:
            return jsonify({'error': 'Cart is empty'}), 400

        total_amount = sum(float(item.unit_price) *
                           item.quantity for item in cart.items)

        if saga_pattern == 'orchestrated':
            # Call orchestrator service
            import requests
            orchestrator_url = os.getenv(
                'ORCHESTRATOR_URL', 'http://localhost:3003')

            response = requests.post(f"{orchestrator_url}/saga/checkout", json={
                'cart_id': cart_id,
                'user_id': user_id,
                'payment_method': payment_method,
                'billing_address': billing_address
            })

            if response.status_code == 201:
                return jsonify({
                    'checkout_type': 'orchestrated_saga',
                    'saga_id': response.json()['saga_id'],
                    'cart_id': cart_id,
                    'total_amount': total_amount,
                    'status': 'initiated'
                }), 201
            else:
                return jsonify({'error': 'Failed to initiate orchestrated saga'}), 500

        elif saga_pattern == 'choreographed':
            # Call choreography coordinator
            import requests
            coordinator_url = os.getenv(
                'CHOREOGRAPHY_URL', 'http://localhost:3004')

            response = requests.post(f"{coordinator_url}/saga/choreography/checkout", json={
                'cart_id': cart_id,
                'user_id': user_id,
                'payment_method': payment_method,
                'billing_address': billing_address
            })

            if response.status_code == 201:
                return jsonify({
                    'checkout_type': 'choreographed_saga',
                    'saga_id': response.json()['saga_id'],
                    'cart_id': cart_id,
                    'total_amount': total_amount,
                    'status': 'initiated'
                }), 201
            else:
                return jsonify({'error': 'Failed to initiate choreographed saga'}), 500

        else:
            return jsonify({'error': 'Invalid saga pattern. Use "orchestrated" or "choreographed"'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Initialize saga handler
if CHOREOGRAPHY_ENABLED:
    cart_saga_handler = CartSagaHandler()

# Health check


@saga_bp.route('/saga/health', methods=['GET'])
def saga_health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'cart-saga',
        'choreography_enabled': CHOREOGRAPHY_ENABLED
    })
