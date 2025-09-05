import asyncio
import asyncpg
import structlog
from typing import Dict, List, Optional, Any
from datetime import datetime
from config import settings

logger = structlog.get_logger()

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                settings.database_url,
                min_size=5,
                max_size=settings.connection_pool_size,
                command_timeout=60
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error("Failed to create database connection pool", error=str(e))
            raise
    
    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query and return status"""
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)
    
    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch multiple rows"""
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch single row"""
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def get_passenger(self, passenger_id: str) -> Optional[Dict[str, Any]]:
        """Get passenger information"""
        query = """
        SELECT passenger_id, pnr, first_name, last_name, email, phone, 
               nationality, created_at, updated_at
        FROM passengers 
        WHERE passenger_id = $1
        """
        return await self.fetchrow(query, passenger_id)
    
    async def get_flight_passengers(self, flight_id: str) -> List[Dict[str, Any]]:
        """Get all passengers for a flight"""
        query = """
        SELECT p.passenger_id, p.pnr, p.first_name, p.last_name, p.email, p.phone,
               p.nationality, b.seat_number, b.booking_class
        FROM passengers p
        JOIN bookings b ON p.passenger_id = b.passenger_id
        WHERE b.flight_id = $1
        """
        return await self.fetch(query, flight_id)
    
    async def store_notification(
        self,
        notification_id: str,
        passenger_id: str,
        notification_type: str,
        channels: List[str],
        priority: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        send_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        template_id: Optional[str] = None
    ) -> None:
        """Store notification in database"""
        query = """
        INSERT INTO notifications (
            notification_id, passenger_id, notification_type, channels, priority,
            title, message, data, send_at, expires_at, template_id, status, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """
        
        await self.execute(
            query,
            notification_id,
            passenger_id,
            notification_type,
            channels,
            priority,
            title,
            message,
            data,
            send_at or datetime.utcnow(),
            expires_at,
            template_id,
            'pending',
            datetime.utcnow()
        )
    
    async def update_notification_status(
        self,
        notification_id: str,
        status: str,
        channels_status: Optional[Dict[str, str]] = None,
        sent_at: Optional[datetime] = None,
        delivered_at: Optional[datetime] = None,
        failed_reason: Optional[str] = None
    ) -> None:
        """Update notification status"""
        query = """
        UPDATE notifications 
        SET status = $2, channels_status = $3, sent_at = $4, 
            delivered_at = $5, failed_reason = $6, updated_at = $7
        WHERE notification_id = $1
        """
        
        await self.execute(
            query,
            notification_id,
            status,
            channels_status,
            sent_at,
            delivered_at,
            failed_reason,
            datetime.utcnow()
        )
    
    async def get_notification_status(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """Get notification status"""
        query = """
        SELECT notification_id, status, channels_status, sent_at, 
               delivered_at, read_at, failed_reason
        FROM notifications
        WHERE notification_id = $1
        """
        return await self.fetchrow(query, notification_id)
    
    async def get_passenger_preferences(self, passenger_id: str) -> Optional[Dict[str, Any]]:
        """Get passenger notification preferences"""
        query = """
        SELECT passenger_id, enabled_channels, quiet_hours_start, quiet_hours_end,
               timezone, language, email_preferences, sms_preferences,
               whatsapp_preferences, push_preferences, created_at, updated_at
        FROM notification_preferences
        WHERE passenger_id = $1
        """
        return await self.fetchrow(query, passenger_id)
    
    async def update_passenger_preferences(
        self,
        passenger_id: str,
        preferences: Dict[str, Any]
    ) -> None:
        """Update passenger notification preferences"""
        query = """
        INSERT INTO notification_preferences (
            passenger_id, enabled_channels, quiet_hours_start, quiet_hours_end,
            timezone, language, email_preferences, sms_preferences,
            whatsapp_preferences, push_preferences, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        ON CONFLICT (passenger_id) 
        DO UPDATE SET 
            enabled_channels = $2,
            quiet_hours_start = $3,
            quiet_hours_end = $4,
            timezone = $5,
            language = $6,
            email_preferences = $7,
            sms_preferences = $8,
            whatsapp_preferences = $9,
            push_preferences = $10,
            updated_at = $12
        """
        
        await self.execute(
            query,
            passenger_id,
            preferences.get('enabled_channels', ['email', 'sms']),
            preferences.get('quiet_hours_start', '22:00'),
            preferences.get('quiet_hours_end', '07:00'),
            preferences.get('timezone', 'UTC'),
            preferences.get('language', 'en'),
            preferences.get('email_preferences', {}),
            preferences.get('sms_preferences', {}),
            preferences.get('whatsapp_preferences', {}),
            preferences.get('push_preferences', {}),
            datetime.utcnow(),
            datetime.utcnow()
        )
    
    async def get_notification_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get notification statistics for the last N days"""
        query = """
        SELECT 
            COUNT(*) as total_notifications,
            COUNT(CASE WHEN status = 'sent' THEN 1 END) as sent_notifications,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_notifications,
            COUNT(CASE WHEN status = 'delivered' THEN 1 END) as delivered_notifications,
            notification_type,
            DATE(created_at) as date
        FROM notifications
        WHERE created_at >= NOW() - INTERVAL '%s days'
        GROUP BY notification_type, DATE(created_at)
        ORDER BY date DESC
        """ % days
        
        return await self.fetch(query)
    
    async def get_channel_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get channel-specific statistics"""
        query = """
        SELECT 
            unnest(channels) as channel,
            COUNT(*) as total_sent,
            COUNT(CASE WHEN status = 'sent' THEN 1 END) as successful_sent,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_sent,
            AVG(EXTRACT(EPOCH FROM (sent_at - created_at))) as avg_delivery_time_seconds
        FROM notifications
        WHERE created_at >= NOW() - INTERVAL '%s days'
        GROUP BY channel
        """ % days
        
        return await self.fetch(query)
    
    async def get_pending_notifications(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get pending notifications to process"""
        query = """
        SELECT notification_id, passenger_id, notification_type, channels, priority,
               title, message, data, send_at, expires_at, template_id
        FROM notifications
        WHERE status = 'pending' 
        AND (send_at IS NULL OR send_at <= NOW())
        AND (expires_at IS NULL OR expires_at > NOW())
        ORDER BY 
            CASE priority
                WHEN 'urgent' THEN 1
                WHEN 'high' THEN 2
                WHEN 'normal' THEN 3
                WHEN 'low' THEN 4
            END,
            created_at ASC
        LIMIT $1
        """
        return await self.fetch(query, limit)
    
    async def get_notification_templates(self, language: str = 'en') -> List[Dict[str, Any]]:
        """Get notification templates for a language"""
        query = """
        SELECT template_id, template_type, language, subject_template, 
               body_template, variables, created_at
        FROM notification_templates
        WHERE language = $1 OR language = 'en'
        ORDER BY 
            CASE WHEN language = $1 THEN 1 ELSE 2 END,
            template_type
        """
        return await self.fetch(query, language)
    
    async def create_notification_log(
        self,
        notification_id: str,
        channel: str,
        status: str,
        response_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Create notification delivery log entry"""
        query = """
        INSERT INTO notification_logs (
            log_id, notification_id, channel, status, response_data, 
            error_message, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        
        log_id = f"{notification_id}_{channel}_{datetime.utcnow().isoformat()}"
        
        await self.execute(
            query,
            log_id,
            notification_id,
            channel,
            status,
            response_data,
            error_message,
            datetime.utcnow()
        )