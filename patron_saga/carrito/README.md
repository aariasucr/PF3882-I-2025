# Shopping Cart API

A REST API for shopping cart management with inventory and payment integration.

## Features

- Create and manage shopping carts
- Add, update, and remove items from cart
- Inventory checking through external service integration
- Payment processing through payment gateway
- Complete checkout process
- SQLAlchemy with PostgreSQL database
- Swagger API documentation
- Marshmallow data validation

## Tech Stack

- **Flask** - Web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Database
- **Flasgger** - Swagger documentation
- **Marshmallow** - Data validation and serialization
- **Flask-CORS** - Cross-origin resource sharing

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Virtual environment (already created)

## Setup

1. **Install dependencies:**

   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Database setup:**
   Make sure PostgreSQL is running and create the database:

   ```sql
   CREATE DATABASE saga;
   ```

3. **Environment variables:**
   Create a `.env` file in the root directory:

   ```
   FLASK_APP=app.py
   FLASK_ENV=development
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/saga
   INVENTARIO_SERVICE_URL=http://localhost:3001
   PAGOS_SERVICE_URL=http://localhost:3002
   SECRET_KEY=your-secret-key-here
   ```

4. **Initialize database:**

   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```

The API will be available at `http://localhost:5000`

## API Documentation

Access the Swagger documentation at: `http://localhost:5000/apidocs`

## API Endpoints

### Cart Management

- `POST /carts` - Create a new cart
- `GET /carts/{cart_id}` - Get cart by ID

### Cart Items

- `POST /carts/{cart_id}/items` - Add item to cart
- `PUT /carts/{cart_id}/items/{item_id}` - Update item quantity
- `DELETE /carts/{cart_id}/items/{item_id}` - Remove item from cart

### Checkout

- `POST /carts/{cart_id}/checkout` - Checkout cart and process payment

### Orders

- `GET /orders/{order_id}` - Get order by ID

## External Services

The API integrates with two external services:

### Inventory Service (Inventario)

- **URL**: `http://localhost:3001` (configurable)
- **Endpoints used**:
  - `GET /products/{product_id}` - Get product information
  - `GET /products/{product_id}/availability` - Check product availability

### Payment Gateway (Pagos)

- **URL**: `http://localhost:3002` (configurable)
- **Endpoints used**:
  - `POST /payments` - Process payment

## Usage Examples

### 1. Create a Cart

```bash
curl -X POST http://localhost:5000/carts \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123"}'
```

### 2. Add Item to Cart

```bash
curl -X POST http://localhost:5000/carts/{cart_id}/items \
  -H "Content-Type: application/json" \
  -d '{"product_id": "prod123", "quantity": 2}'
```

### 3. Checkout Cart

```bash
curl -X POST http://localhost:5000/carts/{cart_id}/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "payment_method": "credit_card",
    "billing_address": {
      "street": "123 Main St",
      "city": "Anytown",
      "country": "US",
      "postal_code": "12345"
    }
  }'
```

## Database Schema

### Tables

- **carts**: Main cart table
- **cart_items**: Items within each cart
- **orders**: Completed orders

### Relationships

- Cart has many CartItems (one-to-many)
- Order belongs to Cart (many-to-one)

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `404` - Not Found
- `500` - Internal Server Error

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Database Migrations

```bash
flask db migrate -m "Description of changes"
flask db upgrade
```

## Production Deployment

1. Set environment to production:

   ```
   FLASK_ENV=production
   ```

2. Use a production WSGI server like Gunicorn:
   ```bash
   gunicorn --bind 0.0.0.0:5000 app:app
   ```

## Security Considerations

- Change the `SECRET_KEY` in production
- Use environment variables for sensitive configuration
- Implement authentication and authorization as needed
- Validate and sanitize all inputs
- Use HTTPS in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request
