import os
from pydantic import BaseModel

class Settings(BaseModel):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://flight_user:secure_password@postgres:5432/flight_disruption")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Kafka
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    
    # Airline PSS APIs
    amadeus_api_key: str = os.getenv("AMADEUS_API_KEY", "")
    sabre_api_key: str = os.getenv("SABRE_API_KEY", "")
    travelport_api_key: str = os.getenv("TRAVELPORT_API_KEY", "")
    
    # Service settings
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    rebooking_cache_ttl: int = int(os.getenv("REBOOKING_CACHE_TTL", "1800"))  # 30 minutes
    
    # Rebooking preferences
    max_alternatives: int = int(os.getenv("MAX_ALTERNATIVES", "10"))
    default_search_window_hours: int = int(os.getenv("DEFAULT_SEARCH_WINDOW_HOURS", "24"))
    min_connection_time_minutes: int = int(os.getenv("MIN_CONNECTION_TIME_MINUTES", "90"))
    
    class Config:
        env_file = ".env"

settings = Settings()