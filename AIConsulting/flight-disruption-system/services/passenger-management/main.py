import asyncio
import json
import structlog
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from pydantic import BaseModel, Field, EmailStr
import redis.asyncio as redis
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import httpx

from database import Database
from rebooking_engine import RebookingEngine
from pss_integrations import PSSIntegration
from config import settings

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

# Pydantic models
class PassengerCreate(BaseModel):
    pnr: str = Field(..., max_length=10)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    nationality: Optional[str] = Field(None, max_length=3)
    passport_number: Optional[str] = Field(None, max_length=20)
    mobility_assistance: bool = False
    dietary_requirements: Optional[str] = None

class PassengerResponse(BaseModel):
    id: UUID
    pnr: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    nationality: Optional[str] = None
    mobility_assistance: bool = False
    current_bookings: List[Dict[str, Any]] = []
    created_at: datetime

class BookingCreate(BaseModel):
    passenger_id: UUID
    flight_id: UUID
    seat_number: Optional[str] = None
    class_: str = Field(..., alias="class", max_length=20)
    booking_reference: str = Field(..., max_length=10)
    original_price: float

class BookingResponse(BaseModel):
    id: UUID
    passenger_id: UUID
    flight_id: UUID
    seat_number: Optional[str] = None
    class_: str = Field(alias="class")
    booking_reference: str
    status: str
    original_price: float
    flight_details: Optional[Dict[str, Any]] = None
    created_at: datetime

class RebookingRequest(BaseModel):
    original_booking_id: UUID
    disruption_id: UUID
    preferred_departure_time: Optional[datetime] = None
    preferred_arrival_time: Optional[datetime] = None
    class_preference: Optional[str] = None
    flexible_dates: bool = True
    max_layovers: int = 2

class RebookingResponse(BaseModel):
    id: UUID
    original_booking_id: UUID
    new_flight_id: Optional[UUID] = None
    passenger_id: UUID
    disruption_id: UUID
    rebooking_status: str
    alternative_options: List[Dict[str, Any]] = []
    cost_difference: float = 0.0
    created_at: datetime

class DisruptionNotification(BaseModel):
    disruption_id: UUID
    flight_id: UUID
    disruption_type: str
    affected_passengers: List[UUID]
    estimated_delay_minutes: int
    alternative_flights: List[Dict[str, Any]] = []

# Global variables
db: Optional[Database] = None
redis_client: Optional[redis.Redis] = None
kafka_producer: Optional[AIOKafkaProducer] = None
kafka_consumer: Optional[AIOKafkaConsumer] = None
rebooking_engine: Optional[RebookingEngine] = None
pss_integration: Optional[PSSIntegration] = None
http_client: Optional[httpx.AsyncClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db, redis_client, kafka_producer, kafka_consumer, rebooking_engine, pss_integration, http_client
    
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
        "disruption-predictions",
        "flight-updates",
        bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
        group_id="passenger-management",
        value_deserializer=lambda x: json.loads(x.decode())
    )
    await kafka_consumer.start()
    
    # Initialize HTTP client
    http_client = httpx.AsyncClient(timeout=30.0)
    
    # Initialize rebooking engine
    rebooking_engine = RebookingEngine(db, redis_client, http_client)
    
    # Initialize PSS integration
    pss_integration = PSSIntegration(
        amadeus_api_key=settings.amadeus_api_key,
        sabre_api_key=settings.sabre_api_key
    )
    
    # Start background tasks
    asyncio.create_task(process_disruption_events())
    
    logger.info("Passenger Management Service started")
    
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
    title="Passenger Management Service",
    description="Handles passenger rebooking and notifications during flight disruptions",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "passenger-management",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/passengers", response_model=PassengerResponse)
async def create_passenger(passenger: PassengerCreate) -> PassengerResponse:
    """Create a new passenger"""
    try:
        # Check if passenger with PNR already exists
        existing = await db.get_passenger_by_pnr(passenger.pnr)
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Passenger with PNR {passenger.pnr} already exists"
            )
        
        # Create passenger
        passenger_id = await db.create_passenger(passenger.dict())
        
        # Get created passenger with bookings
        passenger_data = await db.get_passenger_with_bookings(passenger_id)
        
        return PassengerResponse(**passenger_data)
        
    except Exception as e:
        logger.error("Failed to create passenger", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create passenger: {str(e)}")

@app.get("/api/v1/passengers/{passenger_id}", response_model=PassengerResponse)
async def get_passenger(passenger_id: UUID) -> PassengerResponse:
    """Get passenger by ID"""
    try:
        passenger_data = await db.get_passenger_with_bookings(passenger_id)
        if not passenger_data:
            raise HTTPException(status_code=404, detail="Passenger not found")
        
        return PassengerResponse(**passenger_data)
        
    except Exception as e:
        logger.error("Failed to get passenger", passenger_id=str(passenger_id), error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get passenger: {str(e)}")

@app.get("/api/v1/passengers/pnr/{pnr}", response_model=PassengerResponse)
async def get_passenger_by_pnr(pnr: str) -> PassengerResponse:
    """Get passenger by PNR"""
    try:
        passenger_data = await db.get_passenger_by_pnr(pnr)
        if not passenger_data:
            raise HTTPException(status_code=404, detail="Passenger not found")
        
        # Get full data with bookings
        full_data = await db.get_passenger_with_bookings(passenger_data['id'])
        return PassengerResponse(**full_data)
        
    except Exception as e:
        logger.error("Failed to get passenger by PNR", pnr=pnr, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get passenger: {str(e)}")

@app.post("/api/v1/bookings", response_model=BookingResponse)
async def create_booking(booking: BookingCreate) -> BookingResponse:
    """Create a new booking"""
    try:
        # Verify passenger exists
        passenger = await db.get_passenger(booking.passenger_id)
        if not passenger:
            raise HTTPException(status_code=404, detail="Passenger not found")
        
        # Verify flight exists
        flight = await db.get_flight(booking.flight_id)
        if not flight:
            raise HTTPException(status_code=404, detail="Flight not found")
        
        # Create booking
        booking_data = booking.dict()
        booking_data['class_'] = booking_data.pop('class_')  # Handle alias
        booking_id = await db.create_booking(booking_data)
        
        # Get created booking with flight details
        booking_data = await db.get_booking_with_flight(booking_id)
        
        # Sync with airline PSS if configured
        if pss_integration:
            try:
                await pss_integration.sync_booking(booking_data)
            except Exception as e:
                logger.warning("Failed to sync booking with PSS", error=str(e))
        
        return BookingResponse(**booking_data)
        
    except Exception as e:
        logger.error("Failed to create booking", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create booking: {str(e)}")

@app.get("/api/v1/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: UUID) -> BookingResponse:
    """Get booking by ID"""
    try:
        booking_data = await db.get_booking_with_flight(booking_id)
        if not booking_data:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        return BookingResponse(**booking_data)
        
    except Exception as e:
        logger.error("Failed to get booking", booking_id=str(booking_id), error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get booking: {str(e)}")

@app.post("/api/v1/rebookings", response_model=RebookingResponse)
async def create_rebooking(
    rebooking_request: RebookingRequest,
    background_tasks: BackgroundTasks
) -> RebookingResponse:
    """Create rebooking for disrupted flight"""
    try:
        # Get original booking
        original_booking = await db.get_booking_with_flight(rebooking_request.original_booking_id)
        if not original_booking:
            raise HTTPException(status_code=404, detail="Original booking not found")
        
        # Get disruption details
        disruption = await db.get_disruption(rebooking_request.disruption_id)
        if not disruption:
            raise HTTPException(status_code=404, detail="Disruption not found")
        
        # Find alternative flights
        alternatives = await rebooking_engine.find_alternative_flights(
            original_booking,
            rebooking_request.dict()
        )
        
        if not alternatives:
            # No alternatives found - create pending rebooking
            rebooking_data = {
                'original_booking_id': rebooking_request.original_booking_id,
                'passenger_id': original_booking['passenger_id'],
                'disruption_id': rebooking_request.disruption_id,
                'rebooking_reason': f"Flight disruption: {disruption['type']}",
                'rebooking_status': 'pending'
            }
            
            rebooking_id = await db.create_rebooking(rebooking_data)
            
            return RebookingResponse(
                id=rebooking_id,
                original_booking_id=rebooking_request.original_booking_id,
                passenger_id=original_booking['passenger_id'],
                disruption_id=rebooking_request.disruption_id,
                rebooking_status='pending',
                alternative_options=[],
                created_at=datetime.utcnow()
            )
        
        # Auto-select best alternative based on preferences
        best_alternative = await rebooking_engine.select_best_alternative(
            alternatives,
            original_booking,
            rebooking_request.dict()
        )
        
        # Create rebooking with selected alternative
        rebooking_data = {
            'original_booking_id': rebooking_request.original_booking_id,
            'new_flight_id': best_alternative['flight_id'],
            'passenger_id': original_booking['passenger_id'],
            'disruption_id': rebooking_request.disruption_id,
            'rebooking_reason': f"Automatic rebooking due to {disruption['type']}",
            'cost_difference': best_alternative.get('cost_difference', 0.0),
            'rebooking_status': 'confirmed'
        }
        
        rebooking_id = await db.create_rebooking(rebooking_data)
        
        # Update original booking status
        await db.update_booking_status(
            rebooking_request.original_booking_id, 
            'rebooked'
        )
        
        # Create new booking for alternative flight
        new_booking_data = {
            'passenger_id': original_booking['passenger_id'],
            'flight_id': best_alternative['flight_id'],
            'class_': original_booking['class_'],
            'booking_reference': f"RB{original_booking['booking_reference'][:8]}",
            'original_price': original_booking['original_price'] + best_alternative.get('cost_difference', 0.0)
        }
        
        await db.create_booking(new_booking_data)
        
        # Send notifications
        background_tasks.add_task(
            send_rebooking_notifications,
            original_booking['passenger_id'],
            rebooking_id,
            best_alternative
        )
        
        # Publish rebooking event
        await kafka_producer.send(
            "passenger-rebookings",
            {
                "rebooking_id": str(rebooking_id),
                "passenger_id": str(original_booking['passenger_id']),
                "original_flight_id": str(original_booking['flight_id']),
                "new_flight_id": str(best_alternative['flight_id']),
                "disruption_id": str(rebooking_request.disruption_id),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return RebookingResponse(
            id=rebooking_id,
            original_booking_id=rebooking_request.original_booking_id,
            new_flight_id=best_alternative['flight_id'],
            passenger_id=original_booking['passenger_id'],
            disruption_id=rebooking_request.disruption_id,
            rebooking_status='confirmed',
            alternative_options=alternatives[:5],  # Top 5 alternatives
            cost_difference=best_alternative.get('cost_difference', 0.0),
            created_at=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error("Failed to create rebooking", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create rebooking: {str(e)}")

@app.get("/api/v1/rebookings/{rebooking_id}", response_model=RebookingResponse)
async def get_rebooking(rebooking_id: UUID) -> RebookingResponse:
    """Get rebooking by ID"""
    try:
        rebooking_data = await db.get_rebooking(rebooking_id)
        if not rebooking_data:
            raise HTTPException(status_code=404, detail="Rebooking not found")
        
        return RebookingResponse(**rebooking_data)
        
    except Exception as e:
        logger.error("Failed to get rebooking", rebooking_id=str(rebooking_id), error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get rebooking: {str(e)}")

@app.post("/api/v1/disruptions/{disruption_id}/notify-passengers")
async def notify_affected_passengers(
    disruption_id: UUID,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Notify all passengers affected by a disruption"""
    try:
        # Get disruption details
        disruption = await db.get_disruption_with_passengers(disruption_id)
        if not disruption:
            raise HTTPException(status_code=404, detail="Disruption not found")
        
        affected_passengers = disruption.get('affected_passengers', [])
        
        # Queue notifications for all affected passengers
        background_tasks.add_task(
            batch_notify_passengers,
            disruption_id,
            affected_passengers,
            disruption
        )
        
        return {
            "message": f"Notifications queued for {len(affected_passengers)} passengers",
            "disruption_id": str(disruption_id),
            "affected_passenger_count": len(affected_passengers),
            "estimated_completion": (datetime.utcnow() + timedelta(minutes=10)).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to notify passengers", disruption_id=str(disruption_id), error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to notify passengers: {str(e)}")

@app.get("/api/v1/passengers/{passenger_id}/disruptions")
async def get_passenger_disruptions(passenger_id: UUID) -> List[Dict[str, Any]]:
    """Get all disruptions affecting a passenger"""
    try:
        disruptions = await db.get_passenger_disruptions(passenger_id)
        return disruptions
        
    except Exception as e:
        logger.error("Failed to get passenger disruptions", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get disruptions: {str(e)}")

@app.get("/api/v1/flights/{flight_id}/passengers")
async def get_flight_passengers(flight_id: UUID) -> List[PassengerResponse]:
    """Get all passengers on a flight"""
    try:
        passengers = await db.get_flight_passengers(flight_id)
        return [PassengerResponse(**passenger) for passenger in passengers]
        
    except Exception as e:
        logger.error("Failed to get flight passengers", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get passengers: {str(e)}")

# Background tasks
async def process_disruption_events():
    """Process disruption events from Kafka"""
    try:
        async for msg in kafka_consumer:
            try:
                event_data = msg.value
                
                if msg.topic == "disruption-predictions":
                    await handle_disruption_prediction(event_data)
                elif msg.topic == "flight-updates":
                    await handle_flight_update(event_data)
                    
            except Exception as e:
                logger.error("Failed to process Kafka message", error=str(e))
                
    except Exception as e:
        logger.error("Kafka consumer failed", error=str(e))

async def handle_disruption_prediction(prediction_data: Dict[str, Any]):
    """Handle disruption prediction event"""
    try:
        flight_id = prediction_data.get('flight_id')
        confidence = prediction_data.get('prediction', {}).get('confidence_score', 0)
        
        # Only act on high-confidence predictions
        if confidence < 0.7:
            return
        
        # Get affected passengers
        passengers = await db.get_flight_passengers(flight_id)
        
        # Start proactive rebooking process
        for passenger in passengers:
            # Queue rebooking for each passenger
            asyncio.create_task(
                proactive_rebooking(passenger, prediction_data)
            )
        
        logger.info(
            "Proactive rebooking initiated",
            flight_id=flight_id,
            passenger_count=len(passengers),
            confidence=confidence
        )
        
    except Exception as e:
        logger.error("Failed to handle disruption prediction", error=str(e))

async def handle_flight_update(update_data: Dict[str, Any]):
    """Handle flight status update event"""
    try:
        flight_id = update_data.get('flight_id')
        new_status = update_data.get('status')
        
        if new_status in ['cancelled', 'delayed']:
            # Get affected passengers
            passengers = await db.get_flight_passengers(flight_id)
            
            # Notify passengers of status change
            for passenger in passengers:
                asyncio.create_task(
                    send_status_update_notification(passenger, update_data)
                )
        
    except Exception as e:
        logger.error("Failed to handle flight update", error=str(e))

async def proactive_rebooking(passenger: Dict[str, Any], prediction_data: Dict[str, Any]):
    """Proactively rebook passenger based on prediction"""
    try:
        # Get passenger's active booking on the predicted disrupted flight
        booking = await db.get_active_booking_for_flight(
            passenger['id'], 
            prediction_data['flight_id']
        )
        
        if not booking:
            return
        
        # Create mock disruption for proactive rebooking
        mock_disruption = {
            'id': uuid4(),
            'flight_id': prediction_data['flight_id'],
            'type': prediction_data.get('prediction', {}).get('predicted_disruption_type', 'weather'),
            'severity': 3,
            'predicted_delay': prediction_data.get('prediction', {}).get('predicted_delay_minutes', 120)
        }
        
        # Find alternatives
        alternatives = await rebooking_engine.find_alternative_flights(
            booking,
            {'flexible_dates': True, 'max_layovers': 1}
        )
        
        if alternatives:
            # Send proactive rebooking options to passenger
            await send_proactive_rebooking_options(
                passenger,
                alternatives,
                prediction_data
            )
        
    except Exception as e:
        logger.error("Proactive rebooking failed", error=str(e))

async def send_rebooking_notifications(
    passenger_id: UUID,
    rebooking_id: UUID,
    alternative_flight: Dict[str, Any]
):
    """Send rebooking notifications to passenger"""
    try:
        # Get passenger contact details
        passenger = await db.get_passenger(passenger_id)
        if not passenger:
            return
        
        # Prepare notification message
        notification_data = {
            'passenger_id': str(passenger_id),
            'type': 'rebooking_confirmation',
            'subject': 'Flight Rebooking Confirmation',
            'message': f"Your flight has been rebooked. New flight: {alternative_flight.get('flight_number')}",
            'rebooking_id': str(rebooking_id),
            'new_flight_details': alternative_flight
        }
        
        # Send via notification service
        await kafka_producer.send("passenger-notifications", notification_data)
        
        logger.info("Rebooking notification sent", passenger_id=str(passenger_id))
        
    except Exception as e:
        logger.error("Failed to send rebooking notification", error=str(e))

async def batch_notify_passengers(
    disruption_id: UUID,
    passenger_ids: List[UUID],
    disruption_data: Dict[str, Any]
):
    """Send notifications to multiple passengers"""
    try:
        for passenger_id in passenger_ids:
            notification_data = {
                'passenger_id': str(passenger_id),
                'disruption_id': str(disruption_id),
                'type': 'flight_disruption',
                'subject': 'Flight Disruption Update',
                'message': f"Your flight has been {disruption_data['type']}. We are working on alternatives.",
                'disruption_details': disruption_data
            }
            
            await kafka_producer.send("passenger-notifications", notification_data)
        
        logger.info(
            "Batch notifications sent",
            disruption_id=str(disruption_id),
            passenger_count=len(passenger_ids)
        )
        
    except Exception as e:
        logger.error("Batch notification failed", error=str(e))

async def send_status_update_notification(
    passenger: Dict[str, Any],
    update_data: Dict[str, Any]
):
    """Send flight status update notification"""
    try:
        notification_data = {
            'passenger_id': str(passenger['id']),
            'type': 'flight_status_update',
            'subject': 'Flight Status Update',
            'message': f"Flight status updated to: {update_data['status']}",
            'flight_details': update_data
        }
        
        await kafka_producer.send("passenger-notifications", notification_data)
        
    except Exception as e:
        logger.error("Status update notification failed", error=str(e))

async def send_proactive_rebooking_options(
    passenger: Dict[str, Any],
    alternatives: List[Dict[str, Any]],
    prediction_data: Dict[str, Any]
):
    """Send proactive rebooking options to passenger"""
    try:
        notification_data = {
            'passenger_id': str(passenger['id']),
            'type': 'proactive_rebooking_options',
            'subject': 'Alternative Flight Options Available',
            'message': 'Based on our predictions, your flight may be disrupted. Here are alternative options.',
            'alternatives': alternatives[:3],  # Top 3 options
            'prediction_confidence': prediction_data.get('prediction', {}).get('confidence_score')
        }
        
        await kafka_producer.send("passenger-notifications", notification_data)
        
        logger.info("Proactive rebooking options sent", passenger_id=str(passenger['id']))
        
    except Exception as e:
        logger.error("Failed to send proactive options", error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)