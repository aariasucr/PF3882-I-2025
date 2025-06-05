# 🎯 Saga Pattern Testing Guide

This guide provides comprehensive curl commands to test both **Orchestrated** and **Choreographed** Saga patterns in your e-commerce microservices system.

## 📋 Prerequisites

Ensure all services are running:

```bash
docker-compose -f docker-compose.saga.yml up -d
```

Verify services are healthy:

```bash
curl http://localhost:3000/health  # Cart Service
curl http://localhost:3001/health  # Inventory Service
curl http://localhost:3002/api/v1/health  # Payment Service
curl http://localhost:3003/health  # Saga Orchestrator
curl http://localhost:3004/health  # Saga Choreography
```

## 🛠️ Step 1: Setup Test Data

### 1.1 Create Test Products

Create a gaming laptop:

```bash
curl -X POST http://localhost:3001/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gaming Laptop",
    "description": "High-performance gaming laptop",
    "price": 1299.99,
    "quantity": 10,
    "category": "Electronics",
    "sku": "LAPTOP-GAMING-001"
  }'
```

Create a wireless mouse:

```bash
curl -X POST http://localhost:3001/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wireless Mouse",
    "description": "Ergonomic wireless mouse",
    "price": 29.99,
    "quantity": 50,
    "category": "Accessories",
    "sku": "MOUSE-WIRELESS-001"
  }'
```

### 1.2 Create Test Carts

Create cart for orchestrated saga:

```bash
ORCHESTRATED_CART=$(curl -s -X POST http://localhost:3000/carts \
  -H "Content-Type: application/json" \
  -d '{"user_id": "orchestrated-user-123"}')

ORCHESTRATED_CART_ID=$(echo $ORCHESTRATED_CART | jq -r '.id')
echo "Orchestrated Cart ID: $ORCHESTRATED_CART_ID"
```

Create cart for choreographed saga:

```bash
CHOREOGRAPHED_CART=$(curl -s -X POST http://localhost:3000/carts \
  -H "Content-Type: application/json" \
  -d '{"user_id": "choreographed-user-456"}')

CHOREOGRAPHED_CART_ID=$(echo $CHOREOGRAPHED_CART | jq -r '.id')
echo "Choreographed Cart ID: $CHOREOGRAPHED_CART_ID"
```

## 🎯 Step 2: Test Orchestrated Saga Pattern

### 2.1 Initiate Orchestrated Saga

**Replace `$ORCHESTRATED_CART_ID` with your actual cart ID:**

```bash
ORCHESTRATED_SAGA=$(curl -s -X POST http://localhost:3003/saga/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "cart_id": "YOUR_ORCHESTRATED_CART_ID",
    "user_id": "orchestrated-user-123",
    "items": [
      {"product_id": 1, "quantity": 2},
      {"product_id": 2, "quantity": 1}
    ],
    "payment_method": "credit_card",
    "billing_address": {
      "street": "123 Orchestrated St",
      "city": "Saga City",
      "country": "US",
      "postal_code": "12345"
    }
  }')

echo "Orchestrated Saga Response:"
echo $ORCHESTRATED_SAGA | jq

ORCHESTRATED_SAGA_ID=$(echo $ORCHESTRATED_SAGA | jq -r '.saga_id')
echo "Orchestrated Saga ID: $ORCHESTRATED_SAGA_ID"
```

### 2.2 Monitor Orchestrated Saga Status

Wait for processing (3 seconds) then check status:

```bash
sleep 3

# Check saga transactions
curl -s http://localhost:3003/saga/transactions | jq

# Check specific saga status (if endpoint exists)
curl -s http://localhost:3003/saga/$ORCHESTRATED_SAGA_ID/status | jq
```

### 2.3 Verify Orchestrated Saga Results

Check inventory reservations:

```bash
curl -s http://localhost:3001/api/products/reservations/$ORCHESTRATED_CART_ID | jq
```

Check created orders:

```bash
curl -s http://localhost:3000/orders/saga/$ORCHESTRATED_CART_ID | jq
```

Check payment records:

```bash
curl -s http://localhost:3002/api/v1/payments/saga/$ORCHESTRATED_CART_ID | jq
```

Check updated cart status:

```bash
curl -s http://localhost:3000/carts/$ORCHESTRATED_CART_ID | jq
```

## 🎭 Step 3: Test Choreographed Saga Pattern

### 3.1 Initiate Choreographed Saga

**Replace `$CHOREOGRAPHED_CART_ID` with your actual cart ID:**

```bash
CHOREOGRAPHED_SAGA=$(curl -s -X POST http://localhost:3004/saga/choreography/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "cart_id": "YOUR_CHOREOGRAPHED_CART_ID",
    "user_id": "choreographed-user-456",
    "items": [
      {"product_id": 1, "quantity": 1}
    ],
    "payment_method": "debit_card",
    "billing_address": {
      "street": "456 Choreographed Ave",
      "city": "Event City",
      "country": "US",
      "postal_code": "67890"
    }
  }')

echo "Choreographed Saga Response:"
echo $CHOREOGRAPHED_SAGA | jq

CHOREOGRAPHED_SAGA_ID=$(echo $CHOREOGRAPHED_SAGA | jq -r '.saga_id')
echo "Choreographed Saga ID: $CHOREOGRAPHED_SAGA_ID"
```

### 3.2 Monitor Choreographed Saga Status

Wait for event processing (5 seconds) then check status:

```bash
sleep 5

# Check choreographed saga status
curl -s http://localhost:3004/saga/choreography/$CHOREOGRAPHED_SAGA_ID | jq

# List all choreographed sagas
curl -s http://localhost:3004/saga/choreography/status | jq
```

### 3.3 Verify Choreographed Saga Results

Check inventory reservations:

```bash
curl -s http://localhost:3001/api/products/reservations/$CHOREOGRAPHED_CART_ID | jq
```

Check created orders:

```bash
curl -s http://localhost:3000/orders/saga/$CHOREOGRAPHED_CART_ID | jq
```

Check updated cart status:

```bash
curl -s http://localhost:3000/carts/$CHOREOGRAPHED_CART_ID | jq
```

## 🐰 Step 4: Monitor RabbitMQ Events (Choreographed)

### 4.1 Check RabbitMQ Management

Check all queues:

```bash
curl -s -u guest:guest http://localhost:15672/api/queues | jq
```

Check specific saga event queue:

```bash
curl -s -u guest:guest http://localhost:15672/api/queues/%2F/saga_events | jq
```

Check exchange bindings:

```bash
curl -s -u guest:guest http://localhost:15672/api/exchanges/%2F/saga_exchange/bindings/source | jq
```

### 4.2 Access RabbitMQ Web UI

Open in browser: http://localhost:15672

- **Username:** guest
- **Password:** guest

## 💚 Step 5: System Health Checks

### 5.1 Service Health Status

Check all service health:

```bash
echo "=== Cart Service ==="
curl -s http://localhost:3000/health | jq

echo "=== Inventory Service ==="
curl -s http://localhost:3001/health | jq

echo "=== Payment Service ==="
curl -s http://localhost:3002/api/v1/health | jq

echo "=== Saga Orchestrator ==="
curl -s http://localhost:3003/health | jq

echo "=== Saga Choreography ==="
curl -s http://localhost:3004/health | jq
```

### 5.2 Database Status

Check database connectivity:

```bash
curl -s http://localhost:3000/ | jq
```

### 5.3 Final Inventory Levels

Check updated inventory after saga executions:

```bash
curl -s http://localhost:3001/api/products | jq '.products[] | {id, name, quantity}'
```

## ⚠️ Step 6: Test Failure Scenarios

### 6.1 Test Inventory Shortage (Orchestrated)

Create a failure test cart:

```bash
FAILURE_CART=$(curl -s -X POST http://localhost:3000/carts \
  -H "Content-Type: application/json" \
  -d '{"user_id": "failure-test-user"}')

FAILURE_CART_ID=$(echo $FAILURE_CART | jq -r '.id')
echo "Failure Test Cart ID: $FAILURE_CART_ID"
```

Try to order more than available inventory:

```bash
FAILURE_SAGA=$(curl -s -X POST http://localhost:3003/saga/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "cart_id": "'$FAILURE_CART_ID'",
    "user_id": "failure-test-user",
    "items": [
      {"product_id": 1, "quantity": 999}
    ],
    "payment_method": "credit_card",
    "billing_address": {
      "street": "123 Failure St",
      "city": "Test City",
      "country": "US",
      "postal_code": "99999"
    }
  }')

echo "Failure Saga Response:"
echo $FAILURE_SAGA | jq
```

Check compensation actions:

```bash
sleep 3
echo "Checking compensation actions..."
curl -s http://localhost:3003/saga/transactions | jq
```

### 6.2 Test Invalid Payment (Choreographed)

Try choreographed saga with invalid payment data:

```bash
curl -X POST http://localhost:3004/saga/choreography/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "cart_id": "'$CHOREOGRAPHED_CART_ID'",
    "user_id": "invalid-payment-user",
    "items": [
      {"product_id": 1, "quantity": 1}
    ],
    "payment_method": "invalid_card",
    "billing_address": {
      "street": "",
      "city": "",
      "country": "",
      "postal_code": ""
    }
  }'
```

## 📊 Step 7: Compare Results

### 7.1 Performance Comparison

Time orchestrated saga:

```bash
time curl -X POST http://localhost:3003/saga/checkout \
  -H "Content-Type: application/json" \
  -d '{...}'  # Use full payload
```

Time choreographed saga:

```bash
time curl -X POST http://localhost:3004/saga/choreography/checkout \
  -H "Content-Type: application/json" \
  -d '{...}'  # Use full payload
```

### 7.2 Resource Usage

Check Docker container resource usage:

```bash
docker stats --no-stream
```

### 7.3 Final Summary

View all orders created:

```bash
echo "=== All Orders Created ==="
curl -s http://localhost:3000/orders/saga/$ORCHESTRATED_CART_ID | jq
curl -s http://localhost:3000/orders/saga/$CHOREOGRAPHED_CART_ID | jq
```

View final inventory state:

```bash
echo "=== Final Inventory State ==="
curl -s http://localhost:3001/api/products | jq
```

## 🚀 Quick Test Script

To run all tests automatically, use the provided script:

```bash
chmod +x test_sagas.sh
./test_sagas.sh
```

## 🔍 Key Differences to Observe

### Orchestrated Saga:

- ✅ **Centralized control** - Single orchestrator coordinates all steps
- ✅ **Sequential execution** - Steps executed one after another
- ✅ **Immediate feedback** - Direct response with saga status
- ✅ **Easier debugging** - Central point to monitor transaction flow

### Choreographed Saga:

- ✅ **Distributed control** - Each service handles its own coordination
- ✅ **Event-driven** - Services communicate via RabbitMQ events
- ✅ **Parallel execution** - Steps can execute concurrently
- ✅ **Higher resilience** - No single point of failure

## 📈 Expected Results

After running both patterns, you should observe:

1. **Successful Transactions**: Both patterns complete successfully under normal conditions
2. **Inventory Updates**: Product quantities decrease after successful sagas
3. **Order Creation**: Orders are created in both patterns
4. **Payment Processing**: Payments are processed and recorded
5. **Compensation**: Failed transactions trigger rollback actions
6. **Event Flow**: RabbitMQ shows event exchanges for choreographed pattern

## 🎯 Troubleshooting

If you encounter issues:

1. **Check service logs**:

   ```bash
   docker-compose -f docker-compose.saga.yml logs [service-name]
   ```

2. **Verify database connectivity**:

   ```bash
   docker-compose -f docker-compose.saga.yml logs db
   ```

3. **Check RabbitMQ status**:

   ```bash
   docker-compose -f docker-compose.saga.yml logs rabbitmq
   ```

4. **Restart services if needed**:
   ```bash
   docker-compose -f docker-compose.saga.yml restart
   ```

---

**✅ Success!** You now have a complete testing suite for both Saga patterns! 🎉
