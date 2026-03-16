curl -X POST http://localhost:8080/api/v1/orders \
-H "Content-Type: application/json" \
-d '{
  "customerId": 123,
  "productDetails": "Laptop Pro 14",
  "quantity": 1
}'