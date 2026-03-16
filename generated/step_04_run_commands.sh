curl -X POST http://localhost:8080/api/v1/orders \
    -H "Content-Type: application/json" \
    -d '{"customerId": 101, "totalAmount": 49.99}'