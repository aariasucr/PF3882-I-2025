# Product Inventory REST API

A Flask-based REST API for managing product inventory with PostgreSQL database, Marshmallow validation, and Swagger documentation.

## Features

- **CRUD Operations**: Create, Read, Update, Delete products
- **Search**: Search products by name or SKU
- **Pagination**: Paginated product listing
- **Filtering**: Filter products by category
- **Validation**: Input validation using Marshmallow
- **Documentation**: Interactive API documentation with Swagger/Flasgger
- **Database**: PostgreSQL with SQLAlchemy ORM

## API Endpoints

### Products

- `GET /api/products` - Get all products (with pagination and filtering)
- `GET /api/products/{id}` - Get product by ID
- `POST /api/products` - Create new product
- `PUT /api/products/{id}` - Update product
- `DELETE /api/products/{id}` - Delete product
- `GET /api/products/search?q={query}` - Search products

### Documentation

- `GET /apidocs` - Swagger UI documentation
- `GET /health` - Health check endpoint

## Product Schema

```json
{
  "id": 1,
  "name": "Product Name",
  "description": "Product description",
  "price": "29.99",
  "quantity": 100,
  "category": "Electronics",
  "sku": "PROD-001",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

## Requirements

- Python 3.8+
- PostgreSQL 12+
- Virtual environment (recommended)

## Setup Instructions

### 1. Database Setup

First, ensure PostgreSQL is running and create the database:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE saga;

# Exit PostgreSQL
\q
```

### 2. Virtual Environment and Dependencies

```bash
# Activate your virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the project root:

```env
FLASK_APP=app.py
FLASK_ENV=development
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/saga
SECRET_KEY=your-secret-key-change-this-in-production
```

### 4. Database Migration

```bash
# Initialize migration repository
flask db init

# Create initial migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

### 5. Run the Application

```bash
python app.py
```

The API will be available at:

- **Base URL**: http://localhost:5000
- **Swagger Documentation**: http://localhost:5000/apidocs
- **Health Check**: http://localhost:5000/health

## Usage Examples

### Create a Product

```bash
curl -X POST http://localhost:5000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop",
    "description": "Gaming laptop with high performance",
    "price": 1299.99,
    "quantity": 50,
    "category": "Electronics",
    "sku": "LAP-001"
  }'
```

### Get All Products

```bash
curl http://localhost:5000/api/products
```

### Get Products with Pagination

```bash
curl "http://localhost:5000/api/products?page=1&per_page=5"
```

### Filter by Category

```bash
curl "http://localhost:5000/api/products?category=Electronics"
```

### Search Products

```bash
curl "http://localhost:5000/api/products/search?q=laptop"
```

### Update a Product

```bash
curl -X PUT http://localhost:5000/api/products/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Laptop",
    "price": 1199.99,
    "quantity": 45
  }'
```

### Delete a Product

```bash
curl -X DELETE http://localhost:5000/api/products/1
```

## Project Structure

```
├── app.py              # Main Flask application
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── README.md          # Project documentation
├── migrations/        # Database migration files (after flask db init)
└── .venv/            # Virtual environment
```

## Validation Rules

- **name**: Required, 1-100 characters
- **price**: Required, decimal with 2 places
- **quantity**: Required, non-negative integer
- **sku**: Required, unique, 1-50 characters
- **category**: Optional, max 50 characters
- **description**: Optional, text field

## Error Handling

The API returns appropriate HTTP status codes:

- `200` - Success
- `201` - Created
- `204` - No Content (successful deletion)
- `400` - Bad Request (validation errors)
- `404` - Not Found
- `409` - Conflict (duplicate SKU)
- `500` - Internal Server Error

Error responses include descriptive messages:

```json
{
  "error": "SKU already exists"
}
```

## Development

### Adding New Features

1. Add new routes in `app.py`
2. Update Marshmallow schemas for validation
3. Add Swagger documentation using `@swag_from`
4. Create database migrations if schema changes are needed

### Running Tests

You can add tests using pytest:

```bash
pip install pytest
pytest
```

## Production Deployment

For production deployment:

1. Set `FLASK_ENV=production`
2. Use a production WSGI server like Gunicorn
3. Configure proper database connection pooling
4. Set up SSL/TLS certificates
5. Use environment variables for sensitive data
6. Configure logging and monitoring

## License

This project is open source and available under the MIT License.
