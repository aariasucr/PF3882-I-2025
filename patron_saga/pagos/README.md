# Payment Gateway API

A REST API that emulates a payment gateway for ecommerce sites, built with Flask, SQLAlchemy, and PostgreSQL.

## Features

- ✅ Payment processing with multiple payment methods
- ✅ Payment status tracking and management
- ✅ Refund processing (full and partial)
- ✅ Transaction history
- ✅ Input validation with Marshmallow
- ✅ PostgreSQL database with SQLAlchemy ORM
- ✅ Swagger/OpenAPI documentation
- ✅ Asynchronous payment processing
- ✅ RESTful API design

## Tech Stack

- **Flask**: Web framework
- **Flasgger**: Swagger/OpenAPI documentation
- **Marshmallow**: Data validation and serialization
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Database
- **Flask-CORS**: Cross-origin resource sharing

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Virtual environment (already created)

### 1. Install Dependencies

```bash
# Activate your virtual environment
source .venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 2. Database Setup

Make sure PostgreSQL is running and create the database:

```sql
CREATE DATABASE saga;
```

The application will automatically create the required tables when it starts.

### 3. Environment Configuration

Update the `.env` file with your configuration if needed:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://postgres:postgres@localhost/saga
FLASK_ENV=development
FLASK_DEBUG=1
```

### 4. Run the Application

```bash
python app.py
```

The API will be available at `http://localhost:5000`

## API Documentation

Once the application is running, you can access the interactive Swagger documentation at:
`http://localhost:5000/apidocs/`

## API Endpoints

### Payments

#### Create Payment

- **POST** `/api/v1/payments`
- Creates a new payment transaction

#### Get Payment

- **GET** `/api/v1/payments/{payment_id}`
- Retrieves payment details by ID

#### List Payments

- **GET** `/api/v1/payments?merchant_id={merchant_id}`
- Lists payments for a specific merchant

#### Refund Payment

- **POST** `/api/v1/payments/{payment_id}/refund`
- Processes a refund for a payment

#### Get Payment Transactions

- **GET** `/api/v1/payments/{payment_id}/transactions`
- Retrieves all transactions for a payment

### Health Check

#### Health Check

- **GET** `/api/v1/health`
- Returns API health status

## Payment Workflow

1. **Create Payment**: Submit payment details
2. **Processing**: Payment is processed asynchronously
3. **Status Updates**: Payment status changes from `pending` → `processing` → `completed`/`failed`
4. **Refunds**: Process refunds for completed payments

## Payment Statuses

- `pending`: Payment created, awaiting processing
- `processing`: Payment is being processed
- `completed`: Payment successfully processed
- `failed`: Payment processing failed
- `cancelled`: Payment was cancelled
- `refunded`: Payment was refunded

## Payment Methods

- `credit_card`: Credit card payment
- `debit_card`: Debit card payment
- `paypal`: PayPal payment
- `bank_transfer`: Bank transfer payment

## Example Usage

### Create a Payment

```bash
curl -X POST http://localhost:5000/api/v1/payments \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "merchant_123",
    "order_id": "order_456",
    "amount": 99.99,
    "currency": "USD",
    "payment_method": "credit_card",
    "customer_email": "customer@example.com",
    "customer_name": "John Doe",
    "card_number": "4111111111111111",
    "card_expiry_month": 12,
    "card_expiry_year": 2025,
    "card_cvv": "123",
    "description": "Purchase from online store"
  }'
```

### Get Payment Status

```bash
curl http://localhost:5000/api/v1/payments/{payment_id}
```

### Process Refund

```bash
curl -X POST http://localhost:5000/api/v1/payments/{payment_id}/refund \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50.00,
    "reason": "Customer request"
  }'
```

## Database Schema

### Payments Table

- Payment information and status
- Customer details
- Payment method information
- Timestamps and metadata

### Transactions Table

- Individual transaction records
- Links to payments
- Gateway responses and transaction IDs

### Merchants Table

- Merchant information and settings
- API keys and webhook URLs

## Error Handling

The API returns structured error responses with appropriate HTTP status codes:

- `400`: Bad Request (validation errors)
- `404`: Not Found
- `500`: Internal Server Error

## Security Considerations

- Input validation with Marshmallow schemas
- SQL injection protection via SQLAlchemy ORM
- Sensitive card data handling (only last 4 digits stored)
- Environment-based configuration

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-flask

# Run tests
pytest
```

### Database Migrations

The application automatically creates tables on startup. For production environments, consider using Flask-Migrate for proper database migrations.

## Production Deployment

For production deployment:

1. Set `FLASK_ENV=production` in environment variables
2. Use a production WSGI server like Gunicorn
3. Configure proper database connection pooling
4. Implement proper logging and monitoring
5. Set up SSL/TLS encryption
6. Implement rate limiting and authentication

## License

This project is for educational purposes and simulates a payment gateway. Do not use in production without proper security audits and compliance checks.
