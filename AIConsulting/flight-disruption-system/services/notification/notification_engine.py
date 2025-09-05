import asyncio
import structlog
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4
import redis.asyncio as redis
import json
from aiokafka import AIOKafkaProducer
from database import Database
from config import settings
from template_manager import TemplateManager

logger = structlog.get_logger()

class NotificationEngine:
    """Core notification engine that orchestrates multi-channel notifications"""
    
    def __init__(
        self,
        db: Database,
        redis_client: redis.Redis,
        kafka_producer: AIOKafkaProducer,
        channels: Dict[str, Any]
    ):
        self.db = db
        self.redis = redis_client
        self.kafka_producer = kafka_producer
        self.channels = channels
        self.template_manager = TemplateManager(db, redis_client)
        self.processing = False
        
    async def start_processor(self):
        """Start background notification processor"""
        if self.processing:
            return
            
        self.processing = True
        logger.info("Starting notification processor")
        
        while self.processing:
            try:
                await self._process_pending_notifications()
                await asyncio.sleep(1)  # Process every second
            except Exception as e:
                logger.error("Error in notification processor", error=str(e))
                await asyncio.sleep(5)  # Wait before retry
    
    async def stop_processor(self):
        """Stop background notification processor"""
        self.processing = False
        logger.info("Notification processor stopped")
    
    async def send_notification(
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
    ) -> Dict[str, Any]:
        """Send notification through specified channels"""
        
        try:
            # Get passenger information
            passenger = await self.db.get_passenger(passenger_id)
            if not passenger:
                raise ValueError(f"Passenger {passenger_id} not found")
            
            # Get passenger preferences
            preferences = await self.db.get_passenger_preferences(passenger_id)
            if preferences:
                # Filter channels based on preferences
                enabled_channels = preferences.get('enabled_channels', channels)
                channels = [ch for ch in channels if ch in enabled_channels]
            
            # Check quiet hours if applicable
            if preferences and not self._is_priority_override(priority):
                if self._is_quiet_hours(preferences):
                    # Schedule for later unless urgent
                    if priority not in ['urgent', 'high']:
                        send_at = self._get_next_active_time(preferences)
            
            # Store notification
            await self.db.store_notification(
                notification_id=notification_id,
                passenger_id=passenger_id,
                notification_type=notification_type,
                channels=channels,
                priority=priority,
                title=title,
                message=message,
                data=data,
                send_at=send_at,
                expires_at=expires_at,
                template_id=template_id
            )
            
            # If immediate send
            if not send_at or send_at <= datetime.utcnow():
                return await self._send_notification_now(
                    notification_id=notification_id,
                    passenger=passenger,
                    channels=channels,
                    title=title,
                    message=message,
                    data=data,
                    template_id=template_id,
                    preferences=preferences
                )
            else:
                # Add to scheduled queue
                await self._schedule_notification(notification_id, send_at)
                return {
                    'channels_sent': {},
                    'channels_failed': {},
                    'total_sent': 0,
                    'total_failed': 0,
                    'status': 'scheduled'
                }
                
        except Exception as e:
            logger.error("Failed to send notification", error=str(e))
            await self.db.update_notification_status(
                notification_id=notification_id,
                status='failed',
                failed_reason=str(e)
            )
            raise
    
    async def _send_notification_now(
        self,
        notification_id: str,
        passenger: Dict[str, Any],
        channels: List[str],
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        template_id: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send notification immediately"""
        
        channels_sent = {}
        channels_failed = {}
        
        # Prepare notification content
        if template_id:
            content = await self.template_manager.render_template(
                template_id=template_id,
                language=preferences.get('language', 'en') if preferences else 'en',
                variables={'passenger': passenger, 'data': data or {}}
            )
            title = content.get('subject', title)
            message = content.get('body', message)
        
        # Send through each channel
        for channel in channels:
            if channel not in self.channels:
                channels_failed[channel] = f"Channel {channel} not available"
                continue
            
            try:
                channel_impl = self.channels[channel]
                success = await channel_impl.send(
                    passenger=passenger,
                    title=title,
                    message=message,
                    data=data
                )
                
                if success:
                    channels_sent[channel] = True
                    await self.db.create_notification_log(
                        notification_id=notification_id,
                        channel=channel,
                        status='sent',
                        response_data={'success': True}
                    )
                else:
                    channels_failed[channel] = "Channel send failed"
                    await self.db.create_notification_log(
                        notification_id=notification_id,
                        channel=channel,
                        status='failed',
                        error_message="Channel send failed"
                    )
                    
            except Exception as e:
                error_msg = str(e)
                channels_failed[channel] = error_msg
                await self.db.create_notification_log(
                    notification_id=notification_id,
                    channel=channel,
                    status='failed',
                    error_message=error_msg
                )
                logger.error(
                    "Channel send failed",
                    notification_id=notification_id,
                    channel=channel,
                    error=error_msg
                )
        
        # Update notification status
        total_sent = len(channels_sent)
        total_failed = len(channels_failed)
        
        if total_sent > 0:
            status = 'sent' if total_failed == 0 else 'partial'
        else:
            status = 'failed'
        
        await self.db.update_notification_status(
            notification_id=notification_id,
            status=status,
            channels_status={**channels_sent, **channels_failed},
            sent_at=datetime.utcnow()
        )
        
        # Publish to Kafka for downstream processing
        await self._publish_notification_event(
            notification_id=notification_id,
            status=status,
            channels_sent=channels_sent,
            channels_failed=channels_failed
        )
        
        return {
            'channels_sent': channels_sent,
            'channels_failed': channels_failed,
            'total_sent': total_sent,
            'total_failed': total_failed,
            'status': status
        }
    
    async def send_bulk_notifications(
        self,
        passenger_ids: List[str],
        notification_type: str,
        channels: List[str],
        priority: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        template_id: Optional[str] = None
    ):
        """Send notifications to multiple passengers"""
        
        logger.info(
            "Processing bulk notifications",
            passenger_count=len(passenger_ids),
            notification_type=notification_type
        )
        
        semaphore = asyncio.Semaphore(settings.max_concurrent_notifications)
        
        async def send_single(passenger_id: str):
            async with semaphore:
                try:
                    notification_id = str(uuid4())
                    await self.send_notification(
                        notification_id=notification_id,
                        passenger_id=passenger_id,
                        notification_type=notification_type,
                        channels=channels,
                        priority=priority,
                        title=title,
                        message=message,
                        data=data,
                        template_id=template_id
                    )
                except Exception as e:
                    logger.error(
                        "Failed to send bulk notification",
                        passenger_id=passenger_id,
                        error=str(e)
                    )
        
        # Process in batches
        batch_size = settings.batch_size
        for i in range(0, len(passenger_ids), batch_size):
            batch = passenger_ids[i:i + batch_size]
            tasks = [send_single(pid) for pid in batch]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Small delay between batches
            if i + batch_size < len(passenger_ids):
                await asyncio.sleep(0.1)
        
        logger.info("Bulk notifications processing completed")
    
    async def handle_disruption_notification(
        self,
        flight_id: str,
        disruption_data: Dict[str, Any]
    ):
        """Handle disruption notification for all affected passengers"""
        
        try:
            # Get affected passengers
            passengers = await self.db.get_flight_passengers(flight_id)
            logger.info(
                "Processing disruption notification",
                flight_id=flight_id,
                passenger_count=len(passengers)
            )
            
            # Determine notification content based on disruption type
            disruption_type = disruption_data.get('type', 'unknown')
            delay_minutes = disruption_data.get('delay_minutes', 0)
            
            title, message = self._generate_disruption_message(
                disruption_type=disruption_type,
                delay_minutes=delay_minutes,
                flight_id=flight_id
            )
            
            # Send to all passengers
            passenger_ids = [p['passenger_id'] for p in passengers]
            
            await self.send_bulk_notifications(
                passenger_ids=passenger_ids,
                notification_type='disruption_alert',
                channels=['sms', 'email', 'push'],
                priority='high' if delay_minutes > 120 else 'normal',
                title=title,
                message=message,
                data=disruption_data,
                template_id='disruption_alert'
            )
            
        except Exception as e:
            logger.error("Failed to handle disruption notification", error=str(e))
            raise
    
    async def get_notification_status(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """Get notification delivery status"""
        return await self.db.get_notification_status(notification_id)
    
    async def get_passenger_preferences(self, passenger_id: str) -> Optional[Dict[str, Any]]:
        """Get passenger notification preferences"""
        return await self.db.get_passenger_preferences(passenger_id)
    
    async def update_passenger_preferences(
        self,
        passenger_id: str,
        preferences: Dict[str, Any]
    ):
        """Update passenger notification preferences"""
        await self.db.update_passenger_preferences(passenger_id, preferences)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get notification statistics"""
        stats = await self.db.get_notification_statistics()
        channel_stats = await self.db.get_channel_statistics()
        
        return {
            'general_statistics': stats,
            'channel_statistics': channel_stats,
            'system_status': await self.get_health_status()
        }
    
    async def get_health_status(self) -> str:
        """Get notification engine health status"""
        try:
            # Check if processor is running
            if not self.processing:
                return "stopped"
            
            # Check channel health
            unhealthy_channels = []
            for name, channel in self.channels.items():
                if hasattr(channel, 'health_check'):
                    if not await channel.health_check():
                        unhealthy_channels.append(name)
            
            if unhealthy_channels:
                return f"degraded ({', '.join(unhealthy_channels)} unhealthy)"
            
            return "healthy"
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return "unhealthy"
    
    async def get_channels_status(self) -> Dict[str, str]:
        """Get status of all notification channels"""
        status = {}
        
        for name, channel in self.channels.items():
            try:
                if hasattr(channel, 'health_check'):
                    healthy = await channel.health_check()
                    status[name] = "healthy" if healthy else "unhealthy"
                else:
                    status[name] = "unknown"
            except Exception as e:
                status[name] = f"error: {str(e)}"
        
        return status
    
    async def test_all_channels(self) -> Dict[str, Any]:
        """Test all notification channels"""
        results = {}
        
        for name, channel in self.channels.items():
            try:
                if hasattr(channel, 'test'):
                    result = await channel.test()
                    results[name] = {"status": "success", "result": result}
                else:
                    results[name] = {"status": "no_test_method", "result": None}
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
        
        return results
    
    async def _process_pending_notifications(self):
        """Process pending notifications from queue"""
        notifications = await self.db.get_pending_notifications(limit=settings.batch_size)
        
        if not notifications:
            return
        
        logger.debug(f"Processing {len(notifications)} pending notifications")
        
        for notification in notifications:
            try:
                passenger = await self.db.get_passenger(notification['passenger_id'])
                if not passenger:
                    await self.db.update_notification_status(
                        notification['notification_id'],
                        'failed',
                        failed_reason='Passenger not found'
                    )
                    continue
                
                await self._send_notification_now(
                    notification_id=notification['notification_id'],
                    passenger=passenger,
                    channels=notification['channels'],
                    title=notification['title'],
                    message=notification['message'],
                    data=notification['data'],
                    template_id=notification['template_id']
                )
                
            except Exception as e:
                logger.error(
                    "Failed to process pending notification",
                    notification_id=notification['notification_id'],
                    error=str(e)
                )
                await self.db.update_notification_status(
                    notification['notification_id'],
                    'failed',
                    failed_reason=str(e)
                )
    
    async def _schedule_notification(self, notification_id: str, send_at: datetime):
        """Schedule notification for later processing"""
        delay_seconds = (send_at - datetime.utcnow()).total_seconds()
        
        await self.redis.zadd(
            settings.scheduled_queue,
            {notification_id: send_at.timestamp()}
        )
        
        logger.info(
            "Notification scheduled",
            notification_id=notification_id,
            send_at=send_at,
            delay_seconds=delay_seconds
        )
    
    async def _publish_notification_event(
        self,
        notification_id: str,
        status: str,
        channels_sent: Dict[str, bool],
        channels_failed: Dict[str, str]
    ):
        """Publish notification event to Kafka"""
        try:
            event = {
                'notification_id': notification_id,
                'status': status,
                'channels_sent': channels_sent,
                'channels_failed': channels_failed,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await self.kafka_producer.send(
                settings.kafka_notification_topic,
                value=event
            )
            
        except Exception as e:
            logger.error("Failed to publish notification event", error=str(e))
    
    def _generate_disruption_message(
        self,
        disruption_type: str,
        delay_minutes: int,
        flight_id: str
    ) -> tuple:
        """Generate disruption notification message"""
        
        if disruption_type == 'cancellation':
            title = f"Flight {flight_id} Cancelled"
            message = f"We regret to inform you that flight {flight_id} has been cancelled. We are rebooking you automatically."
        elif disruption_type == 'delay':
            hours = delay_minutes // 60
            minutes = delay_minutes % 60
            
            if hours > 0:
                delay_text = f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
            else:
                delay_text = f"{minutes}m"
                
            title = f"Flight {flight_id} Delayed {delay_text}"
            message = f"Flight {flight_id} is delayed by {delay_text}. We'll keep you updated with any changes."
        else:
            title = f"Flight {flight_id} Update"
            message = f"There's been an update to your flight {flight_id}. Please check your booking for details."
        
        return title, message
    
    def _is_priority_override(self, priority: str) -> bool:
        """Check if priority overrides quiet hours"""
        return priority in ['urgent', 'high']
    
    def _is_quiet_hours(self, preferences: Dict[str, Any]) -> bool:
        """Check if current time is in quiet hours"""
        # Simplified implementation - assumes UTC
        current_time = datetime.utcnow().time()
        start_time = datetime.strptime(preferences.get('quiet_hours_start', '22:00'), '%H:%M').time()
        end_time = datetime.strptime(preferences.get('quiet_hours_end', '07:00'), '%H:%M').time()
        
        if start_time <= end_time:
            return start_time <= current_time <= end_time
        else:  # Crosses midnight
            return current_time >= start_time or current_time <= end_time
    
    def _get_next_active_time(self, preferences: Dict[str, Any]) -> datetime:
        """Get next active time outside quiet hours"""
        end_time = datetime.strptime(preferences.get('quiet_hours_end', '07:00'), '%H:%M').time()
        now = datetime.utcnow()
        next_active = datetime.combine(now.date(), end_time)
        
        # If end time is tomorrow
        if next_active <= now:
            next_active += timedelta(days=1)
        
        return next_active