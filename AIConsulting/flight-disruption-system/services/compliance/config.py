import os
from pydantic import BaseModel

class Settings(BaseModel):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://flight_user:secure_password@postgres:5432/flight_disruption")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Kafka
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    
    # Service settings
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    compliance_cache_ttl: int = int(os.getenv("COMPLIANCE_CACHE_TTL", "7200"))  # 2 hours
    
    # Compliance processing settings
    auto_process_threshold: float = float(os.getenv("AUTO_PROCESS_THRESHOLD", "0.9"))  # Confidence threshold
    claim_deadline_days: int = int(os.getenv("CLAIM_DEADLINE_DAYS", "30"))
    dispute_deadline_days: int = int(os.getenv("DISPUTE_DEADLINE_DAYS", "60"))
    
    # EU261 Compensation amounts (EUR)
    eu261_short_haul: float = float(os.getenv("EU261_SHORT_HAUL", "250"))  # <= 1500km
    eu261_medium_haul: float = float(os.getenv("EU261_MEDIUM_HAUL", "400"))  # 1500-3500km
    eu261_long_haul: float = float(os.getenv("EU261_LONG_HAUL", "600"))  # > 3500km
    
    # UK CAA Compensation amounts (GBP)
    uk_caa_short_haul: float = float(os.getenv("UK_CAA_SHORT_HAUL", "220"))
    uk_caa_medium_haul: float = float(os.getenv("UK_CAA_MEDIUM_HAUL", "350"))
    uk_caa_long_haul: float = float(os.getenv("UK_CAA_LONG_HAUL", "520"))
    
    # US DOT compensation rules (USD)
    dot_domestic_2x_max: float = float(os.getenv("DOT_DOMESTIC_2X_MAX", "775"))
    dot_domestic_4x_max: float = float(os.getenv("DOT_DOMESTIC_4X_MAX", "1550"))
    dot_international_multiplier: float = float(os.getenv("DOT_INTERNATIONAL_MULTIPLIER", "1.5"))
    
    # Delay thresholds (minutes)
    min_compensation_delay: int = int(os.getenv("MIN_COMPENSATION_DELAY", "180"))  # 3 hours
    severe_delay_threshold: int = int(os.getenv("SEVERE_DELAY_THRESHOLD", "300"))  # 5 hours
    
    # Extraordinary circumstances
    extraordinary_circumstances: str = os.getenv(
        "EXTRAORDINARY_CIRCUMSTANCES", 
        "weather,security,atc,strike,political_instability,health_emergency"
    )
    
    # Care obligations
    meal_allowance_2h: float = float(os.getenv("MEAL_ALLOWANCE_2H", "10"))
    meal_allowance_4h: float = float(os.getenv("MEAL_ALLOWANCE_4H", "20"))
    hotel_allowance_overnight: float = float(os.getenv("HOTEL_ALLOWANCE_OVERNIGHT", "100"))
    transport_allowance: float = float(os.getenv("TRANSPORT_ALLOWANCE", "30"))
    
    # Communication settings
    communication_allowance_2h: float = float(os.getenv("COMMUNICATION_ALLOWANCE_2H", "5"))
    communication_allowance_4h: float = float(os.getenv("COMMUNICATION_ALLOWANCE_4H", "10"))
    
    # Processing timeframes (days)
    standard_processing_days: int = int(os.getenv("STANDARD_PROCESSING_DAYS", "30"))
    expedited_processing_days: int = int(os.getenv("EXPEDITED_PROCESSING_DAYS", "7"))
    
    # Integration settings
    enable_auto_processing: bool = os.getenv("ENABLE_AUTO_PROCESSING", "true").lower() == "true"
    enable_dispute_handling: bool = os.getenv("ENABLE_DISPUTE_HANDLING", "true").lower() == "true"
    
    class Config:
        env_file = ".env"

settings = Settings()