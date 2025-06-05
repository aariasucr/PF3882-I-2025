import random
import time
from datetime import datetime, timedelta
from models import db, Payment, Transaction, PaymentStatus, PaymentMethod
from sqlalchemy.exc import SQLAlchemyError
import uuid


class PaymentService:

    @staticmethod
    def create_payment(payment_data):
        """Create a new payment record"""
        try:
            # Extract card information if present
            card_last_four = None
            card_brand = None

            if payment_data.get('card_number'):
                card_number = payment_data['card_number'].replace(
                    ' ', '').replace('-', '')
                card_last_four = card_number[-4:]
                card_brand = PaymentService._detect_card_brand(card_number)

            payment = Payment(
                merchant_id=payment_data['merchant_id'],
                order_id=payment_data['order_id'],
                amount=payment_data['amount'],
                currency=payment_data.get('currency', 'USD'),
                payment_method=PaymentMethod(payment_data['payment_method']),
                customer_email=payment_data['customer_email'],
                customer_name=payment_data['customer_name'],
                card_last_four=card_last_four,
                card_brand=card_brand,
                description=payment_data.get('description'),
                metadata=payment_data.get('metadata')
            )

            db.session.add(payment)
            db.session.commit()

            return payment

        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Database error: {str(e)}")

    @staticmethod
    def process_payment(payment_id):
        """Process a payment (simulate payment gateway processing)"""
        try:
            payment = Payment.query.get(payment_id)
            if not payment:
                raise Exception("Payment not found")

            if payment.status != PaymentStatus.PENDING:
                raise Exception(
                    f"Payment cannot be processed. Current status: {payment.status.value}")

            # Update status to processing
            payment.status = PaymentStatus.PROCESSING
            payment.updated_at = datetime.utcnow()
            db.session.commit()

            # Simulate processing time
            time.sleep(1)

            # Simulate payment processing result (90% success rate)
            success = random.random() > 0.1

            if success:
                payment.status = PaymentStatus.COMPLETED
                payment.processed_at = datetime.utcnow()

                # Create successful transaction record
                transaction = Transaction(
                    payment_id=payment.id,
                    transaction_type='charge',
                    amount=payment.amount,
                    status='completed',
                    gateway_transaction_id=f"txn_{uuid.uuid4().hex[:12]}",
                    gateway_response={
                        'status': 'success',
                        'authorization_code': f"auth_{uuid.uuid4().hex[:8]}",
                        'processor_response': 'Approved'
                    }
                )
            else:
                payment.status = PaymentStatus.FAILED

                # Create failed transaction record
                transaction = Transaction(
                    payment_id=payment.id,
                    transaction_type='charge',
                    amount=payment.amount,
                    status='failed',
                    gateway_response={
                        'status': 'failed',
                        'error_code': random.choice(['insufficient_funds', 'card_declined', 'expired_card']),
                        'processor_response': 'Declined'
                    }
                )

            payment.updated_at = datetime.utcnow()
            db.session.add(transaction)
            db.session.commit()

            return payment

        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Database error: {str(e)}")

    @staticmethod
    def get_payment(payment_id):
        """Retrieve payment by ID"""
        return Payment.query.get(payment_id)

    @staticmethod
    def get_payments_by_merchant(merchant_id, limit=100, offset=0):
        """Get payments for a specific merchant"""
        return Payment.query.filter_by(merchant_id=merchant_id)\
            .order_by(Payment.created_at.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()

    @staticmethod
    def refund_payment(payment_id, refund_amount=None, reason=None):
        """Process a refund for a payment"""
        try:
            payment = Payment.query.get(payment_id)
            if not payment:
                raise Exception("Payment not found")

            if payment.status != PaymentStatus.COMPLETED:
                raise Exception(
                    f"Cannot refund payment with status: {payment.status.value}")

            # If no amount specified, refund the full amount
            if refund_amount is None:
                refund_amount = payment.amount

            if refund_amount > payment.amount:
                raise Exception(
                    "Refund amount cannot exceed original payment amount")

            # Check if this is a full refund
            if refund_amount == payment.amount:
                payment.status = PaymentStatus.REFUNDED

            # Create refund transaction
            transaction = Transaction(
                payment_id=payment.id,
                transaction_type='refund',
                amount=refund_amount,
                status='completed',
                gateway_transaction_id=f"ref_{uuid.uuid4().hex[:12]}",
                gateway_response={
                    'status': 'success',
                    'refund_reason': reason or 'Customer request',
                    'processor_response': 'Refund processed'
                }
            )

            payment.updated_at = datetime.utcnow()
            db.session.add(transaction)
            db.session.commit()

            return transaction

        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Database error: {str(e)}")

    @staticmethod
    def _detect_card_brand(card_number):
        """Simple card brand detection"""
        if card_number.startswith('4'):
            return 'Visa'
        elif card_number.startswith(('51', '52', '53', '54', '55')):
            return 'Mastercard'
        elif card_number.startswith(('34', '37')):
            return 'American Express'
        elif card_number.startswith('6'):
            return 'Discover'
        else:
            return 'Unknown'


class WebhookService:

    @staticmethod
    def send_webhook(merchant_webhook_url, payment_data):
        """Send webhook notification (simplified implementation)"""
        # In a real implementation, this would send HTTP POST request
        # to the merchant's webhook URL with payment status updates
        pass
