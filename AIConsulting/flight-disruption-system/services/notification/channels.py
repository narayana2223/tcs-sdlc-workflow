import asyncio
import structlog
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings

logger = structlog.get_logger()

class NotificationChannel(ABC):
    """Base class for notification channels"""
    
    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client
    
    @abstractmethod
    async def send(
        self,
        passenger: Dict[str, Any],
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send notification through this channel"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if channel is healthy"""
        pass
    
    async def test(self) -> Dict[str, Any]:
        """Test channel functionality"""
        return {"test": "not_implemented"}

class SMSChannel(NotificationChannel):
    """SMS notification channel using Twilio or similar provider"""
    
    def __init__(self, provider_url: str, api_key: str, http_client: httpx.AsyncClient):
        super().__init__(http_client)
        self.provider_url = provider_url
        self.api_key = api_key
        self.sender_number = settings.sms_sender_number
    
    async def send(
        self,
        passenger: Dict[str, Any],
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send SMS notification"""
        
        try:
            phone_number = passenger.get('phone')
            if not phone_number:
                logger.warning("No phone number for passenger", passenger_id=passenger.get('passenger_id'))
                return False
            
            # Demo mode - just log the message
            if settings.demo_mode:
                logger.info(
                    "SMS sent (demo mode)",
                    passenger_id=passenger.get('passenger_id'),
                    phone=phone_number,
                    message=f"{title}: {message}"
                )
                await asyncio.sleep(settings.demo_delay_seconds)
                return True
            
            # Prepare SMS payload
            payload = {
                'From': self.sender_number,
                'To': phone_number,
                'Body': f"{title}\n\n{message}"
            }
            
            # Add additional data if provided
            if data:
                if data.get('flight_number'):
                    payload['Body'] += f"\n\nFlight: {data['flight_number']}"
                if data.get('pnr'):
                    payload['Body'] += f"\nBooking: {data['pnr']}"
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = await self.http_client.post(
                f"{self.provider_url}/Messages",
                data=payload,
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code == 201:
                logger.info(
                    "SMS sent successfully",
                    passenger_id=passenger.get('passenger_id'),
                    phone=phone_number
                )
                return True
            else:
                logger.error(
                    "SMS send failed",
                    status_code=response.status_code,
                    response=response.text
                )
                return False
                
        except Exception as e:
            logger.error("SMS channel error", error=str(e))
            return False
    
    async def health_check(self) -> bool:
        """Check SMS provider health"""
        try:
            if settings.demo_mode:
                return True
                
            response = await self.http_client.get(
                f"{self.provider_url}/Accounts",
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=5.0
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def test(self) -> Dict[str, Any]:
        """Test SMS functionality"""
        return {
            "provider_url": self.provider_url,
            "demo_mode": settings.demo_mode,
            "health": await self.health_check()
        }

class EmailChannel(NotificationChannel):
    """Email notification channel"""
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        http_client: httpx.AsyncClient
    ):
        super().__init__(http_client)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    async def send(
        self,
        passenger: Dict[str, Any],
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send email notification"""
        
        try:
            email = passenger.get('email')
            if not email:
                logger.warning("No email for passenger", passenger_id=passenger.get('passenger_id'))
                return False
            
            # Demo mode - just log the message
            if settings.demo_mode:
                logger.info(
                    "Email sent (demo mode)",
                    passenger_id=passenger.get('passenger_id'),
                    email=email,
                    subject=title,
                    message=message
                )
                await asyncio.sleep(settings.demo_delay_seconds)
                return True
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = email
            msg['Subject'] = title
            
            # Email body with passenger details
            email_body = f"Dear {passenger.get('first_name', 'Passenger')},\n\n"
            email_body += f"{message}\n\n"
            
            if data:
                if data.get('pnr'):
                    email_body += f"Booking Reference: {data['pnr']}\n"
                if data.get('flight_number'):
                    email_body += f"Flight Number: {data['flight_number']}\n"
                if data.get('new_departure_time'):
                    email_body += f"New Departure: {data['new_departure_time']}\n"
            
            email_body += "\nBest regards,\nYour Airline Team"
            
            msg.attach(MIMEText(email_body, 'plain'))
            
            # Send email using asyncio to avoid blocking
            def send_email():
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    if settings.smtp_use_tls:
                        server.starttls()
                    server.login(self.username, self.password)
                    server.send_message(msg)
            
            # Run in thread pool to avoid blocking
            await asyncio.get_event_loop().run_in_executor(None, send_email)
            
            logger.info(
                "Email sent successfully",
                passenger_id=passenger.get('passenger_id'),
                email=email
            )
            return True
            
        except Exception as e:
            logger.error("Email channel error", error=str(e))
            return False
    
    async def health_check(self) -> bool:
        """Check email server health"""
        try:
            if settings.demo_mode:
                return True
                
            def check_smtp():
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    if settings.smtp_use_tls:
                        server.starttls()
                    server.login(self.username, self.password)
                    return True
            
            return await asyncio.get_event_loop().run_in_executor(None, check_smtp)
        except Exception:
            return False
    
    async def test(self) -> Dict[str, Any]:
        """Test email functionality"""
        return {
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "demo_mode": settings.demo_mode,
            "health": await self.health_check()
        }

class WhatsAppChannel(NotificationChannel):
    """WhatsApp notification channel"""
    
    def __init__(self, provider_url: str, api_key: str, http_client: httpx.AsyncClient):
        super().__init__(http_client)
        self.provider_url = provider_url
        self.api_key = api_key
        self.sender_number = settings.whatsapp_sender_number
    
    async def send(
        self,
        passenger: Dict[str, Any],
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send WhatsApp notification"""
        
        try:
            phone_number = passenger.get('phone')
            if not phone_number:
                logger.warning("No phone number for passenger", passenger_id=passenger.get('passenger_id'))
                return False
            
            # Demo mode - just log the message
            if settings.demo_mode:
                logger.info(
                    "WhatsApp sent (demo mode)",
                    passenger_id=passenger.get('passenger_id'),
                    phone=phone_number,
                    message=f"{title}: {message}"
                )
                await asyncio.sleep(settings.demo_delay_seconds)
                return True
            
            # Format WhatsApp message with emojis
            whatsapp_message = f"✈️ {title}\n\n{message}"
            
            if data:
                if data.get('pnr'):
                    whatsapp_message += f"\n\n📋 Booking: {data['pnr']}"
                if data.get('flight_number'):
                    whatsapp_message += f"\n✈️ Flight: {data['flight_number']}"
            
            whatsapp_message += "\n\n💬 Reply STOP to unsubscribe"
            
            payload = {
                'from': self.sender_number,
                'to': phone_number,
                'message': whatsapp_message
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = await self.http_client.post(
                f"{self.provider_url}/messages",
                json=payload,
                headers=headers,
                timeout=10.0
            )
            
            if response.status_code == 200:
                logger.info(
                    "WhatsApp sent successfully",
                    passenger_id=passenger.get('passenger_id'),
                    phone=phone_number
                )
                return True
            else:
                logger.error(
                    "WhatsApp send failed",
                    status_code=response.status_code,
                    response=response.text
                )
                return False
                
        except Exception as e:
            logger.error("WhatsApp channel error", error=str(e))
            return False
    
    async def health_check(self) -> bool:
        """Check WhatsApp provider health"""
        try:
            if settings.demo_mode:
                return True
                
            response = await self.http_client.get(
                f"{self.provider_url}/health",
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=5.0
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def test(self) -> Dict[str, Any]:
        """Test WhatsApp functionality"""
        return {
            "provider_url": self.provider_url,
            "demo_mode": settings.demo_mode,
            "health": await self.health_check()
        }

class PushChannel(NotificationChannel):
    """Push notification channel for mobile apps"""
    
    def __init__(
        self,
        firebase_key: str,
        apns_key: str,
        http_client: httpx.AsyncClient
    ):
        super().__init__(http_client)
        self.firebase_key = firebase_key
        self.apns_key = apns_key
    
    async def send(
        self,
        passenger: Dict[str, Any],
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send push notification"""
        
        try:
            # In real implementation, would get device tokens from passenger data
            device_token = passenger.get('device_token')
            platform = passenger.get('platform', 'ios')  # ios or android
            
            if not device_token:
                logger.info(
                    "No device token for passenger",
                    passenger_id=passenger.get('passenger_id')
                )
                return False
            
            # Demo mode - just log the message
            if settings.demo_mode:
                logger.info(
                    "Push notification sent (demo mode)",
                    passenger_id=passenger.get('passenger_id'),
                    platform=platform,
                    title=title,
                    message=message
                )
                await asyncio.sleep(settings.demo_delay_seconds)
                return True
            
            if platform == 'android':
                return await self._send_android_push(device_token, title, message, data)
            else:
                return await self._send_ios_push(device_token, title, message, data)
                
        except Exception as e:
            logger.error("Push notification error", error=str(e))
            return False
    
    async def _send_android_push(
        self,
        device_token: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send Android push notification via Firebase"""
        
        try:
            payload = {
                'to': device_token,
                'notification': {
                    'title': title,
                    'body': message,
                    'icon': 'airline_logo',
                    'sound': 'default'
                },
                'data': data or {}
            }
            
            headers = {
                'Authorization': f'key={self.firebase_key}',
                'Content-Type': 'application/json'
            }
            
            response = await self.http_client.post(
                'https://fcm.googleapis.com/fcm/send',
                json=payload,
                headers=headers,
                timeout=10.0
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error("Android push error", error=str(e))
            return False
    
    async def _send_ios_push(
        self,
        device_token: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send iOS push notification via APNS"""
        
        try:
            payload = {
                'aps': {
                    'alert': {
                        'title': title,
                        'body': message
                    },
                    'sound': 'default',
                    'badge': 1
                }
            }
            
            if data:
                payload.update(data)
            
            headers = {
                'authorization': f'bearer {self.apns_key}',
                'apns-topic': 'com.airline.app',
                'content-type': 'application/json'
            }
            
            response = await self.http_client.post(
                f'https://api.push.apple.com/3/device/{device_token}',
                json=payload,
                headers=headers,
                timeout=10.0
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error("iOS push error", error=str(e))
            return False
    
    async def health_check(self) -> bool:
        """Check push notification services health"""
        try:
            if settings.demo_mode:
                return True
                
            # Simple check - in production would verify keys and connectivity
            return bool(self.firebase_key and self.apns_key)
        except Exception:
            return False
    
    async def test(self) -> Dict[str, Any]:
        """Test push notification functionality"""
        return {
            "firebase_configured": bool(self.firebase_key),
            "apns_configured": bool(self.apns_key),
            "demo_mode": settings.demo_mode,
            "health": await self.health_check()
        }