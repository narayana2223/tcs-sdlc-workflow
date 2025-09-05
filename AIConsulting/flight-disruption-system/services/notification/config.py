import os
from typing import List

class Settings:
    # Database configuration
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://flight_user:secure_password@localhost:5432/flight_disruption"
    )
    
    # Redis configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Kafka configuration
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_notification_topic: str = os.getenv("KAFKA_NOTIFICATION_TOPIC", "notification.events")
    kafka_disruption_topic: str = os.getenv("KAFKA_DISRUPTION_TOPIC", "disruption.events")
    
    # SMS configuration
    sms_provider_url: str = os.getenv("SMS_PROVIDER_URL", "https://api.twilio.com/2010-04-01")
    sms_api_key: str = os.getenv("SMS_API_KEY", "dummy_sms_key")
    sms_sender_number: str = os.getenv("SMS_SENDER_NUMBER", "+447700123456")
    
    # Email configuration
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "noreply@airline.com")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "dummy_email_password")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    
    # WhatsApp configuration
    whatsapp_provider_url: str = os.getenv("WHATSAPP_PROVIDER_URL", "https://api.whatsapp.com/send")
    whatsapp_api_key: str = os.getenv("WHATSAPP_API_KEY", "dummy_whatsapp_key")
    whatsapp_sender_number: str = os.getenv("WHATSAPP_SENDER_NUMBER", "+447700123456")
    
    # Push notification configuration
    firebase_server_key: str = os.getenv("FIREBASE_SERVER_KEY", "dummy_firebase_key")
    apns_key: str = os.getenv("APNS_KEY", "dummy_apns_key")
    apns_key_id: str = os.getenv("APNS_KEY_ID", "dummy_apns_key_id")
    apns_team_id: str = os.getenv("APNS_TEAM_ID", "dummy_team_id")
    
    # Notification processing
    batch_size: int = int(os.getenv("NOTIFICATION_BATCH_SIZE", "100"))
    retry_attempts: int = int(os.getenv("NOTIFICATION_RETRY_ATTEMPTS", "3"))
    retry_delay_seconds: int = int(os.getenv("NOTIFICATION_RETRY_DELAY", "5"))
    processing_timeout: int = int(os.getenv("NOTIFICATION_TIMEOUT", "30"))
    
    # Rate limiting
    sms_rate_limit: int = int(os.getenv("SMS_RATE_LIMIT", "10"))  # per minute
    email_rate_limit: int = int(os.getenv("EMAIL_RATE_LIMIT", "50"))  # per minute
    whatsapp_rate_limit: int = int(os.getenv("WHATSAPP_RATE_LIMIT", "20"))  # per minute
    push_rate_limit: int = int(os.getenv("PUSH_RATE_LIMIT", "100"))  # per minute
    
    # Template configuration
    template_cache_ttl: int = int(os.getenv("TEMPLATE_CACHE_TTL", "3600"))  # 1 hour
    default_language: str = os.getenv("DEFAULT_LANGUAGE", "en")
    supported_languages: List[str] = os.getenv("SUPPORTED_LANGUAGES", "en,es,fr,de,it").split(",")
    
    # Queue configuration
    high_priority_queue: str = "notifications:high"
    normal_priority_queue: str = "notifications:normal"
    low_priority_queue: str = "notifications:low"
    scheduled_queue: str = "notifications:scheduled"
    
    # Monitoring
    metrics_enabled: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # External service URLs
    passenger_service_url: str = os.getenv("PASSENGER_SERVICE_URL", "http://localhost:8002")
    compliance_service_url: str = os.getenv("COMPLIANCE_SERVICE_URL", "http://localhost:8004")
    
    # Delivery tracking
    delivery_webhook_url: str = os.getenv("DELIVERY_WEBHOOK_URL", "")
    delivery_tracking_enabled: bool = os.getenv("DELIVERY_TRACKING_ENABLED", "true").lower() == "true"
    
    # Security
    webhook_secret: str = os.getenv("WEBHOOK_SECRET", "dummy_webhook_secret")
    api_key_header: str = os.getenv("API_KEY_HEADER", "X-API-Key")
    
    # Performance
    connection_pool_size: int = int(os.getenv("CONNECTION_POOL_SIZE", "20"))
    max_concurrent_notifications: int = int(os.getenv("MAX_CONCURRENT_NOTIFICATIONS", "50"))
    
    # Feature flags
    enable_sms: bool = os.getenv("ENABLE_SMS", "true").lower() == "true"
    enable_email: bool = os.getenv("ENABLE_EMAIL", "true").lower() == "true"
    enable_whatsapp: bool = os.getenv("ENABLE_WHATSAPP", "true").lower() == "true"
    enable_push: bool = os.getenv("ENABLE_PUSH", "true").lower() == "true"
    enable_delivery_tracking: bool = os.getenv("ENABLE_DELIVERY_TRACKING", "true").lower() == "true"
    enable_template_caching: bool = os.getenv("ENABLE_TEMPLATE_CACHING", "true").lower() == "true"
    
    # Demo mode
    demo_mode: bool = os.getenv("DEMO_MODE", "false").lower() == "true"
    demo_delay_seconds: int = int(os.getenv("DEMO_DELAY_SECONDS", "2"))

settings = Settings()