#!/bin/bash

echo "🚀 Starting Saga Pattern Testing..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Setup test data
echo -e "${BLUE}📦 Creating test products...${NC}"

curl -s -X POST http://localhost:3001/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gaming Laptop",
    "description": "High-performance gaming laptop",
    "price": 1299.99,
    "quantity": 10,
    "category": "Electronics",
    "sku": "LAPTOP-GAMING-001"
  }' | jq

curl -s -X POST http://localhost:3001/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wireless Mouse", 
    "description": "Ergonomic wireless mouse",
    "price": 29.99,
    "quantity": 50,
    "category": "Accessories",
    "sku": "MOUSE-WIRELESS-001"
  }' | jq

# 2. Create carts
echo -e "${BLUE}🛒 Creating test carts...${NC}"

ORCHESTRATED_CART=$(curl -s -X POST http://localhost:3000/carts \
  -H "Content-Type: application/json" \
  -d '{"user_id": "orchestrated-user-123"}')

ORCHESTRATED_CART_ID=$(echo $ORCHESTRATED_CART | jq -r '.id')
echo -e "${GREEN}Orchestrated Cart ID: $ORCHESTRATED_CART_ID${NC}"

CHOREOGRAPHED_CART=$(curl -s -X POST http://localhost:3000/carts \
  -H "Content-Type: application/json" \
  -d '{"user_id": "choreographed-user-456"}')

CHOREOGRAPHED_CART_ID=$(echo $CHOREOGRAPHED_CART | jq -r '.id')
echo -e "${GREEN}Choreographed Cart ID: $CHOREOGRAPHED_CART_ID${NC}"

# 3. Test Orchestrated Saga
echo -e "${YELLOW}🎯 Testing ORCHESTRATED Saga Pattern...${NC}"

ORCHESTRATED_SAGA=$(curl -s -X POST http://localhost:3003/saga/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "cart_id": "'$ORCHESTRATED_CART_ID'",
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

echo -e "${GREEN}Orchestrated Saga Response:${NC}"
echo $ORCHESTRATED_SAGA | jq

ORCHESTRATED_SAGA_ID=$(echo $ORCHESTRATED_SAGA | jq -r '.saga_id')
echo -e "${GREEN}Orchestrated Saga ID: $ORCHESTRATED_SAGA_ID${NC}"

# Wait for processing
sleep 3

echo -e "${BLUE}📊 Checking orchestrated saga status...${NC}"
curl -s http://localhost:3003/saga/$ORCHESTRATED_SAGA_ID | jq

# 4. Test Choreographed Saga
echo -e "${YELLOW}🎭 Testing CHOREOGRAPHED Saga Pattern...${NC}"

CHOREOGRAPHED_SAGA=$(curl -s -X POST http://localhost:3003/saga/choreography/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "cart_id": "'$CHOREOGRAPHED_CART_ID'",
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

echo -e "${GREEN}Choreographed Saga Response:${NC}"
echo $CHOREOGRAPHED_SAGA | jq

# Wait for event processing
sleep 5

# 5. Health checks
echo -e "${BLUE}💚 Final system health check...${NC}"

echo -e "${GREEN}Cart Service:${NC}"
curl -s http://localhost:3000/health | jq

echo -e "${GREEN}Inventory Service:${NC}"
curl -s http://localhost:3001/health | jq

echo -e "${GREEN}Payment Service:${NC}"
curl -s http://localhost:3002/api/v1/health | jq

echo -e "${GREEN}Orchestrator:${NC}"
curl -s http://localhost:3003/health | jq

echo -e "${GREEN}Choreography:${NC}"
curl -s http://localhost:3004/health | jq

# 6. Final inventory check
echo -e "${BLUE}📦 Final inventory levels:${NC}"
curl -s http://localhost:3001/api/products | jq '.products[] | {id, name, quantity}'

echo -e "${GREEN}✅ Saga pattern testing complete!${NC}" 