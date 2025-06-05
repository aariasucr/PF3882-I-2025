from flask import Blueprint, request, jsonify
from models import db, Payment, PaymentStatus
from services import PaymentService
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
        publish_payment_processed, publish_payment_failed,
        publish_payment_refunded
    )
    CHOREOGRAPHY_ENABLED = True
except ImportError:
    CHOREOGRAPHY_ENABLED = False
    print("Warning: Choreography event bus not available")

saga_bp = Blueprint('saga', __name__)

# Models for Saga support


class SagaPayment(db.Model):
    __tablename__ = 'saga_payments'

    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    saga_id = db.Column(db.String(36))
    cart_id = db.Column(db.String(36))
    payment_id = db.Column(db.String(36), db.ForeignKey('payments.id'))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD')
    payment_method = db.Column(db.String(50), nullable=False)
    customer_email = db.Column(db.String(255))
    # pending, processed, failed, refunded
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    payment = db.relationship('Payment', backref='saga_payments')

# Orchestrated Saga Endpoints


@saga_bp.route('/api/v1/payments/saga', methods=['POST'])
def create_saga_payment():
    """Create payment for orchestrated saga"""
    try:
        data = request.json
        saga_id = data.get('saga_id')
        cart_id = data.get('cart_id')
        amount = data['amount']
        payment_method = data['payment_method']
        customer_email = data.get('customer_email')

        # Create payment using existing service
        payment_data = {
            'merchant_id': 'ecommerce_store',
            'order_id': cart_id,
            'amount': amount,
            'currency': 'USD',
            'payment_method': payment_method,
            'customer_email': customer_email,
            'customer_name': customer_email.split('@')[0] if customer_email else 'Customer',
            'description': f'Saga payment for cart {cart_id}'
        }

        payment = PaymentService.create_payment(payment_data)

        # Create saga payment record
        saga_payment = SagaPayment(
            saga_id=saga_id,
            cart_id=cart_id,
            payment_id=payment.id,
            amount=amount,
            payment_method=payment_method,
            customer_email=customer_email,
            status='pending'
        )

        db.session.add(saga_payment)
        db.session.commit()

        # Process payment immediately for orchestrated saga
        try:
            PaymentService.process_payment(payment.id)
            payment = PaymentService.get_payment(payment.id)

            if payment.status == PaymentStatus.COMPLETED:
                saga_payment.status = 'processed'
                db.session.commit()

                return jsonify({
                    'payment_id': payment.id,
                    'saga_id': saga_id,
                    'cart_id': cart_id,
                    'amount': str(amount),
                    'status': 'processed',
                    'transaction_id': payment.reference_number
                }), 200
            else:
                saga_payment.status = 'failed'
                db.session.commit()

                return jsonify({
                    'error': 'Payment processing failed',
                    'payment_id': payment.id,
                    'status': 'failed'
                }), 400

        except Exception as e:
            saga_payment.status = 'failed'
            db.session.commit()
            return jsonify({'error': f'Payment processing error: {str(e)}'}), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@saga_bp.route('/api/v1/payments/saga/<payment_id>/refund', methods=['POST'])
def refund_saga_payment(payment_id):
    """Refund payment for orchestrated saga compensation"""
    try:
        data = request.json or {}
        reason = data.get('reason', 'Saga compensation')
        saga_id = data.get('saga_id')

        # Find saga payment
        saga_payment = SagaPayment.query.filter_by(
            payment_id=payment_id).first()
        if saga_id and saga_payment:
            saga_payment = SagaPayment.query.filter_by(
                payment_id=payment_id,
                saga_id=saga_id
            ).first()

        if not saga_payment:
            return jsonify({'error': 'Saga payment not found'}), 404

        # Process refund using existing service
        refund_data = {'reason': reason}
        refund = PaymentService.refund_payment(payment_id, refund_data)

        if refund:
            saga_payment.status = 'refunded'
            db.session.commit()

            return jsonify({
                'payment_id': payment_id,
                'refund_id': refund.id,
                'amount': str(refund.amount),
                'status': 'refunded',
                'reason': reason
            }), 200
        else:
            return jsonify({'error': 'Refund processing failed'}), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Choreographed Saga Event Handlers


class PaymentSagaHandler:
    def __init__(self):
        if CHOREOGRAPHY_ENABLED:
            self.setup_event_handlers()

    def setup_event_handlers(self):
        """Setup event handlers for choreographed saga"""

        # Subscribe to payment request
        event_bus.subscribe_to_event(
            SagaEvent.PAYMENT_REQUESTED,
            self.handle_payment_requested,
            "payment_requested"
        )

        # Subscribe to payment refund request (compensation)
        event_bus.subscribe_to_event(
            SagaEvent.PAYMENT_REFUND_REQUESTED,
            self.handle_payment_refund_requested,
            "payment_refund_requested"
        )

    def handle_payment_requested(self, event):
        """Handle payment request"""
        data = event['data']
        saga_id = data['saga_id']
        cart_id = data['cart_id']
        amount = data['amount']
        payment_method = data['payment_method']
        customer_email = data['customer_email']

        try:
            # Create payment using existing service
            payment_data = {
                'merchant_id': 'ecommerce_store',
                'order_id': cart_id,
                'amount': amount,
                'currency': 'USD',
                'payment_method': payment_method,
                'customer_email': customer_email,
                'customer_name': customer_email.split('@')[0] if customer_email else 'Customer',
                'description': f'Choreographed saga payment for cart {cart_id}'
            }

            payment = PaymentService.create_payment(payment_data)

            # Create saga payment record
            saga_payment = SagaPayment(
                saga_id=saga_id,
                cart_id=cart_id,
                payment_id=payment.id,
                amount=amount,
                payment_method=payment_method,
                customer_email=customer_email,
                status='pending'
            )

            db.session.add(saga_payment)
            db.session.commit()

            # Process payment
            PaymentService.process_payment(payment.id)
            payment = PaymentService.get_payment(payment.id)

            if payment.status == PaymentStatus.COMPLETED:
                saga_payment.status = 'processed'
                db.session.commit()

                # Publish success event
                publish_payment_processed(saga_id, payment.id, float(amount))
            else:
                saga_payment.status = 'failed'
                db.session.commit()

                # Publish failure event
                publish_payment_failed(saga_id, 'Payment processing failed')

        except Exception as e:
            db.session.rollback()
            # Publish failure event
            publish_payment_failed(saga_id, str(e))

    def handle_payment_refund_requested(self, event):
        """Handle payment refund request for compensation"""
        data = event['data']
        saga_id = data['saga_id']
        payment_id = data['payment_id']
        reason = data.get('reason', 'Saga compensation')

        try:
            # Find saga payment
            saga_payment = SagaPayment.query.filter_by(
                payment_id=payment_id,
                saga_id=saga_id
            ).first()

            if not saga_payment:
                print(
                    f"Saga payment {payment_id} not found for saga {saga_id}")
                return

            # Process refund using existing service
            refund_data = {'reason': reason}
            refund = PaymentService.refund_payment(payment_id, refund_data)

            if refund:
                saga_payment.status = 'refunded'
                db.session.commit()

                # Publish success event
                publish_payment_refunded(
                    saga_id, payment_id, str(refund.amount))
            else:
                print(f"Failed to refund payment {payment_id}")

        except Exception as e:
            db.session.rollback()
            print(f"Error refunding payment: {str(e)}")

# Status endpoints


@saga_bp.route('/api/v1/payments/saga/<cart_id>', methods=['GET'])
def get_saga_payments_by_cart(cart_id):
    """Get saga payments for a cart"""
    payments = SagaPayment.query.filter_by(cart_id=cart_id).all()

    return jsonify({
        'cart_id': cart_id,
        'payments': [
            {
                'id': p.id,
                'saga_id': p.saga_id,
                'payment_id': p.payment_id,
                'amount': str(p.amount),
                'currency': p.currency,
                'payment_method': p.payment_method,
                'customer_email': p.customer_email,
                'status': p.status,
                'created_at': p.created_at.isoformat(),
                'updated_at': p.updated_at.isoformat()
            }
            for p in payments
        ]
    })


@saga_bp.route('/api/v1/payments/saga/<saga_id>/status', methods=['GET'])
def get_saga_payment_by_saga_id(saga_id):
    """Get saga payment by saga ID"""
    payment = SagaPayment.query.filter_by(saga_id=saga_id).first()

    if not payment:
        return jsonify({'error': 'Saga payment not found'}), 404

    return jsonify({
        'id': payment.id,
        'saga_id': payment.saga_id,
        'cart_id': payment.cart_id,
        'payment_id': payment.payment_id,
        'amount': str(payment.amount),
        'currency': payment.currency,
        'payment_method': payment.payment_method,
        'customer_email': payment.customer_email,
        'status': payment.status,
        'created_at': payment.created_at.isoformat(),
        'updated_at': payment.updated_at.isoformat()
    })

# Enhanced payment processing for saga patterns


@saga_bp.route('/api/v1/payments/saga/process', methods=['POST'])
def process_saga_payment():
    """Process payment that can work with both saga patterns"""
    try:
        data = request.json
        saga_pattern = data.get('saga_pattern', 'orchestrated')
        saga_id = data.get('saga_id')
        cart_id = data.get('cart_id')
        amount = data['amount']
        payment_method = data['payment_method']
        customer_email = data.get('customer_email')

        if saga_pattern == 'orchestrated':
            # Direct payment processing for orchestrated saga
            return create_saga_payment()

        elif saga_pattern == 'choreographed':
            # For choreographed, this would typically be triggered by events
            # But we can provide a manual trigger for testing
            if CHOREOGRAPHY_ENABLED:
                from event_bus import publish_payment_requested
                publish_payment_requested(
                    saga_id, cart_id, amount, payment_method, customer_email)

                return jsonify({
                    'message': 'Payment request published to event bus',
                    'saga_id': saga_id,
                    'cart_id': cart_id,
                    'amount': amount,
                    'pattern': 'choreographed'
                }), 202
            else:
                return jsonify({'error': 'Choreography not enabled'}), 500

        else:
            return jsonify({'error': 'Invalid saga pattern. Use "orchestrated" or "choreographed"'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Initialize saga handler
if CHOREOGRAPHY_ENABLED:
    payment_saga_handler = PaymentSagaHandler()

# Health check


@saga_bp.route('/saga/health', methods=['GET'])
def saga_health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'payment-saga',
        'choreography_enabled': CHOREOGRAPHY_ENABLED
    })
