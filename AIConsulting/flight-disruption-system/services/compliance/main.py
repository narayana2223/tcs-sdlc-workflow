"""
Compliance Service

Comprehensive regulatory compliance engine for flight disruption management.
Handles EU261, UK CAA, DOT regulations, and international aviation compliance.
"""

import asyncio
import json
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from uuid import UUID, uuid4
from enum import Enum

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
from compliance_engine import ComplianceEngine
from regulations import EU261Engine, UKCAAEngine, DOTEngine, IATAEngine

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
COMPLIANCE_CHECKS = Counter('compliance_checks_total', 'Total compliance checks performed', ['regulation', 'status'])
COMPLIANCE_DURATION = Histogram('compliance_check_duration_seconds', 'Time spent on compliance checks')
ACTIVE_CLAIMS = Gauge('active_claims_current', 'Number of active compliance claims')
COMPENSATION_ISSUED = Counter('compensation_issued_total', 'Total compensation issued', ['type', 'regulation'])

# Enums
class DisruptionType(str, Enum):
    WEATHER = "weather"
    TECHNICAL = "technical"
    CREW = "crew"
    ATC = "atc"
    SECURITY = "security"
    STRIKE = "strike"
    EXTRAORDINARY = "extraordinary"
    AIRLINE_OPERATIONAL = "airline_operational"

class CompensationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    PAID = "paid"
    DISPUTED = "disputed"

class RegulationType(str, Enum):
    EU261 = "eu261"
    UK_CAA = "uk_caa"
    US_DOT = "us_dot"
    IATA = "iata"
    MONTREAL_CONVENTION = "montreal_convention"

# Pydantic models
class FlightInfo(BaseModel):
    flight_id: str
    flight_number: str
    departure_airport: str
    arrival_airport: str
    scheduled_departure: datetime
    actual_departure: Optional[datetime] = None
    scheduled_arrival: datetime
    actual_arrival: Optional[datetime] = None
    aircraft_type: str
    distance_km: int

class PassengerInfo(BaseModel):
    passenger_id: str
    pnr: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    nationality: str
    ticket_price: float
    booking_class: str
    mobility_assistance: bool = False

class DisruptionInfo(BaseModel):
    disruption_id: str
    disruption_type: DisruptionType
    cause: str
    delay_minutes: int
    is_extraordinary_circumstance: bool = False
    weather_data: Optional[Dict[str, Any]] = None
    airline_fault: bool = True

class ComplianceRequest(BaseModel):
    flight_info: FlightInfo
    passenger_info: PassengerInfo
    disruption_info: DisruptionInfo
    regulations_to_check: List[RegulationType] = [RegulationType.EU261]
    auto_process_eligible_claims: bool = True

class ComplianceResult(BaseModel):
    compliance_id: str
    passenger_id: str
    flight_id: str
    regulations_checked: List[str]
    compliance_status: Dict[str, Any]
    eligible_compensation: Dict[str, float]
    total_compensation: float
    compensation_breakdown: Dict[str, Any]
    compliance_reasons: List[str]
    required_actions: List[str]
    claim_deadline: Optional[datetime] = None
    processing_time_seconds: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CompensationClaim(BaseModel):
    claim_id: str
    passenger_id: str
    flight_id: str
    regulation_type: RegulationType
    compensation_amount: float
    claim_status: CompensationStatus
    claim_reasons: List[str]
    supporting_documents: List[str] = []
    claim_deadline: datetime
    submitted_at: datetime
    processed_at: Optional[datetime] = None

class ClaimDispute(BaseModel):
    dispute_id: str
    claim_id: str
    passenger_id: str
    dispute_reason: str
    supporting_evidence: List[str] = []
    dispute_status: str = "pending"
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

# Global variables
db: Optional[Database] = None
redis_client: Optional[redis.Redis] = None
kafka_producer: Optional[AIOKafkaProducer] = None
kafka_consumer: Optional[AIOKafkaConsumer] = None
compliance_engine: Optional[ComplianceEngine] = None
http_client: Optional[httpx.AsyncClient] = None

# Regulation engines
eu261_engine: Optional[EU261Engine] = None
uk_caa_engine: Optional[UKCAAEngine] = None
dot_engine: Optional[DOTEngine] = None
iata_engine: Optional[IATAEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db, redis_client, kafka_producer, kafka_consumer, compliance_engine, http_client
    global eu261_engine, uk_caa_engine, dot_engine, iata_engine
    
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
        "passenger-claims",
        "rebooking-requests",
        bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
        group_id="compliance",
        value_deserializer=lambda x: json.loads(x.decode())
    )
    await kafka_consumer.start()
    
    # Initialize HTTP client
    http_client = httpx.AsyncClient(timeout=30.0)
    
    # Initialize regulation engines
    eu261_engine = EU261Engine()
    uk_caa_engine = UKCAAEngine()
    dot_engine = DOTEngine()
    iata_engine = IATAEngine()
    
    # Initialize main compliance engine
    compliance_engine = ComplianceEngine(
        db, redis_client, http_client,
        {
            RegulationType.EU261: eu261_engine,
            RegulationType.UK_CAA: uk_caa_engine,
            RegulationType.US_DOT: dot_engine,
            RegulationType.IATA: iata_engine
        }
    )
    
    # Start background tasks
    asyncio.create_task(process_compliance_events())
    
    logger.info("Compliance Service started")
    
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
    title="Flight Compliance Service",
    description="Comprehensive regulatory compliance engine for flight disruption management",
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
        "service": "compliance",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/api/v1/compliance/check", response_model=ComplianceResult)
async def check_compliance(
    request: ComplianceRequest,
    background_tasks: BackgroundTasks
) -> ComplianceResult:
    """Perform comprehensive compliance check for flight disruption"""
    start_time = time.time()
    
    try:
        logger.info(
            "Starting compliance check",
            passenger_id=request.passenger_info.passenger_id,
            flight_id=request.flight_info.flight_id,
            disruption_type=request.disruption_info.disruption_type
        )
        
        # Perform compliance analysis
        compliance_result = await compliance_engine.check_compliance(
            flight_info=request.flight_info.dict(),
            passenger_info=request.passenger_info.dict(),
            disruption_info=request.disruption_info.dict(),
            regulations=request.regulations_to_check
        )
        
        # Store compliance result
        await db.store_compliance_result(compliance_result)
        
        # Cache result
        cache_key = f"compliance:{compliance_result['compliance_id']}"
        await redis_client.setex(
            cache_key,
            settings.compliance_cache_ttl,
            json.dumps(compliance_result, default=str)
        )
        
        # Auto-process eligible claims if requested
        if request.auto_process_eligible_claims and compliance_result['total_compensation'] > 0:
            background_tasks.add_task(
                auto_process_compensation_claims,
                compliance_result
            )
        
        # Publish compliance event
        await kafka_producer.send(
            "compliance-results",
            {
                "compliance_id": compliance_result['compliance_id'],
                "passenger_id": request.passenger_info.passenger_id,
                "flight_id": request.flight_info.flight_id,
                "total_compensation": compliance_result['total_compensation'],
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Update metrics
        processing_time = time.time() - start_time
        for regulation in request.regulations_to_check:
            COMPLIANCE_CHECKS.labels(regulation=regulation.value, status="completed").inc()
        COMPLIANCE_DURATION.observe(processing_time)
        
        compliance_result['processing_time_seconds'] = processing_time
        
        return ComplianceResult(**compliance_result)
        
    except Exception as e:
        # Update error metrics
        for regulation in request.regulations_to_check:
            COMPLIANCE_CHECKS.labels(regulation=regulation.value, status="failed").inc()
        
        logger.error("Compliance check failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Compliance check failed: {str(e)}")

@app.post("/api/v1/claims/submit", response_model=CompensationClaim)
async def submit_compensation_claim(
    passenger_id: str,
    flight_id: str,
    regulation_type: RegulationType,
    claim_reason: str,
    supporting_documents: List[str] = []
) -> CompensationClaim:
    """Submit a compensation claim"""
    try:
        # Get existing compliance result
        compliance_result = await db.get_compliance_result_by_flight_passenger(flight_id, passenger_id)
        
        if not compliance_result:
            raise HTTPException(
                status_code=404, 
                detail="No compliance assessment found for this flight and passenger"
            )
        
        # Check if claim is eligible
        eligible_compensation = compliance_result.get('eligible_compensation', {})
        regulation_compensation = eligible_compensation.get(regulation_type.value, 0)
        
        if regulation_compensation <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"No compensation available under {regulation_type.value} for this disruption"
            )
        
        # Create claim
        claim_data = {
            'claim_id': f"CLM_{uuid4().hex[:8].upper()}",
            'passenger_id': passenger_id,
            'flight_id': flight_id,
            'regulation_type': regulation_type,
            'compensation_amount': regulation_compensation,
            'claim_status': CompensationStatus.PENDING,
            'claim_reasons': [claim_reason],
            'supporting_documents': supporting_documents,
            'claim_deadline': datetime.utcnow() + timedelta(days=settings.claim_deadline_days),
            'submitted_at': datetime.utcnow()
        }
        
        claim_id = await db.store_compensation_claim(claim_data)
        claim_data['claim_id'] = claim_id
        
        # Update active claims metric
        ACTIVE_CLAIMS.inc()
        
        # Publish claim event
        await kafka_producer.send(
            "compensation-claims",
            {
                "claim_id": claim_id,
                "passenger_id": passenger_id,
                "flight_id": flight_id,
                "compensation_amount": regulation_compensation,
                "regulation_type": regulation_type.value,
                "status": "submitted",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(
            "Compensation claim submitted",
            claim_id=claim_id,
            passenger_id=passenger_id,
            compensation_amount=regulation_compensation
        )
        
        return CompensationClaim(**claim_data)
        
    except Exception as e:
        logger.error("Failed to submit claim", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to submit claim: {str(e)}")

@app.get("/api/v1/claims/{claim_id}", response_model=CompensationClaim)
async def get_compensation_claim(claim_id: str) -> CompensationClaim:
    """Get compensation claim by ID"""
    try:
        claim_data = await db.get_compensation_claim(claim_id)
        if not claim_data:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        return CompensationClaim(**claim_data)
        
    except Exception as e:
        logger.error("Failed to get claim", claim_id=claim_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get claim: {str(e)}")

@app.put("/api/v1/claims/{claim_id}/status")
async def update_claim_status(
    claim_id: str,
    new_status: CompensationStatus,
    processing_notes: Optional[str] = None,
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """Update claim status"""
    try:
        # Get existing claim
        claim_data = await db.get_compensation_claim(claim_id)
        if not claim_data:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        old_status = claim_data.get('claim_status')
        
        # Update status
        await db.update_claim_status(claim_id, new_status.value, processing_notes)
        
        # Update metrics based on status change
        if old_status == CompensationStatus.PENDING and new_status == CompensationStatus.PAID:
            COMPENSATION_ISSUED.labels(
                type="claim_payment",
                regulation=claim_data.get('regulation_type')
            ).inc()
            ACTIVE_CLAIMS.dec()
        
        # Send notifications
        if background_tasks:
            background_tasks.add_task(
                send_claim_status_notification,
                claim_id,
                old_status,
                new_status.value,
                processing_notes
            )
        
        # Publish status update event
        await kafka_producer.send(
            "claim-status-updates",
            {
                "claim_id": claim_id,
                "passenger_id": claim_data.get('passenger_id'),
                "old_status": old_status,
                "new_status": new_status.value,
                "processing_notes": processing_notes,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(
            "Claim status updated",
            claim_id=claim_id,
            old_status=old_status,
            new_status=new_status.value
        )
        
        return {
            "claim_id": claim_id,
            "old_status": old_status,
            "new_status": new_status.value,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to update claim status", claim_id=claim_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update claim status: {str(e)}")

@app.post("/api/v1/claims/{claim_id}/dispute")
async def submit_claim_dispute(
    claim_id: str,
    dispute_reason: str,
    supporting_evidence: List[str] = []
) -> ClaimDispute:
    """Submit a dispute for a compensation claim"""
    try:
        # Get existing claim
        claim_data = await db.get_compensation_claim(claim_id)
        if not claim_data:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        # Create dispute
        dispute_data = {
            'dispute_id': f"DSP_{uuid4().hex[:8].upper()}",
            'claim_id': claim_id,
            'passenger_id': claim_data.get('passenger_id'),
            'dispute_reason': dispute_reason,
            'supporting_evidence': supporting_evidence,
            'dispute_status': 'pending',
            'submitted_at': datetime.utcnow()
        }
        
        dispute_id = await db.store_claim_dispute(dispute_data)
        dispute_data['dispute_id'] = dispute_id
        
        # Update claim status to disputed
        await db.update_claim_status(claim_id, CompensationStatus.DISPUTED.value, "Dispute submitted")
        
        # Publish dispute event
        await kafka_producer.send(
            "claim-disputes",
            {
                "dispute_id": dispute_id,
                "claim_id": claim_id,
                "passenger_id": claim_data.get('passenger_id'),
                "dispute_reason": dispute_reason,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(
            "Claim dispute submitted",
            dispute_id=dispute_id,
            claim_id=claim_id
        )
        
        return ClaimDispute(**dispute_data)
        
    except Exception as e:
        logger.error("Failed to submit dispute", claim_id=claim_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to submit dispute: {str(e)}")

@app.get("/api/v1/regulations/{regulation_type}/rules")
async def get_regulation_rules(regulation_type: RegulationType) -> Dict[str, Any]:
    """Get detailed rules for a specific regulation"""
    try:
        if regulation_type == RegulationType.EU261:
            rules = await eu261_engine.get_regulation_details()
        elif regulation_type == RegulationType.UK_CAA:
            rules = await uk_caa_engine.get_regulation_details()
        elif regulation_type == RegulationType.US_DOT:
            rules = await dot_engine.get_regulation_details()
        elif regulation_type == RegulationType.IATA:
            rules = await iata_engine.get_regulation_details()
        else:
            raise HTTPException(status_code=404, detail="Regulation type not supported")
        
        return rules
        
    except Exception as e:
        logger.error("Failed to get regulation rules", regulation_type=regulation_type, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get rules: {str(e)}")

@app.get("/api/v1/compliance/batch-check")
async def batch_compliance_check(
    flight_id: str,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Perform compliance check for all passengers on a flight"""
    try:
        # Get all passengers on the flight
        passengers = await db.get_flight_passengers(flight_id)
        
        if not passengers:
            raise HTTPException(status_code=404, detail="No passengers found for this flight")
        
        # Queue batch processing
        background_tasks.add_task(
            process_batch_compliance_checks,
            flight_id,
            passengers
        )
        
        return {
            "message": f"Batch compliance check queued for flight {flight_id}",
            "passenger_count": len(passengers),
            "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to queue batch compliance check", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to queue batch check: {str(e)}")

@app.get("/api/v1/analytics/compliance-summary")
async def get_compliance_analytics() -> Dict[str, Any]:
    """Get compliance analytics and summary"""
    try:
        analytics = await db.get_compliance_analytics()
        return analytics
        
    except Exception as e:
        logger.error("Failed to get compliance analytics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

# Background tasks
async def process_compliance_events():
    """Process compliance-related events from Kafka"""
    try:
        async for msg in kafka_consumer:
            try:
                event_data = msg.value
                
                if msg.topic == "disruption-events":
                    await handle_disruption_event(event_data)
                elif msg.topic == "passenger-claims":
                    await handle_passenger_claim_event(event_data)
                elif msg.topic == "rebooking-requests":
                    await handle_rebooking_event(event_data)
                    
            except Exception as e:
                logger.error("Failed to process Kafka message", error=str(e))
                
    except Exception as e:
        logger.error("Kafka consumer failed", error=str(e))

async def handle_disruption_event(event_data: Dict[str, Any]):
    """Handle disruption event for automatic compliance processing"""
    try:
        disruption_id = event_data.get('disruption_id')
        flight_id = event_data.get('flight_id')
        
        # Get affected passengers
        passengers = await db.get_flight_passengers(flight_id)
        
        # Process compliance for high-impact disruptions
        delay_minutes = event_data.get('estimated_delay_minutes', 0)
        if delay_minutes >= 180:  # 3+ hours
            for passenger in passengers:
                asyncio.create_task(
                    auto_compliance_check(flight_id, passenger, event_data)
                )
        
        logger.info(
            "Disruption event processed for compliance",
            disruption_id=disruption_id,
            passenger_count=len(passengers)
        )
        
    except Exception as e:
        logger.error("Failed to handle disruption event", error=str(e))

async def auto_compliance_check(flight_id: str, passenger: Dict[str, Any], disruption_data: Dict[str, Any]):
    """Perform automatic compliance check for passenger"""
    try:
        # Create compliance request
        request_data = await compliance_engine.create_compliance_request_from_disruption(
            flight_id, passenger, disruption_data
        )
        
        # Perform compliance check
        compliance_result = await compliance_engine.check_compliance(**request_data)
        
        # Store result
        await db.store_compliance_result(compliance_result)
        
        # Auto-submit eligible claims
        if compliance_result['total_compensation'] > 0:
            await auto_process_compensation_claims(compliance_result)
        
    except Exception as e:
        logger.error("Auto compliance check failed", passenger_id=passenger.get('id'), error=str(e))

async def auto_process_compensation_claims(compliance_result: Dict[str, Any]):
    """Automatically process eligible compensation claims"""
    try:
        passenger_id = compliance_result['passenger_id']
        flight_id = compliance_result['flight_id']
        
        eligible_compensation = compliance_result.get('eligible_compensation', {})
        
        for regulation, amount in eligible_compensation.items():
            if amount > 0:
                # Auto-submit claim
                claim_data = {
                    'claim_id': f"AUTO_{uuid4().hex[:8].upper()}",
                    'passenger_id': passenger_id,
                    'flight_id': flight_id,
                    'regulation_type': regulation,
                    'compensation_amount': amount,
                    'claim_status': CompensationStatus.APPROVED,  # Auto-approved
                    'claim_reasons': ['Automatic processing based on compliance assessment'],
                    'supporting_documents': [],
                    'claim_deadline': datetime.utcnow() + timedelta(days=30),
                    'submitted_at': datetime.utcnow(),
                    'processed_at': datetime.utcnow()
                }
                
                await db.store_compensation_claim(claim_data)
                
                # Update metrics
                COMPENSATION_ISSUED.labels(
                    type="auto_processing",
                    regulation=regulation
                ).inc()
                
                logger.info(
                    "Auto-processed compensation claim",
                    claim_id=claim_data['claim_id'],
                    passenger_id=passenger_id,
                    amount=amount,
                    regulation=regulation
                )
        
    except Exception as e:
        logger.error("Auto claim processing failed", error=str(e))

async def process_batch_compliance_checks(flight_id: str, passengers: List[Dict[str, Any]]):
    """Process compliance checks for multiple passengers"""
    try:
        # Get flight and disruption information
        flight_info = await db.get_flight_info(flight_id)
        disruption_info = await db.get_flight_disruption(flight_id)
        
        for passenger in passengers:
            try:
                # Create compliance request
                request_data = {
                    'flight_info': flight_info,
                    'passenger_info': passenger,
                    'disruption_info': disruption_info,
                    'regulations_to_check': [RegulationType.EU261, RegulationType.UK_CAA]
                }
                
                # Perform compliance check
                compliance_result = await compliance_engine.check_compliance(**request_data)
                
                # Store result
                await db.store_compliance_result(compliance_result)
                
                # Auto-process if eligible
                if compliance_result['total_compensation'] > 0:
                    await auto_process_compensation_claims(compliance_result)
                
            except Exception as e:
                logger.error(
                    "Failed to process passenger in batch",
                    passenger_id=passenger.get('id'),
                    error=str(e)
                )
        
        logger.info(
            "Batch compliance processing completed",
            flight_id=flight_id,
            passenger_count=len(passengers)
        )
        
    except Exception as e:
        logger.error("Batch compliance processing failed", flight_id=flight_id, error=str(e))

async def send_claim_status_notification(
    claim_id: str,
    old_status: str,
    new_status: str,
    processing_notes: Optional[str]
):
    """Send notification about claim status update"""
    try:
        # Get claim details
        claim_data = await db.get_compensation_claim(claim_id)
        
        notification_data = {
            'passenger_id': claim_data.get('passenger_id'),
            'type': 'claim_status_update',
            'subject': f'Compensation Claim Update - {claim_id}',
            'message': f'Your claim status has been updated from {old_status} to {new_status}',
            'claim_details': {
                'claim_id': claim_id,
                'old_status': old_status,
                'new_status': new_status,
                'processing_notes': processing_notes,
                'compensation_amount': claim_data.get('compensation_amount')
            }
        }
        
        # Send via notification service
        await kafka_producer.send("passenger-notifications", notification_data)
        
        logger.info("Claim status notification sent", claim_id=claim_id)
        
    except Exception as e:
        logger.error("Failed to send claim notification", claim_id=claim_id, error=str(e))

async def handle_passenger_claim_event(event_data: Dict[str, Any]):
    """Handle passenger claim events"""
    try:
        # Process passenger-initiated claim events
        claim_type = event_data.get('claim_type')
        
        if claim_type == 'compensation_request':
            await process_passenger_compensation_request(event_data)
        
    except Exception as e:
        logger.error("Failed to handle passenger claim event", error=str(e))

async def handle_rebooking_event(event_data: Dict[str, Any]):
    """Handle rebooking events for compliance tracking"""
    try:
        # Track rebookings for compliance purposes
        passenger_id = event_data.get('passenger_id')
        original_flight_id = event_data.get('original_flight_id')
        
        # Check if rebooking affects existing compliance assessments
        compliance_result = await db.get_compliance_result_by_flight_passenger(
            original_flight_id, passenger_id
        )
        
        if compliance_result:
            # Update compliance record with rebooking information
            await db.update_compliance_with_rebooking(
                compliance_result['compliance_id'],
                event_data
            )
        
    except Exception as e:
        logger.error("Failed to handle rebooking event", error=str(e))

async def process_passenger_compensation_request(event_data: Dict[str, Any]):
    """Process passenger-initiated compensation request"""
    try:
        passenger_id = event_data.get('passenger_id')
        flight_id = event_data.get('flight_id')
        
        # Check existing compliance assessment
        existing_assessment = await db.get_compliance_result_by_flight_passenger(
            flight_id, passenger_id
        )
        
        if not existing_assessment:
            # Trigger new compliance assessment
            await auto_compliance_check(flight_id, {'id': passenger_id}, event_data)
        
    except Exception as e:
        logger.error("Failed to process compensation request", error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)