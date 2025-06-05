from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
from enum import Enum

db = SQLAlchemy()


class PaymentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    merchant_id = db.Column(db.String(100), nullable=False)
    order_id = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    status = db.Column(db.Enum(PaymentStatus),
                       default=PaymentStatus.PENDING, nullable=False)
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=False)

    # Customer information
    customer_email = db.Column(db.String(255), nullable=False)
    customer_name = db.Column(db.String(255), nullable=False)

    # Payment details
    card_last_four = db.Column(db.String(4))
    card_brand = db.Column(db.String(50))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = db.Column(db.DateTime)

    # Metadata - renamed to avoid SQLAlchemy conflict
    description = db.Column(db.Text)
    payment_metadata = db.Column(db.JSON)

    # Relationships
    transactions = db.relationship('Transaction', backref='payment', lazy=True)


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    payment_id = db.Column(db.String(36), db.ForeignKey(
        'payments.id'), nullable=False)
    transaction_type = db.Column(
        db.String(50), nullable=False)  # charge, refund, void
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    gateway_transaction_id = db.Column(db.String(255))
    gateway_response = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Merchant(db.Model):
    __tablename__ = 'merchants'

    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    merchant_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    api_key = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Settings
    webhook_url = db.Column(db.String(500))
    allowed_currencies = db.Column(db.JSON, default=['USD'])
    max_transaction_amount = db.Column(db.Numeric(10, 2), default=10000.00)
