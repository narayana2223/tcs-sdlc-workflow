import os
from pydantic import BaseModel

class Settings(BaseModel):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://flight_user:secure_password@postgres:5432/flight_disruption")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Kafka
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    
    # Vendor APIs
    hotel_api_key: str = os.getenv("HOTEL_API_KEY", "")
    transport_api_key: str = os.getenv("TRANSPORT_API_KEY", "")
    booking_com_api_key: str = os.getenv("BOOKING_COM_API_KEY", "")
    uber_api_key: str = os.getenv("UBER_API_KEY", "")
    
    # Service settings
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    optimization_cache_ttl: int = int(os.getenv("OPTIMIZATION_CACHE_TTL", "3600"))  # 1 hour
    
    # Cost optimization settings
    max_hotel_price_per_night: float = float(os.getenv("MAX_HOTEL_PRICE_PER_NIGHT", "200.0"))
    max_transport_cost: float = float(os.getenv("MAX_TRANSPORT_COST", "100.0"))
    meal_voucher_rate_per_hour: float = float(os.getenv("MEAL_VOUCHER_RATE_PER_HOUR", "15.0"))
    
    # EU261 compensation rates
    eu261_short_haul: float = float(os.getenv("EU261_SHORT_HAUL", "250.0"))  # <= 1500km
    eu261_medium_haul: float = float(os.getenv("EU261_MEDIUM_HAUL", "400.0"))  # 1500-3500km
    eu261_long_haul: float = float(os.getenv("EU261_LONG_HAUL", "600.0"))  # > 3500km
    
    # Optimization weights
    cost_weight: float = float(os.getenv("COST_WEIGHT", "0.4"))
    satisfaction_weight: float = float(os.getenv("SATISFACTION_WEIGHT", "0.35"))
    time_weight: float = float(os.getenv("TIME_WEIGHT", "0.25"))
    
    class Config:
        env_file = ".env"

settings = Settings()