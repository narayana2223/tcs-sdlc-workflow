import os
from pydantic import BaseModel

class Settings(BaseModel):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://flight_user:secure_password@postgres:5432/flight_disruption")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Kafka
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    
    # AI/ML APIs
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    weather_api_key: str = os.getenv("WEATHER_API_KEY", "")
    
    # Service settings
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    prediction_cache_ttl: int = int(os.getenv("PREDICTION_CACHE_TTL", "3600"))  # 1 hour
    
    # Model settings
    min_confidence_threshold: float = float(os.getenv("MIN_CONFIDENCE_THRESHOLD", "0.3"))
    high_risk_threshold: float = float(os.getenv("HIGH_RISK_THRESHOLD", "0.7"))
    
    class Config:
        env_file = ".env"

settings = Settings()