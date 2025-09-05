import structlog
from typing import Dict, Any, Optional
import json
from datetime import datetime, timedelta
import redis.asyncio as redis
from database import Database
from config import settings

logger = structlog.get_logger()

class TemplateManager:
    """Manages notification templates with caching and localization"""
    
    def __init__(self, db: Database, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client
        self.cache_prefix = "notification_template:"
        
    async def render_template(
        self,
        template_id: str,
        language: str = 'en',
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Render notification template with variables"""
        
        try:
            # Get template from cache or database
            template = await self._get_template(template_id, language)
            if not template:
                raise ValueError(f"Template {template_id} not found for language {language}")
            
            variables = variables or {}
            
            # Render subject and body
            subject = self._render_string(template['subject_template'], variables)
            body = self._render_string(template['body_template'], variables)
            
            return {
                'subject': subject,
                'body': body,
                'language': language,
                'template_id': template_id
            }
            
        except Exception as e:
            logger.error("Failed to render template", template_id=template_id, error=str(e))
            raise
    
    async def _get_template(self, template_id: str, language: str) -> Optional[Dict[str, Any]]:
        """Get template from cache or database"""
        
        cache_key = f"{self.cache_prefix}{template_id}:{language}"
        
        # Try cache first
        if settings.enable_template_caching:
            cached = await self.redis.get(cache_key)
            if cached:
                return json.loads(cached)
        
        # Get from database
        templates = await self.db.get_notification_templates(language)
        template = next((t for t in templates if t['template_id'] == template_id), None)
        
        # Cache if found
        if template and settings.enable_template_caching:
            await self.redis.setex(
                cache_key,
                settings.template_cache_ttl,
                json.dumps(template, default=str)
            )
        
        return template
    
    def _render_string(self, template_string: str, variables: Dict[str, Any]) -> str:
        """Render template string with variables"""
        
        try:
            # Simple variable substitution using Python format strings
            # In production, would use a proper template engine like Jinja2
            
            # Flatten nested variables for easy access
            flat_vars = self._flatten_variables(variables)
            
            # Replace placeholders
            rendered = template_string
            for key, value in flat_vars.items():
                placeholder = f"{{{key}}}"
                if placeholder in rendered:
                    rendered = rendered.replace(placeholder, str(value))
            
            return rendered
            
        except Exception as e:
            logger.error("Template rendering error", error=str(e))
            return template_string  # Return original if rendering fails
    
    def _flatten_variables(self, variables: Dict[str, Any], prefix: str = '') -> Dict[str, Any]:
        """Flatten nested variables for template substitution"""
        
        flat = {}
        
        for key, value in variables.items():
            new_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                flat.update(self._flatten_variables(value, new_key))
            elif isinstance(value, (list, tuple)):
                flat[new_key] = ', '.join(str(item) for item in value)
            elif isinstance(value, datetime):
                flat[new_key] = value.strftime('%Y-%m-%d %H:%M:%S')
            else:
                flat[new_key] = value
        
        return flat
    
    async def create_default_templates(self):
        """Create default notification templates"""
        
        default_templates = [
            {
                'template_id': 'disruption_alert',
                'template_type': 'disruption_alert',
                'language': 'en',
                'subject_template': 'Flight {data.flight_number} Update',
                'body_template': 'Dear {passenger.first_name}, your flight {data.flight_number} has been affected by a {data.type}. New departure time: {data.new_departure_time}. We apologize for the inconvenience.',
                'variables': ['passenger.first_name', 'data.flight_number', 'data.type', 'data.new_departure_time']
            },
            {
                'template_id': 'rebooking_confirmation',
                'template_type': 'rebooking_confirmation',
                'language': 'en',
                'subject_template': 'Rebooking Confirmed - Flight {data.new_flight_number}',
                'body_template': 'Dear {passenger.first_name}, you have been successfully rebooked on flight {data.new_flight_number} departing at {data.new_departure_time}. Your new seat is {data.new_seat}.',
                'variables': ['passenger.first_name', 'data.new_flight_number', 'data.new_departure_time', 'data.new_seat']
            },
            {
                'template_id': 'boarding_reminder',
                'template_type': 'boarding_reminder',
                'language': 'en',
                'subject_template': 'Boarding Soon - Flight {data.flight_number}',
                'body_template': 'Dear {passenger.first_name}, your flight {data.flight_number} is now boarding at gate {data.gate}. Please proceed to the gate immediately.',
                'variables': ['passenger.first_name', 'data.flight_number', 'data.gate']
            },
            {
                'template_id': 'gate_change',
                'template_type': 'gate_change',
                'language': 'en',
                'subject_template': 'Gate Change - Flight {data.flight_number}',
                'body_template': 'Dear {passenger.first_name}, the gate for flight {data.flight_number} has changed to gate {data.new_gate}.',
                'variables': ['passenger.first_name', 'data.flight_number', 'data.new_gate']
            },
            {
                'template_id': 'delay_update',
                'template_type': 'delay_update',
                'language': 'en',
                'subject_template': 'Flight Delay Update - {data.flight_number}',
                'body_template': 'Dear {passenger.first_name}, flight {data.flight_number} is now delayed by {data.delay_minutes} minutes. New departure time: {data.new_departure_time}.',
                'variables': ['passenger.first_name', 'data.flight_number', 'data.delay_minutes', 'data.new_departure_time']
            },
            {
                'template_id': 'compensation_available',
                'template_type': 'compensation_available',
                'language': 'en',
                'subject_template': 'Compensation Available - £{data.amount}',
                'body_template': 'Dear {passenger.first_name}, you are eligible for £{data.amount} compensation due to the disruption to flight {data.flight_number}. We will process this automatically.',
                'variables': ['passenger.first_name', 'data.amount', 'data.flight_number']
            },
            {
                'template_id': 'care_voucher',
                'template_type': 'care_voucher',
                'language': 'en',
                'subject_template': 'Care Voucher - £{data.amount}',
                'body_template': 'Dear {passenger.first_name}, here is your £{data.amount} voucher for {data.voucher_type}. Code: {data.voucher_code}. Valid until: {data.expires_at}.',
                'variables': ['passenger.first_name', 'data.amount', 'data.voucher_type', 'data.voucher_code', 'data.expires_at']
            }
        ]
        
        # Create templates in database
        for template in default_templates:
            await self._create_template(**template)
    
    async def _create_template(
        self,
        template_id: str,
        template_type: str,
        language: str,
        subject_template: str,
        body_template: str,
        variables: list
    ):
        """Create a notification template"""
        
        query = """
        INSERT INTO notification_templates (
            template_id, template_type, language, subject_template, 
            body_template, variables, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (template_id, language) 
        DO UPDATE SET 
            template_type = $2,
            subject_template = $4,
            body_template = $5,
            variables = $6,
            updated_at = $7
        """
        
        await self.db.execute(
            query,
            template_id,
            template_type,
            language,
            subject_template,
            body_template,
            variables,
            datetime.utcnow()
        )
        
        # Invalidate cache
        cache_key = f"{self.cache_prefix}{template_id}:{language}"
        await self.redis.delete(cache_key)
        
        logger.info(
            "Template created/updated",
            template_id=template_id,
            language=language
        )