# API Examples - Flight Disruption Management System

This document provides practical examples of how to use the Flight Disruption Management System APIs.

## Authentication

All API calls require authentication. First, get a JWT token:

```bash
# Get JWT token
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"

# Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}

# Use token in subsequent requests
export TOKEN="your_jwt_token_here"
```

## 1. Passenger Management

### Create a Passenger
```bash
curl -X POST http://localhost:8000/api/v1/passengers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "pnr": "ABC123",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+447700123456",
    "nationality": "GBR"
  }'
```

### Get Passenger by PNR
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/passengers/pnr/ABC123
```

### Create a Booking
```bash
curl -X POST http://localhost:8000/api/v1/bookings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "passenger_id": "passenger-uuid-here",
    "flight_id": "flight-uuid-here",
    "seat_number": "14A",
    "class": "economy",
    "booking_reference": "BABC123",
    "original_price": 250.00
  }'
```

## 2. Disruption Predictions

### Predict Single Flight Disruption
```bash
curl -X POST http://localhost:8000/api/v1/predictions/single \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "flight_id": "flight-uuid-here",
    "departure_time": "2024-01-15T08:00:00Z",
    "arrival_time": "2024-01-15T10:30:00Z",
    "departure_airport": "LHR",
    "arrival_airport": "CDG",
    "aircraft_type": "Airbus A320",
    "weather_data": {
      "visibility": "5000m",
      "wind_speed": "25kt",
      "precipitation": "light_rain",
      "temperature": "8C"
    }
  }'

# Response:
{
  "flight_id": "flight-uuid-here",
  "predicted_disruption_type": "weather",
  "confidence_score": 0.78,
  "predicted_delay_minutes": 45,
  "prediction_horizon_hours": 4,
  "reasoning": "High winds and reduced visibility at LHR likely to cause moderate delays",
  "risk_factors": ["High wind speed", "Reduced visibility", "Weather deteriorating"],
  "recommended_actions": ["Monitor weather conditions", "Prepare alternative aircraft", "Alert ground crew"],
  "created_at": "2024-01-15T06:00:00Z"
}
```

### Batch Predictions
```bash
curl -X POST http://localhost:8000/api/v1/predictions/batch \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "flight_ids": ["flight1-uuid", "flight2-uuid", "flight3-uuid"],
    "prediction_horizon_hours": 4
  }'
```

### Get High-Risk Flights
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/predictions/high-risk?hours_ahead=4&confidence_threshold=0.7"
```

## 3. Rebooking Management

### Create Rebooking Request
```bash
curl -X POST http://localhost:8000/api/v1/rebookings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "original_booking_id": "booking-uuid-here",
    "disruption_id": "disruption-uuid-here",
    "preferred_departure_time": "2024-01-15T10:00:00Z",
    "class_preference": "economy",
    "flexible_dates": true,
    "max_layovers": 1
  }'

# Response:
{
  "id": "rebooking-uuid",
  "original_booking_id": "booking-uuid-here",
  "new_flight_id": "new-flight-uuid",
  "passenger_id": "passenger-uuid",
  "disruption_id": "disruption-uuid",
  "rebooking_status": "confirmed",
  "alternative_options": [
    {
      "flight_id": "alt-flight-1",
      "flight_number": "BA123",
      "departure_time": "2024-01-15T10:30:00Z",
      "arrival_time": "2024-01-15T13:00:00Z",
      "cost_difference": 0,
      "suitability_score": 0.89
    }
  ],
  "cost_difference": 0,
  "created_at": "2024-01-15T06:15:00Z"
}
```

### Get Flight Passengers
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/flights/flight-uuid-here/passengers
```

## 4. Cost Optimization

### Optimize Hotel Accommodations
```bash
curl -X POST http://localhost:8000/api/v1/cost-optimization/hotels \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "disruption_id": "disruption-uuid",
    "affected_passengers": [
      {
        "passenger_id": "passenger1-uuid",
        "room_preference": "single",
        "loyalty_program": "marriott_gold"
      },
      {
        "passenger_id": "passenger2-uuid",
        "room_preference": "double",
        "special_requirements": ["wheelchair_accessible"]
      }
    ],
    "location": "LHR",
    "check_in_date": "2024-01-15",
    "check_out_date": "2024-01-16",
    "budget_limit": 200.00
  }'

# Response:
{
  "optimization_id": "opt-uuid",
  "total_original_cost": 800.00,
  "total_optimized_cost": 620.00,
  "savings": 180.00,
  "hotel_bookings": [
    {
      "passenger_id": "passenger1-uuid",
      "hotel_name": "Premier Inn Heathrow",
      "cost": 89.00,
      "booking_reference": "PI123456"
    }
  ]
}
```

### Optimize Transport
```bash
curl -X POST http://localhost:8000/api/v1/cost-optimization/transport \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "disruption_id": "disruption-uuid",
    "transport_requests": [
      {
        "passenger_id": "passenger1-uuid",
        "pickup_location": "Heathrow Terminal 5",
        "destination": "Premier Inn Heathrow",
        "transport_type": "taxi",
        "scheduled_time": "2024-01-15T14:00:00Z"
      }
    ],
    "optimize_for": "cost"
  }'
```

## 5. EU261 Compliance

### Calculate Compensation
```bash
curl -X POST http://localhost:8000/api/v1/compliance/compensation/calculate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "booking_id": "booking-uuid",
    "disruption_id": "disruption-uuid",
    "flight_distance_km": 1250,
    "delay_minutes": 180,
    "disruption_type": "weather",
    "exceptional_circumstances": false
  }'

# Response:
{
  "eligible_for_compensation": true,
  "compensation_amount": 400.00,
  "currency": "EUR",
  "reason": "Flight delay over 3 hours on medium distance route (1250km)",
  "regulation": "EU261/2004 Article 7",
  "exceptional_circumstances": false,
  "automatic_processing": true
}
```

### Process Compensation Claim
```bash
curl -X POST http://localhost:8000/api/v1/compliance/compensation/claims \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "passenger_id": "passenger-uuid",
    "booking_id": "booking-uuid",
    "disruption_id": "disruption-uuid",
    "compensation_amount": 400.00,
    "claim_type": "automatic",
    "payment_method": "bank_transfer",
    "bank_details": {
      "iban": "GB29NWBK60161331926819",
      "account_holder": "John Doe"
    }
  }'
```

## 6. Notifications

### Send Passenger Notification
```bash
curl -X POST http://localhost:8000/api/v1/notifications \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "passenger_id": "passenger-uuid",
    "type": "email",
    "subject": "Flight Disruption Update",
    "message": "Your flight BA123 has been delayed by 2 hours due to weather conditions. We have automatically rebooked you on flight BA125 departing at 10:30.",
    "priority": "high",
    "send_immediately": true
  }'
```

### Send Bulk Notifications
```bash
curl -X POST http://localhost:8000/api/v1/notifications/bulk \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "disruption_id": "disruption-uuid",
    "message_template": "flight_disruption",
    "channels": ["email", "sms"],
    "personalization": {
      "flight_number": "BA123",
      "new_departure_time": "10:30",
      "compensation_amount": "£400"
    }
  }'
```

## 7. Monitoring and Health

### System Health Check
```bash
curl http://localhost:8000/health

# Response:
{
  "status": "healthy",
  "timestamp": "2024-01-15T06:30:00Z",
  "services": {
    "redis": "healthy",
    "postgres": "healthy",
    "disruption-predictor": "healthy",
    "passenger-management": "healthy",
    "cost-optimizer": "healthy",
    "compliance": "healthy",
    "notification": "healthy"
  }
}
```

### Service Metrics
```bash
curl http://localhost:8000/metrics
```

## 8. Advanced Examples

### Complete Disruption Management Workflow
```bash
# 1. Detect potential disruption
curl -X POST http://localhost:8000/api/v1/predictions/single \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"flight_id": "BA123-uuid", ...}'

# 2. If high confidence, get affected passengers
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/flights/BA123-uuid/passengers

# 3. Create rebookings for affected passengers
curl -X POST http://localhost:8000/api/v1/rebookings \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"original_booking_id": "booking-uuid", ...}'

# 4. Calculate compensation
curl -X POST http://localhost:8000/api/v1/compliance/compensation/calculate \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"booking_id": "booking-uuid", ...}'

# 5. Send notifications
curl -X POST http://localhost:8000/api/v1/notifications/bulk \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"disruption_id": "disruption-uuid", ...}'
```

### Bulk Operations
```bash
# Process multiple disruptions
for flight_id in flight1-uuid flight2-uuid flight3-uuid; do
  curl -X POST http://localhost:8000/api/v1/predictions/single \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"flight_id\": \"$flight_id\", ...}"
done
```

## Error Handling

### Common HTTP Status Codes
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Invalid or missing token
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Example Error Response
```json
{
  "detail": "Passenger with PNR ABC123 not found",
  "error_code": "PASSENGER_NOT_FOUND",
  "timestamp": "2024-01-15T06:30:00Z"
}
```

## Rate Limits

- **Default**: 1000 requests per minute per IP
- **Authentication**: Required for all endpoints except `/health`
- **Bulk operations**: Lower rate limits apply

## Testing Scripts

### Create Test Data
```bash
#!/bin/bash
# Create comprehensive test data

TOKEN="your_token_here"

# Create test passenger
PASSENGER_ID=$(curl -s -X POST http://localhost:8000/api/v1/passengers \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"pnr": "TEST001", "first_name": "Test", "last_name": "Passenger", "email": "test@example.com"}' \
  | jq -r '.id')

echo "Created passenger: $PASSENGER_ID"

# Create test booking
BOOKING_ID=$(curl -s -X POST http://localhost:8000/api/v1/bookings \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"passenger_id\": \"$PASSENGER_ID\", \"flight_id\": \"test-flight-id\", \"class\": \"economy\", \"booking_reference\": \"TEST001\", \"original_price\": 200}" \
  | jq -r '.id')

echo "Created booking: $BOOKING_ID"
```

This completes the comprehensive API examples. The system provides extensive functionality for managing flight disruptions autonomously while maintaining full observability and control.