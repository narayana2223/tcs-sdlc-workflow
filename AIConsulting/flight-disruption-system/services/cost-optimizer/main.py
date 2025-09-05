"""
Cost Optimizer Service

Advanced cost optimization microservice for flight disruptions.
Handles hotel bookings, transport arrangements, meal vouchers, and compensation calculations.
"""

import asyncio
import json
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import structlog
import redis.asyncio as redis
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import httpx
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST

from config import settings
from database import Database
from optimization_engine import OptimizationEngine
from vendor_integrations import VendorIntegrations

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
OPTIMIZATION_COUNTER = Counter('optimizations_total', 'Total optimizations performed', ['type'])
OPTIMIZATION_DURATION = Histogram('optimization_duration_seconds', 'Time spent on optimizations')
COST_SAVINGS_GAUGE = Gauge('cost_savings_current', 'Current cost savings achieved')
VENDOR_REQUESTS = Counter('vendor_requests_total', 'Total vendor API requests', ['vendor', 'status'])

# Pydantic models
class PassengerProfile(BaseModel):
    passenger_id: str
    loyalty_tier: Optional[str] = None
    preferences: Dict[str, Any] = {}
    mobility_assistance: bool = False
    dietary_requirements: Optional[str] = None

class DisruptionContext(BaseModel):
    disruption_id: str
    flight_id: str
    disruption_type: str
    severity: int = Field(..., ge=1, le=5)
    estimated_delay_hours: int
    affected_passenger_count: int
    original_departure: datetime
    original_arrival: datetime
    departure_airport: str
    arrival_airport: str

class CostOptimizationRequest(BaseModel):
    disruption_context: DisruptionContext
    passenger_profiles: List[PassengerProfile]
    budget_constraints: Optional[Dict[str, float]] = None
    optimization_priorities: List[str] = ["cost", "passenger_satisfaction", "time"]
    include_hotels: bool = True
    include_transport: bool = True
    include_meals: bool = True
    include_compensation: bool = True

class OptimizationResult(BaseModel):
    optimization_id: str
    total_cost: float
    cost_breakdown: Dict[str, float]
    passenger_allocations: List[Dict[str, Any]]
    vendor_bookings: List[Dict[str, Any]]
    compensation_calculations: List[Dict[str, Any]]
    estimated_savings: float
    confidence_score: float
    recommendations: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class HotelBookingRequest(BaseModel):
    passenger_id: str
    check_in_date: datetime
    check_out_date: datetime
    location: str
    room_type: Optional[str] = "standard"
    max_price_per_night: Optional[float] = None
    accessibility_requirements: bool = False

class TransportBookingRequest(BaseModel):
    passenger_id: str
    pickup_location: str
    destination: str
    pickup_time: datetime
    transport_type: str = "taxi"  # taxi, bus, train
    max_price: Optional[float] = None
    accessibility_requirements: bool = False

class CompensationRequest(BaseModel):
    passenger_id: str
    disruption_type: str
    delay_hours: int
    flight_distance_km: int
    ticket_price: float
    passenger_class: str

# Global variables
db: Optional[Database] = None
redis_client: Optional[redis.Redis] = None
kafka_producer: Optional[AIOKafkaProducer] = None
kafka_consumer: Optional[AIOKafkaConsumer] = None
optimization_engine: Optional[OptimizationEngine] = None
vendor_integrations: Optional[VendorIntegrations] = None
http_client: Optional[httpx.AsyncClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db, redis_client, kafka_producer, kafka_consumer, optimization_engine, vendor_integrations, http_client
    
    # Initialize database
    db = Database(settings.database_url)
    await db.connect()
    
    # Initialize Redis
    redis_client = redis.from_url(settings.redis_url)
    
    # Initialize Kafka
    kafka_producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
        value_serializer=lambda x: json.dumps(x, default=str).encode()
    )
    await kafka_producer.start()
    
    kafka_consumer = AIOKafkaConsumer(
        "disruption-events",
        "rebooking-requests",
        bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
        group_id="cost-optimizer",
        value_deserializer=lambda x: json.loads(x.decode())
    )
    await kafka_consumer.start()
    
    # Initialize HTTP client
    http_client = httpx.AsyncClient(timeout=30.0)
    
    # Initialize optimization engine
    optimization_engine = OptimizationEngine(db, redis_client, http_client)
    
    # Initialize vendor integrations
    vendor_integrations = VendorIntegrations(
        hotel_api_key=settings.hotel_api_key,
        transport_api_key=settings.transport_api_key,
        http_client=http_client
    )
    
    # Start background tasks
    asyncio.create_task(process_optimization_events())
    
    logger.info("Cost Optimizer Service started")
    
    yield
    
    # Shutdown
    if kafka_producer:
        await kafka_producer.stop()
    if kafka_consumer:
        await kafka_consumer.stop()
    if redis_client:
        await redis_client.close()
    if http_client:
        await http_client.aclose()
    if db:
        await db.disconnect()

app = FastAPI(
    title="Cost Optimizer Service",
    description="Advanced cost optimization for flight disruption management",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "cost-optimizer",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/api/v1/optimize", response_model=OptimizationResult)
async def optimize_disruption_costs(
    request: CostOptimizationRequest,
    background_tasks: BackgroundTasks
) -> OptimizationResult:
    """Optimize costs for a flight disruption"""
    start_time = time.time()
    
    try:
        logger.info(
            "Starting cost optimization",
            disruption_id=request.disruption_context.disruption_id,
            passenger_count=len(request.passenger_profiles)
        )
        
        # Run comprehensive cost optimization
        optimization_result = await optimization_engine.optimize_disruption_costs(
            request.disruption_context.dict(),
            [p.dict() for p in request.passenger_profiles],
            request.budget_constraints or {},
            request.optimization_priorities
        )
        
        # Store optimization result
        await db.store_optimization_result(optimization_result)
        
        # Cache result for quick retrieval
        cache_key = f"optimization:{optimization_result['optimization_id']}"
        await redis_client.setex(
            cache_key,
            settings.optimization_cache_ttl,
            json.dumps(optimization_result, default=str)
        )
        
        # Process vendor bookings in background
        if optimization_result.get('vendor_bookings'):
            background_tasks.add_task(
                execute_vendor_bookings,
                optimization_result['vendor_bookings']
            )
        
        # Publish optimization result
        await kafka_producer.send(
            "cost-optimizations",
            {
                "optimization_id": optimization_result['optimization_id'],
                "disruption_id": request.disruption_context.disruption_id,
                "total_cost": optimization_result['total_cost'],
                "estimated_savings": optimization_result['estimated_savings'],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Update metrics
        OPTIMIZATION_COUNTER.labels(type=request.disruption_context.disruption_type).inc()
        OPTIMIZATION_DURATION.observe(time.time() - start_time)
        COST_SAVINGS_GAUGE.set(optimization_result['estimated_savings'])
        
        return OptimizationResult(**optimization_result)
        
    except Exception as e:
        logger.error("Cost optimization failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

@app.post("/api/v1/hotels/book")
async def book_hotel(request: HotelBookingRequest) -> Dict[str, Any]:
    """Book hotel accommodation for passenger"""
    try:
        VENDOR_REQUESTS.labels(vendor="hotel", status="requested").inc()
        
        # Find best hotel options
        hotel_options = await vendor_integrations.search_hotels(
            location=request.location,
            check_in=request.check_in_date,
            check_out=request.check_out_date,
            room_type=request.room_type,
            max_price=request.max_price_per_night,
            accessibility=request.accessibility_requirements
        )
        
        if not hotel_options:
            VENDOR_REQUESTS.labels(vendor="hotel", status="no_availability").inc()
            raise HTTPException(status_code=404, detail="No hotel availability found")
        
        # Select best option based on optimization criteria
        selected_hotel = hotel_options[0]  # Optimization engine should rank these
        
        # Make booking
        booking_result = await vendor_integrations.book_hotel(
            selected_hotel,
            request.passenger_id,
            request.check_in_date,
            request.check_out_date
        )
        
        # Store booking details
        await db.store_hotel_booking(request.passenger_id, booking_result)
        
        VENDOR_REQUESTS.labels(vendor="hotel", status="booked").inc()
        
        return booking_result
        
    except Exception as e:
        VENDOR_REQUESTS.labels(vendor="hotel", status="failed").inc()
        logger.error("Hotel booking failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Hotel booking failed: {str(e)}")

@app.post("/api/v1/transport/book")
async def book_transport(request: TransportBookingRequest) -> Dict[str, Any]:
    """Book transport for passenger"""
    try:
        VENDOR_REQUESTS.labels(vendor="transport", status="requested").inc()
        
        # Find transport options
        transport_options = await vendor_integrations.search_transport(
            pickup=request.pickup_location,
            destination=request.destination,
            pickup_time=request.pickup_time,
            transport_type=request.transport_type,
            max_price=request.max_price,
            accessibility=request.accessibility_requirements
        )
        
        if not transport_options:
            VENDOR_REQUESTS.labels(vendor="transport", status="no_availability").inc()
            raise HTTPException(status_code=404, detail="No transport options found")
        
        # Select best option
        selected_transport = transport_options[0]
        
        # Make booking
        booking_result = await vendor_integrations.book_transport(
            selected_transport,
            request.passenger_id
        )
        
        # Store booking details
        await db.store_transport_booking(request.passenger_id, booking_result)
        
        VENDOR_REQUESTS.labels(vendor="transport", status="booked").inc()
        
        return booking_result
        
    except Exception as e:
        VENDOR_REQUESTS.labels(vendor="transport", status="failed").inc()
        logger.error("Transport booking failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Transport booking failed: {str(e)}")

@app.post("/api/v1/compensation/calculate")
async def calculate_compensation(request: CompensationRequest) -> Dict[str, Any]:
    """Calculate EU261 and additional compensation for passenger"""
    try:
        # Calculate EU261 compensation
        eu261_amount = await optimization_engine.calculate_eu261_compensation(
            delay_hours=request.delay_hours,
            flight_distance_km=request.flight_distance_km,
            disruption_type=request.disruption_type
        )
        
        # Calculate additional airline compensation
        additional_compensation = await optimization_engine.calculate_additional_compensation(
            ticket_price=request.ticket_price,
            passenger_class=request.passenger_class,
            delay_hours=request.delay_hours,
            disruption_type=request.disruption_type
        )
        
        # Calculate meal vouchers
        meal_vouchers = await optimization_engine.calculate_meal_vouchers(
            delay_hours=request.delay_hours,
            passenger_class=request.passenger_class
        )
        
        compensation_details = {
            "passenger_id": request.passenger_id,
            "eu261_compensation": eu261_amount,
            "additional_compensation": additional_compensation,
            "meal_vouchers": meal_vouchers,
            "total_compensation": eu261_amount + additional_compensation + meal_vouchers.get('total_value', 0),
            "calculation_details": {
                "flight_distance_km": request.flight_distance_km,
                "delay_hours": request.delay_hours,
                "disruption_type": request.disruption_type,
                "passenger_class": request.passenger_class,
                "ticket_price": request.ticket_price
            },
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        # Store compensation calculation
        await db.store_compensation_calculation(request.passenger_id, compensation_details)
        
        return compensation_details
        
    except Exception as e:
        logger.error("Compensation calculation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Compensation calculation failed: {str(e)}")

@app.get("/api/v1/optimizations/{optimization_id}")
async def get_optimization_result(optimization_id: str) -> OptimizationResult:
    """Get optimization result by ID"""
    try:
        # Check cache first
        cache_key = f"optimization:{optimization_id}"
        cached = await redis_client.get(cache_key)
        
        if cached:
            result = json.loads(cached)
            return OptimizationResult(**result)
        
        # Check database
        result = await db.get_optimization_result(optimization_id)
        if result:
            # Cache for future requests
            await redis_client.setex(
                cache_key,
                settings.optimization_cache_ttl,
                json.dumps(result, default=str)
            )
            return OptimizationResult(**result)
        
        raise HTTPException(status_code=404, detail="Optimization result not found")
        
    except Exception as e:
        logger.error("Failed to get optimization result", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get result: {str(e)}")

@app.get("/api/v1/disruptions/{disruption_id}/cost-summary")
async def get_disruption_cost_summary(disruption_id: str) -> Dict[str, Any]:
    """Get cost summary for a specific disruption"""
    try:
        cost_summary = await db.get_disruption_cost_summary(disruption_id)
        if not cost_summary:
            raise HTTPException(status_code=404, detail="Disruption not found")
        
        return cost_summary
        
    except Exception as e:
        logger.error("Failed to get cost summary", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get cost summary: {str(e)}")

@app.get("/api/v1/analytics/cost-savings")
async def get_cost_savings_analytics() -> Dict[str, Any]:
    """Get cost savings analytics"""
    try:
        analytics = await db.get_cost_savings_analytics()
        return analytics
        
    except Exception as e:
        logger.error("Failed to get analytics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

# Background tasks
async def process_optimization_events():
    """Process optimization events from Kafka"""
    try:
        async for msg in kafka_consumer:
            try:
                event_data = msg.value
                
                if msg.topic == "disruption-events":
                    await handle_disruption_event(event_data)
                elif msg.topic == "rebooking-requests":
                    await handle_rebooking_request(event_data)
                    
            except Exception as e:
                logger.error("Failed to process Kafka message", error=str(e))
                
    except Exception as e:
        logger.error("Kafka consumer failed", error=str(e))

async def handle_disruption_event(event_data: Dict[str, Any]):
    """Handle new disruption event for cost optimization"""
    try:
        disruption_id = event_data.get('disruption_id')
        severity = event_data.get('severity', 3)
        
        # Only auto-optimize for high-severity disruptions
        if severity >= 4:
            # Get affected passengers
            passengers = await db.get_disruption_passengers(disruption_id)
            
            # Create optimization request
            disruption_context = DisruptionContext(
                disruption_id=disruption_id,
                flight_id=event_data.get('flight_id'),
                disruption_type=event_data.get('type'),
                severity=severity,
                estimated_delay_hours=event_data.get('estimated_delay_hours', 4),
                affected_passenger_count=len(passengers),
                original_departure=datetime.fromisoformat(event_data.get('original_departure')),
                original_arrival=datetime.fromisoformat(event_data.get('original_arrival')),
                departure_airport=event_data.get('departure_airport'),
                arrival_airport=event_data.get('arrival_airport')
            )
            
            passenger_profiles = [
                PassengerProfile(
                    passenger_id=str(p['id']),
                    loyalty_tier=p.get('loyalty_tier'),
                    preferences=p.get('preferences', {}),
                    mobility_assistance=p.get('mobility_assistance', False),
                    dietary_requirements=p.get('dietary_requirements')
                )
                for p in passengers
            ]
            
            # Run optimization
            optimization_request = CostOptimizationRequest(
                disruption_context=disruption_context,
                passenger_profiles=passenger_profiles
            )
            
            await optimize_disruption_costs(optimization_request, None)
        
    except Exception as e:
        logger.error("Failed to handle disruption event", error=str(e))

async def handle_rebooking_request(event_data: Dict[str, Any]):
    """Handle rebooking request for cost calculation"""
    try:
        passenger_id = event_data.get('passenger_id')
        
        # Calculate rebooking-related costs
        rebooking_costs = await optimization_engine.calculate_rebooking_costs(
            passenger_id,
            event_data
        )
        
        # Store costs
        await db.store_rebooking_costs(passenger_id, rebooking_costs)
        
        logger.info(
            "Rebooking costs calculated",
            passenger_id=passenger_id,
            total_cost=rebooking_costs.get('total_cost')
        )
        
    except Exception as e:
        logger.error("Failed to handle rebooking request", error=str(e))

async def execute_vendor_bookings(vendor_bookings: List[Dict[str, Any]]):
    """Execute vendor bookings in background"""
    try:
        for booking in vendor_bookings:
            booking_type = booking.get('type')
            
            if booking_type == 'hotel':
                await vendor_integrations.execute_hotel_booking(booking)
            elif booking_type == 'transport':
                await vendor_integrations.execute_transport_booking(booking)
            
            # Add delay between bookings to avoid rate limits
            await asyncio.sleep(1)
        
        logger.info("Vendor bookings completed", booking_count=len(vendor_bookings))
        
    except Exception as e:
        logger.error("Vendor booking execution failed", error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)