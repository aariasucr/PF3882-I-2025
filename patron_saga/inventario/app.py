from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flasgger import Swagger, swag_from
from marshmallow import Schema, fields, ValidationError, validate
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/saga')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Swagger configuration
app.config['SWAGGER'] = {
    'title': 'Product Inventory API',
    'uiversion': 3,
    'description': 'A REST API for managing product inventory',
    'version': '1.0.0'
}
swagger = Swagger(app)

# Product Model


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    category = db.Column(db.String(50))
    sku = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(
    ), onupdate=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': str(self.price),
            'quantity': self.quantity,
            'category': self.category,
            'sku': self.sku,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Marshmallow Schemas


class ProductSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(allow_none=True)
    price = fields.Decimal(required=True, places=2)
    quantity = fields.Int(required=True, validate=validate.Range(min=0))
    category = fields.Str(allow_none=True, validate=validate.Length(max=50))
    sku = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class ProductUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=100))
    description = fields.Str(allow_none=True)
    price = fields.Decimal(places=2)
    quantity = fields.Int(validate=validate.Range(min=0))
    category = fields.Str(allow_none=True, validate=validate.Length(max=50))
    sku = fields.Str(validate=validate.Length(min=1, max=50))


product_schema = ProductSchema()
products_schema = ProductSchema(many=True)
product_update_schema = ProductUpdateSchema()

# API Routes


@app.route('/api/products', methods=['GET'])
@swag_from({
    'tags': ['Products'],
    'summary': 'Get all products',
    'description': 'Retrieve a list of all products in the inventory',
    'parameters': [
        {
            'name': 'page',
            'in': 'query',
            'type': 'integer',
            'default': 1,
            'description': 'Page number for pagination'
        },
        {
            'name': 'per_page',
            'in': 'query',
            'type': 'integer',
            'default': 10,
            'description': 'Number of items per page'
        },
        {
            'name': 'category',
            'in': 'query',
            'type': 'string',
            'description': 'Filter by category'
        }
    ],
    'responses': {
        200: {
            'description': 'List of products',
            'schema': {
                'type': 'object',
                'properties': {
                    'products': {
                        'type': 'array',
                        'items': {'$ref': '#/definitions/Product'}
                    },
                    'total': {'type': 'integer'},
                    'page': {'type': 'integer'},
                    'per_page': {'type': 'integer'},
                    'pages': {'type': 'integer'}
                }
            }
        }
    }
})
def get_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    category = request.args.get('category')

    query = Product.query

    if category:
        query = query.filter(Product.category.ilike(f'%{category}%'))

    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    products = pagination.items

    return jsonify({
        'products': products_schema.dump(products),
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@app.route('/api/products/<int:product_id>', methods=['GET'])
@swag_from({
    'tags': ['Products'],
    'summary': 'Get a product by ID',
    'description': 'Retrieve a specific product by its ID',
    'parameters': [
        {
            'name': 'product_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'Product ID'
        }
    ],
    'responses': {
        200: {
            'description': 'Product details',
            'schema': {'$ref': '#/definitions/Product'}
        },
        404: {
            'description': 'Product not found'
        }
    }
})
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product_schema.dump(product))


@app.route('/api/products', methods=['POST'])
@swag_from({
    'tags': ['Products'],
    'summary': 'Create a new product',
    'description': 'Add a new product to the inventory',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {'$ref': '#/definitions/ProductInput'}
        }
    ],
    'responses': {
        201: {
            'description': 'Product created successfully',
            'schema': {'$ref': '#/definitions/Product'}
        },
        400: {
            'description': 'Validation error'
        },
        409: {
            'description': 'SKU already exists'
        }
    }
})
def create_product():
    try:
        json_data = request.get_json()
        if not json_data:
            return jsonify({'error': 'No input data provided'}), 400

        # Validate input data
        data = product_schema.load(json_data)

        # Check if SKU already exists
        if Product.query.filter_by(sku=data['sku']).first():
            return jsonify({'error': 'SKU already exists'}), 409

        # Create new product
        product = Product(**data)
        db.session.add(product)
        db.session.commit()

        return jsonify(product_schema.dump(product)), 201

    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/<int:product_id>', methods=['PUT'])
@swag_from({
    'tags': ['Products'],
    'summary': 'Update a product',
    'description': 'Update an existing product',
    'parameters': [
        {
            'name': 'product_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'Product ID'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {'$ref': '#/definitions/ProductUpdate'}
        }
    ],
    'responses': {
        200: {
            'description': 'Product updated successfully',
            'schema': {'$ref': '#/definitions/Product'}
        },
        400: {
            'description': 'Validation error'
        },
        404: {
            'description': 'Product not found'
        },
        409: {
            'description': 'SKU already exists'
        }
    }
})
def update_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        json_data = request.get_json()

        if not json_data:
            return jsonify({'error': 'No input data provided'}), 400

        # Validate input data
        data = product_update_schema.load(json_data)

        # Check if SKU already exists (if updating SKU)
        if 'sku' in data and data['sku'] != product.sku:
            if Product.query.filter_by(sku=data['sku']).first():
                return jsonify({'error': 'SKU already exists'}), 409

        # Update product fields
        for key, value in data.items():
            setattr(product, key, value)

        db.session.commit()

        return jsonify(product_schema.dump(product))

    except ValidationError as err:
        return jsonify({'errors': err.messages}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Products'],
    'summary': 'Delete a product',
    'description': 'Remove a product from the inventory',
    'parameters': [
        {
            'name': 'product_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'Product ID'
        }
    ],
    'responses': {
        204: {
            'description': 'Product deleted successfully'
        },
        404: {
            'description': 'Product not found'
        }
    }
})
def delete_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        return '', 204

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/search', methods=['GET'])
@swag_from({
    'tags': ['Products'],
    'summary': 'Search products',
    'description': 'Search products by name or SKU',
    'parameters': [
        {
            'name': 'q',
            'in': 'query',
            'type': 'string',
            'required': True,
            'description': 'Search query'
        }
    ],
    'responses': {
        200: {
            'description': 'Search results',
            'schema': {
                'type': 'array',
                'items': {'$ref': '#/definitions/Product'}
            }
        }
    }
})
def search_products():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    products = Product.query.filter(
        db.or_(
            Product.name.ilike(f'%{query}%'),
            Product.sku.ilike(f'%{query}%')
        )
    ).all()

    return jsonify(products_schema.dump(products))

# Health check endpoint


@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Product Inventory API is running'})

# Swagger model definitions


@app.route('/swagger-definitions')
def swagger_definitions():
    return jsonify({
        'definitions': {
            'Product': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'name': {'type': 'string'},
                    'description': {'type': 'string'},
                    'price': {'type': 'string'},
                    'quantity': {'type': 'integer'},
                    'category': {'type': 'string'},
                    'sku': {'type': 'string'},
                    'created_at': {'type': 'string'},
                    'updated_at': {'type': 'string'}
                }
            },
            'ProductInput': {
                'type': 'object',
                'required': ['name', 'price', 'quantity', 'sku'],
                'properties': {
                    'name': {'type': 'string'},
                    'description': {'type': 'string'},
                    'price': {'type': 'number'},
                    'quantity': {'type': 'integer'},
                    'category': {'type': 'string'},
                    'sku': {'type': 'string'}
                }
            },
            'ProductUpdate': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'description': {'type': 'string'},
                    'price': {'type': 'number'},
                    'quantity': {'type': 'integer'},
                    'category': {'type': 'string'},
                    'sku': {'type': 'string'}
                }
            }
        }
    })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=3001)
