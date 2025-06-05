from flask import Flask, request, jsonify
from flask_cors import CORS
from flasgger import Swagger, swag_from
from marshmallow import ValidationError
import threading
import time

from config import Config
from models import db, Payment, Transaction, PaymentStatus
from schemas import (
    PaymentRequestSchema, PaymentResponseSchema, RefundRequestSchema,
    TransactionSchema, ErrorResponseSchema, SuccessResponseSchema
)
from services import PaymentService


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    CORS(app)
    Swagger(app, config=app.config['SWAGGER'])

    # Create tables
    with app.app_context():
        db.create_all()

    return app


app = create_app()

# Schemas
payment_request_schema = PaymentRequestSchema()
payment_response_schema = PaymentResponseSchema()
refund_request_schema = RefundRequestSchema()
transaction_schema = TransactionSchema()
error_response_schema = ErrorResponseSchema()
success_response_schema = SuccessResponseSchema()


@app.route('/api/v1/payments', methods=['POST'])
@swag_from({
    'tags': ['Payments'],
    'summary': 'Create a new payment',
    'description': 'Initiates a new payment transaction',
    'parameters': [{
        'name': 'payment',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'properties': {
                'merchant_id': {'type': 'string', 'example': 'merchant_123'},
                'order_id': {'type': 'string', 'example': 'order_456'},
                'amount': {'type': 'number', 'example': 99.99},
                'currency': {'type': 'string', 'example': 'USD'},
                'payment_method': {'type': 'string', 'enum': ['credit_card', 'debit_card', 'paypal', 'bank_transfer']},
                'customer_email': {'type': 'string', 'example': 'customer@example.com'},
                'customer_name': {'type': 'string', 'example': 'John Doe'},
                'card_number': {'type': 'string', 'example': '4111111111111111'},
                'card_expiry_month': {'type': 'integer', 'example': 12},
                'card_expiry_year': {'type': 'integer', 'example': 2025},
                'card_cvv': {'type': 'string', 'example': '123'},
                'description': {'type': 'string', 'example': 'Purchase from online store'}
            },
            'required': ['merchant_id', 'order_id', 'amount', 'payment_method', 'customer_email', 'customer_name']
        }
    }],
    'responses': {
        '201': {
            'description': 'Payment created successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                    'status': {'type': 'string'},
                    'amount': {'type': 'number'},
                    'currency': {'type': 'string'}
                }
            }
        },
        '400': {
            'description': 'Validation error',
            'schema': error_response_schema
        }
    }
})
def create_payment():
    try:
        # Validate request data
        payment_data = payment_request_schema.load(request.json)

        # Create payment
        payment = PaymentService.create_payment(payment_data)

        # Start async processing
        thread = threading.Thread(
            target=process_payment_async, args=(payment.id,))
        thread.start()

        response_data = payment_response_schema.dump(payment)
        return jsonify(response_data), 201

    except ValidationError as e:
        error_response = error_response_schema.dump({
            'error': 'Validation Error',
            'message': 'Invalid request data',
            'details': e.messages
        })
        return jsonify(error_response), 400

    except Exception as e:
        error_response = error_response_schema.dump({
            'error': 'Internal Server Error',
            'message': str(e)
        })
        return jsonify(error_response), 500


def process_payment_async(payment_id):
    """Process payment asynchronously"""
    with app.app_context():
        try:
            PaymentService.process_payment(payment_id)
        except Exception as e:
            print(f"Error processing payment {payment_id}: {str(e)}")


@app.route('/api/v1/payments/<payment_id>', methods=['GET'])
@swag_from({
    'tags': ['Payments'],
    'summary': 'Get payment details',
    'description': 'Retrieve payment information by ID',
    'parameters': [{
        'name': 'payment_id',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': 'Payment ID'
    }],
    'responses': {
        '200': {
            'description': 'Payment details',
            'schema': payment_response_schema
        },
        '404': {
            'description': 'Payment not found',
            'schema': error_response_schema
        }
    }
})
def get_payment(payment_id):
    try:
        payment = PaymentService.get_payment(payment_id)

        if not payment:
            error_response = error_response_schema.dump({
                'error': 'Not Found',
                'message': 'Payment not found'
            })
            return jsonify(error_response), 404

        response_data = payment_response_schema.dump(payment)
        return jsonify(response_data), 200

    except Exception as e:
        error_response = error_response_schema.dump({
            'error': 'Internal Server Error',
            'message': str(e)
        })
        return jsonify(error_response), 500


@app.route('/api/v1/payments/<payment_id>/refund', methods=['POST'])
@swag_from({
    'tags': ['Payments'],
    'summary': 'Refund a payment',
    'description': 'Process a full or partial refund for a payment',
    'parameters': [
        {
            'name': 'payment_id',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Payment ID'
        },
        {
            'name': 'refund',
            'in': 'body',
            'schema': {
                'type': 'object',
                'properties': {
                    'amount': {'type': 'number', 'description': 'Refund amount (optional, defaults to full amount)'},
                    'reason': {'type': 'string', 'description': 'Reason for refund'}
                }
            }
        }
    ],
    'responses': {
        '200': {
            'description': 'Refund processed successfully',
            'schema': transaction_schema
        },
        '400': {
            'description': 'Validation error',
            'schema': error_response_schema
        },
        '404': {
            'description': 'Payment not found',
            'schema': error_response_schema
        }
    }
})
def refund_payment(payment_id):
    try:
        # Validate request data if present
        refund_data = {}
        if request.json:
            refund_data = refund_request_schema.load(request.json)

        # Process refund
        transaction = PaymentService.refund_payment(
            payment_id,
            refund_data.get('amount'),
            refund_data.get('reason')
        )

        response_data = transaction_schema.dump(transaction)
        return jsonify(response_data), 200

    except ValidationError as e:
        error_response = error_response_schema.dump({
            'error': 'Validation Error',
            'message': 'Invalid request data',
            'details': e.messages
        })
        return jsonify(error_response), 400

    except Exception as e:
        error_response = error_response_schema.dump({
            'error': 'Bad Request',
            'message': str(e)
        })
        return jsonify(error_response), 400


@app.route('/api/v1/payments', methods=['GET'])
@swag_from({
    'tags': ['Payments'],
    'summary': 'List payments',
    'description': 'Get a list of payments for a merchant',
    'parameters': [
        {
            'name': 'merchant_id',
            'in': 'query',
            'type': 'string',
            'required': True,
            'description': 'Merchant ID'
        },
        {
            'name': 'limit',
            'in': 'query',
            'type': 'integer',
            'default': 100,
            'description': 'Number of results to return'
        },
        {
            'name': 'offset',
            'in': 'query',
            'type': 'integer',
            'default': 0,
            'description': 'Number of results to skip'
        }
    ],
    'responses': {
        '200': {
            'description': 'List of payments',
            'schema': {
                'type': 'object',
                'properties': {
                    'payments': {
                        'type': 'array',
                        'items': payment_response_schema
                    },
                    'total': {'type': 'integer'}
                }
            }
        },
        '400': {
            'description': 'Bad request',
            'schema': error_response_schema
        }
    }
})
def list_payments():
    try:
        merchant_id = request.args.get('merchant_id')
        if not merchant_id:
            error_response = error_response_schema.dump({
                'error': 'Bad Request',
                'message': 'merchant_id parameter is required'
            })
            return jsonify(error_response), 400

        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))

        payments = PaymentService.get_payments_by_merchant(
            merchant_id, limit, offset)
        payments_data = payment_response_schema.dump(payments, many=True)

        response = {
            'payments': payments_data,
            'total': len(payments_data)
        }

        return jsonify(response), 200

    except Exception as e:
        error_response = error_response_schema.dump({
            'error': 'Internal Server Error',
            'message': str(e)
        })
        return jsonify(error_response), 500


@app.route('/api/v1/payments/<payment_id>/transactions', methods=['GET'])
@swag_from({
    'tags': ['Payments'],
    'summary': 'Get payment transactions',
    'description': 'Get all transactions for a specific payment',
    'parameters': [{
        'name': 'payment_id',
        'in': 'path',
        'type': 'string',
        'required': True,
        'description': 'Payment ID'
    }],
    'responses': {
        '200': {
            'description': 'List of transactions',
            'schema': {
                'type': 'array',
                'items': transaction_schema
            }
        },
        '404': {
            'description': 'Payment not found',
            'schema': error_response_schema
        }
    }
})
def get_payment_transactions(payment_id):
    try:
        payment = PaymentService.get_payment(payment_id)

        if not payment:
            error_response = error_response_schema.dump({
                'error': 'Not Found',
                'message': 'Payment not found'
            })
            return jsonify(error_response), 404

        transactions_data = transaction_schema.dump(
            payment.transactions, many=True)
        return jsonify(transactions_data), 200

    except Exception as e:
        error_response = error_response_schema.dump({
            'error': 'Internal Server Error',
            'message': str(e)
        })
        return jsonify(error_response), 500


@app.route('/api/v1/health', methods=['GET'])
@swag_from({
    'tags': ['Health'],
    'summary': 'Health check',
    'description': 'Check if the API is running',
    'responses': {
        '200': {
            'description': 'API is healthy',
            'schema': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string'},
                    'timestamp': {'type': 'string'}
                }
            }
        }
    }
})
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time()
    }), 200


@app.errorhandler(404)
def not_found(error):
    error_response = error_response_schema.dump({
        'error': 'Not Found',
        'message': 'The requested resource was not found'
    })
    return jsonify(error_response), 404


@app.errorhandler(500)
def internal_error(error):
    error_response = error_response_schema.dump({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    })
    return jsonify(error_response), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3002)
