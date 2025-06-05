import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'payment-gateway-secret-key'

    # Database configuration with fallback to SQLite
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Fallback to SQLite for development/testing
        SQLALCHEMY_DATABASE_URI = 'sqlite:///payment_gateway.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Payment Gateway Configuration
    PAYMENT_TIMEOUT = 300  # 5 minutes
    MAX_PAYMENT_AMOUNT = 100000.00  # $100,000
    MIN_PAYMENT_AMOUNT = 0.01  # $0.01

    # Swagger Configuration
    SWAGGER = {
        'title': 'Payment Gateway API',
        'uiversion': 3,
        'version': '1.0.0',
        'description': 'A REST API that emulates a payment gateway for ecommerce sites',
        'headers': [],
        'specs': [
            {
                'endpoint': 'apispec_1',
                'route': '/apispec_1.json',
                'rule_filter': lambda rule: True,  # all in
                'model_filter': lambda tag: True,  # all in
            }
        ]
    }
