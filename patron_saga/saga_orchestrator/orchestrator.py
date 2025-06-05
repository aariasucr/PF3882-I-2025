from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from enum import Enum
import uuid
import requests
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional
import pika
import json
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/saga')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Enums


class SagaStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"

# Models


class SagaTransaction(db.Model):
    __tablename__ = 'saga_transactions'

    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    cart_id = db.Column(db.String(36), nullable=False)
    user_id = db.Column(db.String(100), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    billing_address = db.Column(db.JSON, nullable=False)
    status = db.Column(db.Enum(SagaStatus), default=SagaStatus.PENDING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    steps = db.relationship('SagaStep', backref='saga',
                            lazy=True, cascade='all, delete-orphan')


class SagaStep(db.Model):
    __tablename__ = 'saga_steps'

    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    saga_id = db.Column(db.String(36), db.ForeignKey(
        'saga_transactions.id'), nullable=False)
    step_name = db.Column(db.String(100), nullable=False)
    step_order = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(StepStatus), default=StepStatus.PENDING)
    service_url = db.Column(db.String(200), nullable=False)
    request_data = db.Column(db.JSON)
    response_data = db.Column(db.JSON)
    compensation_url = db.Column(db.String(200))
    compensation_data = db.Column(db.JSON)
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Saga Orchestrator Class


class SagaOrchestrator:
    def __init__(self):
        self.services = {
            'carrito': os.getenv('CARRITO_SERVICE_URL', 'http://localhost:3000'),
            'inventario': os.getenv('INVENTARIO_SERVICE_URL', 'http://localhost:3001'),
            'pagos': os.getenv('PAGOS_SERVICE_URL', 'http://localhost:3002')
        }

    def create_checkout_saga(self, cart_id: str, user_id: str, payment_method: str, billing_address: dict) -> str:
        """Create a new checkout saga transaction"""

        # Get cart details
        cart_response = requests.get(
            f"{self.services['carrito']}/carts/{cart_id}")
        if cart_response.status_code != 200:
            raise Exception("Cart not found")

        cart_data = cart_response.json()
        total_amount = sum(
            float(item['unit_price']) * item['quantity'] for item in cart_data['items'])

        # Create saga transaction
        saga = SagaTransaction(
            cart_id=cart_id,
            user_id=user_id,
            total_amount=total_amount,
            payment_method=payment_method,
            billing_address=billing_address,
            status=SagaStatus.PENDING
        )

        # Define saga steps
        steps = [
            {
                'step_name': 'reserve_inventory',
                'step_order': 1,
                'service_url': f"{self.services['inventario']}/api/products/reserve",
                'request_data': {
                    'cart_id': cart_id,
                    'items': cart_data['items']
                },
                'compensation_url': f"{self.services['inventario']}/api/products/unreserve",
                'compensation_data': {'cart_id': cart_id}
            },
            {
                'step_name': 'process_payment',
                'step_order': 2,
                'service_url': f"{self.services['pagos']}/api/v1/payments",
                'request_data': {
                    'merchant_id': 'ecommerce_store',
                    'order_id': cart_id,
                    'amount': float(total_amount),
                    'currency': 'USD',
                    'payment_method': payment_method,
                    'customer_email': f"{user_id}@example.com",
                    'customer_name': user_id,
                    'description': f'Purchase for cart {cart_id}'
                },
                'compensation_url': f"{self.services['pagos']}/api/v1/payments/{{payment_id}}/refund",
                'compensation_data': {'reason': 'Saga compensation'}
            },
            {
                'step_name': 'create_order',
                'step_order': 3,
                'service_url': f"{self.services['carrito']}/orders",
                'request_data': {
                    'cart_id': cart_id,
                    'user_id': user_id,
                    'total_amount': float(total_amount),
                    'payment_method': payment_method
                },
                'compensation_url': f"{self.services['carrito']}/orders/{{order_id}}/cancel",
                'compensation_data': {'reason': 'Saga compensation'}
            },
            {
                'step_name': 'update_inventory',
                'step_order': 4,
                'service_url': f"{self.services['inventario']}/api/products/commit",
                'request_data': {
                    'cart_id': cart_id,
                    'items': cart_data['items']
                },
                'compensation_url': f"{self.services['inventario']}/api/products/restore",
                'compensation_data': {'cart_id': cart_id}
            }
        ]

        # Create saga steps
        for step_data in steps:
            step = SagaStep(
                saga_id=saga.id,
                **step_data
            )
            saga.steps.append(step)

        db.session.add(saga)
        db.session.commit()

        # Start saga execution asynchronously
        threading.Thread(target=self.execute_saga, args=(saga.id,)).start()

        return saga.id

    def execute_saga(self, saga_id: str):
        """Execute saga steps in sequence"""
        with app.app_context():
            saga = SagaTransaction.query.get(saga_id)
            if not saga:
                return

            saga.status = SagaStatus.RUNNING
            db.session.commit()

            try:
                # Execute steps in order
                for step in sorted(saga.steps, key=lambda x: x.step_order):
                    if not self.execute_step(step):
                        # Step failed, start compensation
                        self.compensate_saga(saga_id)
                        return

                # All steps completed successfully
                saga.status = SagaStatus.COMPLETED
                db.session.commit()

            except Exception as e:
                print(f"Saga execution failed: {str(e)}")
                self.compensate_saga(saga_id)

    def execute_step(self, step: SagaStep) -> bool:
        """Execute a single saga step with retry logic"""
        step.status = StepStatus.RUNNING
        db.session.commit()

        for attempt in range(step.max_retries + 1):
            try:
                response = requests.post(
                    step.service_url,
                    json=step.request_data,
                    timeout=30
                )

                if response.status_code in [200, 201]:
                    step.status = StepStatus.COMPLETED
                    step.response_data = response.json()
                    db.session.commit()
                    return True

                step.retry_count = attempt + 1
                if attempt < step.max_retries:
                    time.sleep(2 ** attempt)  # Exponential backoff

            except Exception as e:
                print(
                    f"Step {step.step_name} attempt {attempt + 1} failed: {str(e)}")
                step.retry_count = attempt + 1
                if attempt < step.max_retries:
                    time.sleep(2 ** attempt)

        step.status = StepStatus.FAILED
        db.session.commit()
        return False

    def compensate_saga(self, saga_id: str):
        """Execute compensation for all completed steps"""
        saga = SagaTransaction.query.get(saga_id)
        if not saga:
            return

        saga.status = SagaStatus.COMPENSATING
        db.session.commit()

        # Compensate completed steps in reverse order
        completed_steps = [
            s for s in saga.steps if s.status == StepStatus.COMPLETED]
        completed_steps.sort(key=lambda x: x.step_order, reverse=True)

        for step in completed_steps:
            self.compensate_step(step)

        saga.status = SagaStatus.COMPENSATED
        db.session.commit()

    def compensate_step(self, step: SagaStep):
        """Execute compensation for a single step"""
        if not step.compensation_url:
            step.status = StepStatus.COMPENSATED
            db.session.commit()
            return

        compensation_url = step.compensation_url
        compensation_data = step.compensation_data or {}

        # Replace placeholders with actual values from response
        if step.response_data:
            for key, value in step.response_data.items():
                placeholder = f"{{{key}}}"
                compensation_url = compensation_url.replace(
                    placeholder, str(value))

        try:
            response = requests.post(
                compensation_url,
                json=compensation_data,
                timeout=30
            )

            if response.status_code in [200, 201, 204]:
                step.status = StepStatus.COMPENSATED
            else:
                print(
                    f"Compensation failed for step {step.step_name}: {response.text}")

        except Exception as e:
            print(f"Compensation error for step {step.step_name}: {str(e)}")

        db.session.commit()


# Initialize orchestrator
orchestrator = SagaOrchestrator()

# API Routes


@app.route('/saga/checkout', methods=['POST'])
def initiate_checkout_saga():
    """Initiate a checkout saga transaction"""
    try:
        data = request.json
        saga_id = orchestrator.create_checkout_saga(
            cart_id=data['cart_id'],
            user_id=data['user_id'],
            payment_method=data['payment_method'],
            billing_address=data['billing_address']
        )

        return jsonify({
            'saga_id': saga_id,
            'status': 'initiated',
            'message': 'Checkout saga started'
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/saga/<saga_id>', methods=['GET'])
def get_saga_status(saga_id):
    """Get saga transaction status"""
    saga = SagaTransaction.query.get_or_404(saga_id)

    steps_status = []
    for step in sorted(saga.steps, key=lambda x: x.step_order):
        steps_status.append({
            'step_name': step.step_name,
            'status': step.status.value,
            'retry_count': step.retry_count,
            'response_data': step.response_data
        })

    return jsonify({
        'saga_id': saga.id,
        'status': saga.status.value,
        'cart_id': saga.cart_id,
        'user_id': saga.user_id,
        'total_amount': str(saga.total_amount),
        'steps': steps_status,
        'created_at': saga.created_at.isoformat(),
        'updated_at': saga.updated_at.isoformat()
    })


@app.route('/saga/<saga_id>/compensate', methods=['POST'])
def manual_compensate_saga(saga_id):
    """Manually trigger saga compensation"""
    try:
        orchestrator.compensate_saga(saga_id)
        return jsonify({'message': 'Compensation initiated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'saga-orchestrator'})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=3003, debug=True)
