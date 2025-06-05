# 🎭 Saga Pattern Implementation for E-commerce Microservices

This project implements both **Orchestrated** and **Choreographed** Saga patterns for managing distributed transactions across microservices in an e-commerce system.

## 🏗️ Architecture Overview

### Services

- **Cart Service** (`carrito`) - Shopping cart management
- **Payment Service** (`pagos`) - Payment processing
- **Inventory Service** (`inventario`) - Product inventory management
- **Saga Orchestrator** - Central coordinator for orchestrated sagas
- **Saga Choreography** - Event-driven coordinator for choreographed sagas

### Infrastructure

- **PostgreSQL** - Database for persistence
- **RabbitMQ** - Message broker for event-driven communication

## 🎯 Saga Patterns Implemented

### 1. 🎼 Orchestrated Saga Pattern

**Central Coordinator Controls the Flow**

```
Client Request → Saga Orchestrator → Service A → Service B → Service C
                        ↓
            Tracks State & Handles Compensation
```

**Characteristics:**

- ✅ Centralized control and monitoring
- ✅ Clear transaction state visibility
- ✅ Easier debugging and error handling
- ❌ Single point of failure
- ❌ Services coupled to orchestrator

**Transaction Flow:**

1. Reserve Inventory
2. Process Payment
3. Create Order
4. Commit Inventory

### 2. 💃 Choreographed Saga Pattern

**Services Coordinate Through Events**

```
Client Request → Service A → Event Bus → Service B → Event Bus → Service C
                               ↓              ↓              ↓
                        Event Listeners & Reactive Logic
```

**Characteristics:**

- ✅ Loose coupling between services
- ✅ High scalability and resilience
- ✅ No single point of failure
- ❌ Complex debugging
- ❌ Harder to track overall state

**Event Flow:**

1. `checkout.initiated` → `inventory.reserve.requested`
2. `inventory.reserved` → `payment.requested`
3. `payment.processed` → `order.create.requested`
4. `order.created` → `inventory.commit.requested`
5. `inventory.committed` → `checkout.completed`

## 🚀 Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- PostgreSQL (if running locally)
- RabbitMQ (if running locally)

### 1. Start Infrastructure

```bash
# Start all services including both saga patterns
docker-compose -f docker-compose.saga.yml up -d

# Or start individual components
docker-compose up rabbitmq db
```

### 2. Initialize Database

```bash
# Run database migrations for each service
cd carrito && python -c "from app import db; db.create_all()"
cd ../inventario && python init_db.py
cd ../pagos && python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### 3. Add Sample Data

```bash
# Add sample products to inventory
curl -X POST http://localhost:3001/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop Pro",
    "description": "High-performance laptop",
    "price": 1299.99,
    "quantity": 10,
    "category": "Electronics",
    "sku": "LAPTOP-001"
  }'
```

## 🧪 Testing Both Patterns

### Test Orchestrated Saga

#### 1. Create Cart and Add Items

```bash
# Create cart
cart_response=$(curl -X POST http://localhost:3000/carts \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123"}')

cart_id=$(echo $cart_response | jq -r '.id')

# Add item to cart
curl -X POST http://localhost:3000/carts/$cart_id/items \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "1",
    "quantity": 2
  }'
```

#### 2. Initiate Orchestrated Saga

```bash
# Start orchestrated checkout saga
saga_response=$(curl -X POST http://localhost:3003/saga/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "cart_id": "'$cart_id'",
    "user_id": "user123",
    "payment_method": "credit_card",
    "billing_address": {
      "street": "123 Main St",
      "city": "Anytown",
      "country": "USA",
      "postal_code": "12345"
    }
  }')

saga_id=$(echo $saga_response | jq -r '.saga_id')
echo "Orchestrated Saga ID: $saga_id"
```

#### 3. Monitor Saga Progress

```bash
# Check saga status
curl http://localhost:3003/saga/$saga_id | jq

# Watch real-time progress
watch -n 2 "curl -s http://localhost:3003/saga/$saga_id | jq '.status, .steps[].status'"
```

### Test Choreographed Saga

#### 1. Create Cart and Add Items (same as above)

#### 2. Initiate Choreographed Saga

```bash
# Start choreographed checkout saga
saga_response=$(curl -X POST http://localhost:3004/saga/choreography/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "cart_id": "'$cart_id'",
    "user_id": "user123",
    "payment_method": "credit_card",
    "billing_address": {
      "street": "123 Main St",
      "city": "Anytown",
      "country": "USA",
      "postal_code": "12345"
    }
  }')

saga_id=$(echo $saga_response | jq -r '.saga_id')
echo "Choreographed Saga ID: $saga_id"
```

#### 3. Monitor Saga Progress

```bash
# Check saga status
curl http://localhost:3004/saga/choreography/$saga_id | jq

# View all choreographed sagas
curl http://localhost:3004/saga/choreography/status | jq
```

### Universal Checkout Endpoint

The cart service provides a unified checkout endpoint that can trigger either pattern:

```bash
# Orchestrated checkout
curl -X POST http://localhost:3000/checkout/saga \
  -H "Content-Type: application/json" \
  -d '{
    "cart_id": "'$cart_id'",
    "user_id": "user123",
    "payment_method": "credit_card",
    "billing_address": {...},
    "saga_pattern": "orchestrated"
  }'

# Choreographed checkout
curl -X POST http://localhost:3000/checkout/saga \
  -H "Content-Type: application/json" \
  -d '{
    "cart_id": "'$cart_id'",
    "user_id": "user123",
    "payment_method": "credit_card",
    "billing_address": {...},
    "saga_pattern": "choreographed"
  }'
```

## 🔧 Service Endpoints

### Saga Orchestrator (Port 3003)

- `POST /saga/checkout` - Initiate orchestrated saga
- `GET /saga/{saga_id}` - Get saga status
- `POST /saga/{saga_id}/compensate` - Manual compensation
- `GET /health` - Health check

### Saga Choreography (Port 3004)

- `POST /saga/choreography/checkout` - Initiate choreographed saga
- `GET /saga/choreography/{saga_id}` - Get saga status
- `GET /saga/choreography/status` - List all sagas
- `GET /health` - Health check

### Enhanced Service Endpoints

Each service now includes saga-specific endpoints:

#### Cart Service (Port 3000)

- `POST /checkout/saga` - Universal saga checkout
- `POST /orders` - Create saga order (orchestrated)
- `POST /orders/{order_id}/cancel` - Cancel order (compensation)
- `GET /orders/saga/{cart_id}` - Get saga orders

#### Inventory Service (Port 3001)

- `POST /api/products/reserve` - Reserve inventory (orchestrated)
- `POST /api/products/unreserve` - Unreserve (compensation)
- `POST /api/products/commit` - Commit reservation
- `GET /api/products/reservations/{cart_id}` - View reservations

#### Payment Service (Port 3002)

- `POST /api/v1/payments/saga` - Create saga payment (orchestrated)
- `POST /api/v1/payments/saga/{payment_id}/refund` - Refund (compensation)
- `GET /api/v1/payments/saga/{cart_id}` - Get saga payments

## 📊 Monitoring & Observability

### RabbitMQ Management UI

- **URL:** http://localhost:15672
- **Credentials:** guest/guest
- **Monitor:** Event flows, queue depths, message rates

### Saga Dashboard (Optional)

- **URL:** http://localhost:8080
- **Features:** Visual saga flow tracking

### Health Checks

```bash
# Check all service health
curl http://localhost:3000/health  # Cart
curl http://localhost:3001/health  # Inventory
curl http://localhost:3002/health  # Payment
curl http://localhost:3003/health  # Orchestrator
curl http://localhost:3004/health  # Choreography
```

## 🚨 Error Handling & Compensation

### Orchestrated Saga Compensation

- Automatic retry with exponential backoff
- Sequential compensation in reverse order
- Detailed error tracking and logging

### Choreographed Saga Compensation

- Event-driven compensation flows
- Distributed error handling
- Eventual consistency guarantees

### Testing Failure Scenarios

#### Simulate Payment Failure

```bash
# Create a payment that will fail
curl -X POST http://localhost:3002/api/v1/payments \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "test",
    "order_id": "fail-test",
    "amount": -1,
    "payment_method": "invalid_card"
  }'
```

#### Simulate Inventory Shortage

```bash
# Try to order more than available
curl -X POST http://localhost:3000/carts/{cart_id}/items \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "1",
    "quantity": 999999
  }'
```

## 🎯 When to Use Each Pattern

### Use Orchestrated When:

- ✅ Need centralized control and visibility
- ✅ Complex business logic coordination required
- ✅ Strict data consistency requirements
- ✅ Easier debugging is priority
- ✅ Team prefers centralized architecture

### Use Choreographed When:

- ✅ High scalability and performance needed
- ✅ Loose coupling between services preferred
- ✅ Event-driven architecture already in place
- ✅ Resilience to individual service failures important
- ✅ Independent service evolution required

## 🔍 Performance Considerations

### Orchestrated Saga

- **Latency:** Higher due to sequential HTTP calls
- **Throughput:** Limited by orchestrator capacity
- **Resource Usage:** Central coordinator resource intensive

### Choreographed Saga

- **Latency:** Lower with parallel event processing
- **Throughput:** Higher with distributed processing
- **Resource Usage:** Distributed across services

## 🛠️ Development Guide

### Adding New Saga Steps

#### Orchestrated

1. Add step definition in `orchestrator.py`
2. Implement service endpoint
3. Add compensation logic

#### Choreographed

1. Define new event types in `event_bus.py`
2. Add event handlers in relevant services
3. Implement compensation events

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/saga

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# Service URLs
CARRITO_SERVICE_URL=http://localhost:3000
INVENTARIO_SERVICE_URL=http://localhost:3001
PAGOS_SERVICE_URL=http://localhost:3002
ORCHESTRATOR_URL=http://localhost:3003
CHOREOGRAPHY_URL=http://localhost:3004
```

## 🎉 Summary

This implementation provides a complete comparison of both Saga patterns in a real-world e-commerce context. You can:

✅ **Compare patterns side-by-side** with the same business logic
✅ **Test both patterns** with identical checkout flows  
✅ **Monitor and debug** transactions in both approaches
✅ **Understand trade-offs** through hands-on experience
✅ **Scale and modify** based on your specific needs

The implementation demonstrates enterprise-grade patterns with proper error handling, compensation, monitoring, and scalability considerations.
