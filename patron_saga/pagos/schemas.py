from marshmallow import Schema, fields, validate, ValidationError, post_load
from models import PaymentStatus, PaymentMethod
import re


class PaymentRequestSchema(Schema):
    merchant_id = fields.Str(
        required=True, validate=validate.Length(min=1, max=100))
    order_id = fields.Str(
        required=True, validate=validate.Length(min=1, max=100))
    amount = fields.Decimal(required=True, validate=validate.Range(
        min=0.01, max=100000.00), places=2)
    currency = fields.Str(missing='USD', validate=validate.Length(equal=3))
    payment_method = fields.Str(required=True, validate=validate.OneOf(
        [method.value for method in PaymentMethod]))

    # Customer information
    customer_email = fields.Email(required=True)
    customer_name = fields.Str(
        required=True, validate=validate.Length(min=1, max=255))

    # Payment details (for card payments)
    card_number = fields.Str(validate=validate.Length(min=13, max=19))
    card_expiry_month = fields.Int(validate=validate.Range(min=1, max=12))
    card_expiry_year = fields.Int(validate=validate.Range(min=2024, max=2050))
    card_cvv = fields.Str(validate=validate.Length(min=3, max=4))
    card_holder_name = fields.Str(validate=validate.Length(max=255))

    # Optional fields
    description = fields.Str(validate=validate.Length(max=500))
    metadata = fields.Dict()

    @post_load
    def validate_card_details(self, data, **kwargs):
        if data.get('payment_method') in ['credit_card', 'debit_card']:
            required_card_fields = [
                'card_number', 'card_expiry_month', 'card_expiry_year', 'card_cvv']
            missing_fields = [
                field for field in required_card_fields if not data.get(field)]
            if missing_fields:
                raise ValidationError(
                    f"Missing required card fields: {', '.join(missing_fields)}")

            # Validate card number (basic Luhn algorithm)
            card_number = data.get('card_number', '').replace(
                ' ', '').replace('-', '')
            if not re.match(r'^\d{13,19}$', card_number):
                raise ValidationError("Invalid card number format")

        return data


class PaymentResponseSchema(Schema):
    id = fields.Str()
    merchant_id = fields.Str()
    order_id = fields.Str()
    amount = fields.Decimal(places=2)
    currency = fields.Str()
    status = fields.Str()
    payment_method = fields.Str()
    customer_email = fields.Email()
    customer_name = fields.Str()
    card_last_four = fields.Str()
    card_brand = fields.Str()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    processed_at = fields.DateTime()
    description = fields.Str()
    metadata = fields.Dict()


class RefundRequestSchema(Schema):
    amount = fields.Decimal(validate=validate.Range(min=0.01), places=2)
    reason = fields.Str(validate=validate.Length(max=500))


class TransactionSchema(Schema):
    id = fields.Str()
    payment_id = fields.Str()
    transaction_type = fields.Str()
    amount = fields.Decimal(places=2)
    status = fields.Str()
    gateway_transaction_id = fields.Str()
    created_at = fields.DateTime()


class ErrorResponseSchema(Schema):
    error = fields.Str(required=True)
    message = fields.Str(required=True)
    details = fields.Dict()


class SuccessResponseSchema(Schema):
    success = fields.Bool(default=True)
    message = fields.Str()
    data = fields.Dict()
