from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio
import structlog
from datetime import datetime, timedelta
from uuid import uuid4
import redis.asyncio as redis
import httpx
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import json
from contextlib import asynccontextmanager
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from config import settings
from database import Database
from notification_engine import NotificationEngine
from channels import SMSChannel, EmailChannel, WhatsAppChannel, PushChannel

# Prometheus metrics
NOTIFICATIONS_SENT = Counter('notifications_sent_total', 'Total notifications sent', ['channel', 'type', 'status'])
NOTIFICATION_LATENCY = Histogram('notification_latency_seconds', 'Notification processing latency', ['channel'])
ACTIVE_NOTIFICATIONS = Gauge('active_notifications', 'Currently active notifications')
NOTIFICATION_ERRORS = Counter('notification_errors_total', 'Notification errors', ['channel', 'error_type'])

logger = structlog.get_logger()

# Pydantic models
class NotificationChannel(str, Enum):
    SMS = "sms"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    PUSH = "push"
    ALL = "all"

class NotificationType(str, Enum):
    DISRUPTION_ALERT = "disruption_alert"
    REBOOKING_CONFIRMATION = "rebooking_confirmation"
    BOARDING_REMINDER = "boarding_reminder"
    GATE_CHANGE = "gate_change"
    DELAY_UPDATE = "delay_update"
    CANCELLATION = "cancellation"
    COMPENSATION_AVAILABLE = "compensation_available"
    CARE_VOUCHER = "care_voucher"

class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NotificationRequest(BaseModel):
    passenger_id: str
    notification_type: NotificationType
    channels: List[NotificationChannel]
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    send_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    template_id: Optional[str] = None

class BulkNotificationRequest(BaseModel):
    passenger_ids: List[str]
    notification_type: NotificationType
    channels: List[NotificationChannel]
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    template_id: Optional[str] = None

class NotificationResult(BaseModel):
    notification_id: str
    passenger_id: str
    channels_sent: Dict[str, bool]
    channels_failed: Dict[str, str]
    total_sent: int
    total_failed: int
    processing_time_ms: float
    status: str
    created_at: datetime

class NotificationStatus(BaseModel):
    notification_id: str
    status: str
    channels_status: Dict[str, str]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    failed_reason: Optional[str]

class NotificationPreferences(BaseModel):
    passenger_id: str
    enabled_channels: List[NotificationChannel] = [NotificationChannel.EMAIL, NotificationChannel.SMS]
    quiet_hours_start: Optional[str] = "22:00"
    quiet_hours_end: Optional[str] = "07:00"
    timezone: str = "UTC"
    language: str = "en"
    email_preferences: Dict[str, bool] = {
        "marketing": False,
        "operational": True,
        "compensation": True,
        "disruptions": True
    }

# Global variables
db: Optional[Database] = None
redis_client: Optional[redis.Redis] = None
http_client: Optional[httpx.AsyncClient] = None
kafka_producer: Optional[AIOKafkaProducer] = None
kafka_consumer: Optional[AIOKafkaConsumer] = None
notification_engine: Optional[NotificationEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db, redis_client, http_client, kafka_producer, kafka_consumer, notification_engine
    
    try:
        # Initialize database
        db = Database()
        await db.connect()
        logger.info("Database connected successfully")
        
        # Initialize Redis
        redis_client = redis.from_url(settings.redis_url)
        await redis_client.ping()
        logger.info("Redis connected successfully")
        
        # Initialize HTTP client
        http_client = httpx.AsyncClient(timeout=30.0)
        logger.info("HTTP client initialized")
        
        # Initialize Kafka producer
        kafka_producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda x: json.dumps(x).encode()
        )
        await kafka_producer.start()
        logger.info("Kafka producer started")
        
        # Initialize notification channels
        channels = {
            'sms': SMSChannel(
                provider_url=settings.sms_provider_url,
                api_key=settings.sms_api_key,
                http_client=http_client
            ),
            'email': EmailChannel(
                smtp_host=settings.smtp_host,
                smtp_port=settings.smtp_port,
                username=settings.smtp_username,
                password=settings.smtp_password,
                http_client=http_client
            ),
            'whatsapp': WhatsAppChannel(
                provider_url=settings.whatsapp_provider_url,
                api_key=settings.whatsapp_api_key,
                http_client=http_client
            ),
            'push': PushChannel(
                firebase_key=settings.firebase_server_key,
                apns_key=settings.apns_key,
                http_client=http_client
            )
        }
        
        # Initialize notification engine
        notification_engine = NotificationEngine(
            db=db,
            redis_client=redis_client,
            kafka_producer=kafka_producer,
            channels=channels
        )
        
        # Start background notification processor
        asyncio.create_task(notification_engine.start_processor())
        
        logger.info("Notification service started successfully")
        
    except Exception as e:
        logger.error("Failed to start notification service", error=str(e))
        raise
    
    yield
    
    # Shutdown
    try:
        if kafka_producer:
            await kafka_producer.stop()
        if db:
            await db.disconnect()
        if redis_client:
            await redis_client.aclose()
        if http_client:
            await http_client.aclose()
        logger.info("Notification service shutdown completed")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))

# FastAPI app
app = FastAPI(
    title="Flight Disruption Notification Service",
    description="Multi-channel passenger notification service for flight disruptions",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        await db.execute("SELECT 1")
        
        # Check Redis
        await redis_client.ping()
        
        # Check notification engine
        engine_status = await notification_engine.get_health_status()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "services": {
                "database": "healthy",
                "redis": "healthy",
                "notification_engine": engine_status,
                "channels": await notification_engine.get_channels_status()
            }
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@app.post("/api/v1/notifications", response_model=NotificationResult)
async def send_notification(
    request: NotificationRequest,
    background_tasks: BackgroundTasks
) -> NotificationResult:
    """Send notification to a single passenger"""
    
    start_time = datetime.utcnow()
    notification_id = str(uuid4())
    
    try:
        logger.info(
            "Processing notification request",
            notification_id=notification_id,
            passenger_id=request.passenger_id,
            channels=request.channels,
            notification_type=request.notification_type
        )
        
        # Validate passenger exists
        passenger = await db.get_passenger(request.passenger_id)
        if not passenger:
            raise HTTPException(status_code=404, detail="Passenger not found")
        
        # Process notification
        result = await notification_engine.send_notification(
            notification_id=notification_id,
            passenger_id=request.passenger_id,
            notification_type=request.notification_type,
            channels=request.channels,
            priority=request.priority,
            title=request.title,
            message=request.message,
            data=request.data,
            send_at=request.send_at,
            expires_at=request.expires_at,
            template_id=request.template_id
        )
        
        # Update metrics
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        for channel in request.channels:
            channel_success = result['channels_sent'].get(channel.value, False)
            status = 'success' if channel_success else 'failed'
            NOTIFICATIONS_SENT.labels(
                channel=channel.value,
                type=request.notification_type.value,
                status=status
            ).inc()
            NOTIFICATION_LATENCY.labels(channel=channel.value).observe(processing_time)
        
        logger.info(
            "Notification processed successfully",
            notification_id=notification_id,
            processing_time_ms=processing_time * 1000,
            channels_sent=result['total_sent']
        )
        
        return NotificationResult(
            notification_id=notification_id,
            passenger_id=request.passenger_id,
            channels_sent=result['channels_sent'],
            channels_failed=result['channels_failed'],
            total_sent=result['total_sent'],
            total_failed=result['total_failed'],
            processing_time_ms=processing_time * 1000,
            status=result['status'],
            created_at=start_time
        )
        
    except Exception as e:
        logger.error(
            "Failed to process notification",
            notification_id=notification_id,
            error=str(e)
        )
        NOTIFICATION_ERRORS.labels(
            channel="unknown",
            error_type=type(e).__name__
        ).inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/notifications/bulk")
async def send_bulk_notifications(
    request: BulkNotificationRequest,
    background_tasks: BackgroundTasks
):
    """Send notifications to multiple passengers"""
    
    try:
        logger.info(
            "Processing bulk notification request",
            passenger_count=len(request.passenger_ids),
            channels=request.channels,
            notification_type=request.notification_type
        )
        
        # Process in background
        background_tasks.add_task(
            notification_engine.send_bulk_notifications,
            passenger_ids=request.passenger_ids,
            notification_type=request.notification_type,
            channels=request.channels,
            priority=request.priority,
            title=request.title,
            message=request.message,
            data=request.data,
            template_id=request.template_id
        )
        
        return {
            "message": "Bulk notification processing started",
            "passenger_count": len(request.passenger_ids),
            "estimated_completion": datetime.utcnow() + timedelta(minutes=5)
        }
        
    except Exception as e:
        logger.error("Failed to process bulk notification", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/notifications/{notification_id}/status", response_model=NotificationStatus)
async def get_notification_status(notification_id: str) -> NotificationStatus:
    """Get notification delivery status"""
    
    try:
        status = await notification_engine.get_notification_status(notification_id)
        if not status:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return NotificationStatus(**status)
        
    except Exception as e:
        logger.error("Failed to get notification status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/passengers/{passenger_id}/preferences", response_model=NotificationPreferences)
async def get_notification_preferences(passenger_id: str) -> NotificationPreferences:
    """Get passenger notification preferences"""
    
    try:
        preferences = await notification_engine.get_passenger_preferences(passenger_id)
        if not preferences:
            # Return default preferences
            return NotificationPreferences(passenger_id=passenger_id)
        
        return NotificationPreferences(**preferences)
        
    except Exception as e:
        logger.error("Failed to get notification preferences", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/passengers/{passenger_id}/preferences")
async def update_notification_preferences(
    passenger_id: str,
    preferences: NotificationPreferences
):
    """Update passenger notification preferences"""
    
    try:
        await notification_engine.update_passenger_preferences(
            passenger_id=passenger_id,
            preferences=preferences.dict()
        )
        
        return {"message": "Preferences updated successfully"}
        
    except Exception as e:
        logger.error("Failed to update notification preferences", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/notifications/disruption")
async def send_disruption_notification(
    flight_id: str,
    disruption_data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Send disruption notifications to all affected passengers"""
    
    try:
        logger.info(
            "Processing disruption notification",
            flight_id=flight_id,
            disruption_type=disruption_data.get('type')
        )
        
        # Process in background
        background_tasks.add_task(
            notification_engine.handle_disruption_notification,
            flight_id=flight_id,
            disruption_data=disruption_data
        )
        
        return {
            "message": "Disruption notification processing started",
            "flight_id": flight_id
        }
        
    except Exception as e:
        logger.error("Failed to process disruption notification", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/notifications/stats")
async def get_notification_stats():
    """Get notification statistics"""
    
    try:
        stats = await notification_engine.get_statistics()
        return stats
        
    except Exception as e:
        logger.error("Failed to get notification stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/notifications/test")
async def test_notification_channels():
    """Test all notification channels"""
    
    try:
        results = await notification_engine.test_all_channels()
        return results
        
    except Exception as e:
        logger.error("Failed to test notification channels", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005, workers=1)