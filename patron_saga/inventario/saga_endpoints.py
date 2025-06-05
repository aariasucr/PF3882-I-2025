from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from app import db, Product
import uuid
from datetime import datetime, timedelta
import sys
import os

# Add the saga_choreography directory to the path to import event_bus
sys.path.append(os.path.join(os.path.dirname(
    __file__), '..', 'saga_choreography'))

try:
    from event_bus import (
        event_bus, SagaEvent,
        publish_inventory_reserved, publish_inventory_reserve_failed,
        publish_inventory_committed, publish_inventory_commit_failed,
        publish_inventory_unreserved
    )
    CHOREOGRAPHY_ENABLED = True
except ImportError:
    CHOREOGRAPHY_ENABLED = False
    print("Warning: Choreography event bus not available")

saga_bp = Blueprint('saga', __name__)

# Models for Saga support


class InventoryReservation(db.Model):
    __tablename__ = 'inventory_reservations'

    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    cart_id = db.Column(db.String(36), nullable=False)
    saga_id = db.Column(db.String(36))
    product_id = db.Column(db.Integer, db.ForeignKey(
        'products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    # reserved, committed, cancelled
    status = db.Column(db.String(20), default='reserved')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(
        db.DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=30))

    product = db.relationship('Product', backref='reservations')

# Orchestrated Saga Endpoints


@saga_bp.route('/api/products/reserve', methods=['POST'])
def reserve_inventory():
    """Reserve inventory for orchestrated saga"""
    try:
        data = request.json
        cart_id = data['cart_id']
        items = data['items']
        saga_id = data.get('saga_id')

        reservations = []

        # Check availability for all items first
        for item in items:
            product = Product.query.get(item['product_id'])
            if not product:
                return jsonify({'error': f'Product {item["product_id"]} not found'}), 404

            if product.quantity < item['quantity']:
                return jsonify({
                    'error': f'Insufficient inventory for product {item["product_id"]}',
                    'available': product.quantity,
                    'requested': item['quantity']
                }), 400

        # Reserve all items
        for item in items:
            product = Product.query.get(item['product_id'])

            # Create reservation
            reservation = InventoryReservation(
                cart_id=cart_id,
                saga_id=saga_id,
                product_id=product.id,
                quantity=item['quantity']
            )

            # Reduce available quantity
            product.quantity -= item['quantity']

            db.session.add(reservation)
            reservations.append({
                'reservation_id': reservation.id,
                'product_id': product.id,
                'quantity': item['quantity']
            })

        db.session.commit()

        return jsonify({
            'cart_id': cart_id,
            'reservations': reservations,
            'status': 'reserved',
            'expires_at': (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@saga_bp.route('/api/products/unreserve', methods=['POST'])
def unreserve_inventory():
    """Unreserve inventory for orchestrated saga compensation"""
    try:
        data = request.json
        cart_id = data['cart_id']
        saga_id = data.get('saga_id')

        # Find reservations
        reservations = InventoryReservation.query.filter_by(
            cart_id=cart_id,
            status='reserved'
        ).all()

        if saga_id:
            reservations = [r for r in reservations if r.saga_id == saga_id]

        # Restore inventory
        for reservation in reservations:
            product = Product.query.get(reservation.product_id)
            if product:
                product.quantity += reservation.quantity

            reservation.status = 'cancelled'

        db.session.commit()

        return jsonify({
            'cart_id': cart_id,
            'unreserved_items': len(reservations),
            'status': 'unreserved'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@saga_bp.route('/api/products/commit', methods=['POST'])
def commit_inventory():
    """Commit inventory reservations for orchestrated saga"""
    try:
        data = request.json
        cart_id = data['cart_id']
        saga_id = data.get('saga_id')

        # Find reservations
        reservations = InventoryReservation.query.filter_by(
            cart_id=cart_id,
            status='reserved'
        ).all()

        if saga_id:
            reservations = [r for r in reservations if r.saga_id == saga_id]

        if not reservations:
            return jsonify({'error': 'No reservations found for cart'}), 404

        # Commit reservations
        for reservation in reservations:
            reservation.status = 'committed'

        db.session.commit()

        return jsonify({
            'cart_id': cart_id,
            'committed_items': len(reservations),
            'status': 'committed'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@saga_bp.route('/api/products/restore', methods=['POST'])
def restore_inventory():
    """Restore inventory after commit failure for orchestrated saga"""
    try:
        data = request.json
        cart_id = data['cart_id']
        saga_id = data.get('saga_id')

        # Find committed reservations
        reservations = InventoryReservation.query.filter_by(
            cart_id=cart_id,
            status='committed'
        ).all()

        if saga_id:
            reservations = [r for r in reservations if r.saga_id == saga_id]

        # Restore inventory
        for reservation in reservations:
            product = Product.query.get(reservation.product_id)
            if product:
                product.quantity += reservation.quantity

            reservation.status = 'cancelled'

        db.session.commit()

        return jsonify({
            'cart_id': cart_id,
            'restored_items': len(reservations),
            'status': 'restored'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Choreographed Saga Event Handlers


class InventorySagaHandler:
    def __init__(self):
        if CHOREOGRAPHY_ENABLED:
            self.setup_event_handlers()

    def setup_event_handlers(self):
        """Setup event handlers for choreographed saga"""

        # Subscribe to checkout initiated event
        event_bus.subscribe_to_event(
            SagaEvent.CHECKOUT_INITIATED,
            self.handle_checkout_initiated,
            "inventory_checkout_initiated"
        )

        # Subscribe to inventory reserve request
        event_bus.subscribe_to_event(
            SagaEvent.INVENTORY_RESERVE_REQUESTED,
            self.handle_inventory_reserve_requested,
            "inventory_reserve_requested"
        )

        # Subscribe to inventory commit request
        event_bus.subscribe_to_event(
            SagaEvent.INVENTORY_COMMIT_REQUESTED,
            self.handle_inventory_commit_requested,
            "inventory_commit_requested"
        )

        # Subscribe to compensation events
        event_bus.subscribe_to_event(
            SagaEvent.INVENTORY_UNRESERVE_REQUESTED,
            self.handle_inventory_unreserve_requested,
            "inventory_unreserve_requested"
        )

    def handle_checkout_initiated(self, event):
        """Handle checkout initiated event - start inventory reservation"""
        data = event['data']
        saga_id = data['saga_id']
        cart_id = data['cart_id']

        # Get cart items (you might need to call cart service here)
        # For now, using mock data
        # Replace with actual cart lookup
        items = [{'product_id': 1, 'quantity': 2}]

        # Publish inventory reserve request
        from event_bus import publish_inventory_reserve_requested
        publish_inventory_reserve_requested(saga_id, cart_id, items)

    def handle_inventory_reserve_requested(self, event):
        """Handle inventory reserve request"""
        data = event['data']
        saga_id = data['saga_id']
        cart_id = data['cart_id']
        items = data['items']

        try:
            reservations = []

            # Check availability for all items first
            for item in items:
                product = Product.query.get(item['product_id'])
                if not product or product.quantity < item['quantity']:
                    publish_inventory_reserve_failed(
                        saga_id, cart_id,
                        f'Insufficient inventory for product {item["product_id"]}'
                    )
                    return

            # Reserve all items
            for item in items:
                product = Product.query.get(item['product_id'])

                reservation = InventoryReservation(
                    cart_id=cart_id,
                    saga_id=saga_id,
                    product_id=product.id,
                    quantity=item['quantity']
                )

                product.quantity -= item['quantity']
                db.session.add(reservation)
                reservations.append(reservation.id)

            db.session.commit()

            # Publish success event
            publish_inventory_reserved(
                saga_id, cart_id, f"reservation_{cart_id}")

        except Exception as e:
            db.session.rollback()
            publish_inventory_reserve_failed(saga_id, cart_id, str(e))

    def handle_inventory_commit_requested(self, event):
        """Handle inventory commit request"""
        data = event['data']
        saga_id = data['saga_id']
        cart_id = data['cart_id']

        try:
            # Find reservations
            reservations = InventoryReservation.query.filter_by(
                cart_id=cart_id,
                saga_id=saga_id,
                status='reserved'
            ).all()

            if not reservations:
                publish_inventory_commit_failed(
                    saga_id, 'No reservations found')
                return

            # Commit reservations
            for reservation in reservations:
                reservation.status = 'committed'

            db.session.commit()

            # Publish success event
            publish_inventory_committed(saga_id, cart_id)

        except Exception as e:
            db.session.rollback()
            from event_bus import publish_inventory_commit_failed
            publish_inventory_commit_failed(saga_id, str(e))

    def handle_inventory_unreserve_requested(self, event):
        """Handle inventory unreserve request for compensation"""
        data = event['data']
        saga_id = data['saga_id']
        cart_id = data['cart_id']

        try:
            # Find reservations
            reservations = InventoryReservation.query.filter_by(
                cart_id=cart_id,
                saga_id=saga_id
            ).filter(InventoryReservation.status.in_(['reserved', 'committed'])).all()

            # Restore inventory
            for reservation in reservations:
                product = Product.query.get(reservation.product_id)
                if product:
                    product.quantity += reservation.quantity

                reservation.status = 'cancelled'

            db.session.commit()

            # Publish success event
            publish_inventory_unreserved(saga_id, cart_id)

        except Exception as e:
            db.session.rollback()
            print(f"Error unreserving inventory: {str(e)}")

# Status endpoints


@saga_bp.route('/api/products/reservations/<cart_id>', methods=['GET'])
def get_reservations(cart_id):
    """Get reservations for a cart"""
    reservations = InventoryReservation.query.filter_by(cart_id=cart_id).all()

    return jsonify({
        'cart_id': cart_id,
        'reservations': [
            {
                'id': r.id,
                'product_id': r.product_id,
                'quantity': r.quantity,
                'status': r.status,
                'created_at': r.created_at.isoformat(),
                'expires_at': r.expires_at.isoformat()
            }
            for r in reservations
        ]
    })


@saga_bp.route('/api/products/availability/<int:product_id>', methods=['GET'])
def get_product_availability(product_id):
    """Get product availability"""
    product = Product.query.get_or_404(product_id)

    # Calculate reserved quantity
    reserved_qty = db.session.query(
        db.func.sum(InventoryReservation.quantity)
    ).filter_by(
        product_id=product_id,
        status='reserved'
    ).scalar() or 0

    return jsonify({
        'product_id': product_id,
        'total_quantity': product.quantity,
        'reserved_quantity': reserved_qty,
        'available_quantity': product.quantity
    })


# Initialize saga handler
if CHOREOGRAPHY_ENABLED:
    inventory_saga_handler = InventorySagaHandler()

# Health check


@saga_bp.route('/saga/health', methods=['GET'])
def saga_health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'inventory-saga',
        'choreography_enabled': CHOREOGRAPHY_ENABLED
    })
