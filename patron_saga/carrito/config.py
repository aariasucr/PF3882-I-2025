import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL') or 'postgresql://postgres:postgres@localhost:5432/saga'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # External services
    INVENTARIO_SERVICE_URL = os.environ.get(
        'INVENTARIO_SERVICE_URL') or 'http://localhost:3001'
    PAGOS_SERVICE_URL = os.environ.get(
        'PAGOS_SERVICE_URL') or 'http://localhost:3002'


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
