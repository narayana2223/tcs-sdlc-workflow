import os
from typing import Optional

class ExternalAPIConfig:
    """Configuration for external API integrations"""
    
    def __init__(self):
        # Demo mode
        self.demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"
        
        # Weather API configuration
        self.weather_api_key = os.getenv("WEATHER_API_KEY", "demo_weather_key")
        self.weather_api_url = os.getenv("WEATHER_API_URL", "https://api.weatherapi.com/v1")
        
        # PSS (Passenger Service System) configuration
        self.pss_provider = os.getenv("PSS_PROVIDER", "amadeus")  # amadeus, sabre, travelport
        self.pss_api_key = os.getenv("PSS_API_KEY", "demo_pss_key")
        self.pss_api_url = os.getenv("PSS_API_URL", "https://api.amadeus.com")
        self.pss_username = os.getenv("PSS_USERNAME", "demo_user")
        self.pss_password = os.getenv("PSS_PASSWORD", "demo_password")
        
        # Hotel booking API configuration
        self.hotel_provider = os.getenv("HOTEL_PROVIDER", "booking.com")  # booking.com, expedia, amadeus_hotel
        self.hotel_api_key = os.getenv("HOTEL_API_KEY", "demo_hotel_key")
        self.hotel_api_url = os.getenv("HOTEL_API_URL", "https://api.booking.com/v2")
        
        # Ground transport API configuration
        self.transport_provider = os.getenv("TRANSPORT_PROVIDER", "uber")  # uber, lyft, local_taxi
        self.transport_api_key = os.getenv("TRANSPORT_API_KEY", "demo_transport_key")
        self.transport_api_url = os.getenv("TRANSPORT_API_URL", "https://api.uber.com/v1")
        
        # Airline API configuration (for direct airline integrations)
        self.airline_api_key = os.getenv("AIRLINE_API_KEY", "demo_airline_key")
        self.airline_api_url = os.getenv("AIRLINE_API_URL", "https://api.airline.com/v1")
        
        # External notification providers
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "demo_twilio_sid")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "demo_twilio_token")
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY", "demo_sendgrid_key")
        
        # API rate limiting
        self.weather_rate_limit = int(os.getenv("WEATHER_API_RATE_LIMIT", "1000"))  # requests per hour
        self.pss_rate_limit = int(os.getenv("PSS_API_RATE_LIMIT", "500"))  # requests per hour
        self.hotel_rate_limit = int(os.getenv("HOTEL_API_RATE_LIMIT", "100"))  # requests per minute
        self.transport_rate_limit = int(os.getenv("TRANSPORT_API_RATE_LIMIT", "100"))  # requests per minute
        
        # Timeout configurations
        self.default_timeout = int(os.getenv("API_DEFAULT_TIMEOUT", "30"))  # seconds
        self.weather_timeout = int(os.getenv("WEATHER_API_TIMEOUT", "15"))  # seconds
        self.pss_timeout = int(os.getenv("PSS_API_TIMEOUT", "60"))  # seconds
        self.hotel_timeout = int(os.getenv("HOTEL_API_TIMEOUT", "30"))  # seconds
        self.transport_timeout = int(os.getenv("TRANSPORT_API_TIMEOUT", "20"))  # seconds
        
        # Retry configurations
        self.max_retries = int(os.getenv("API_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("API_RETRY_DELAY", "1"))  # seconds
        self.backoff_factor = float(os.getenv("API_BACKOFF_FACTOR", "2.0"))
        
        # Cache configurations
        self.enable_caching = os.getenv("API_ENABLE_CACHING", "true").lower() == "true"
        self.cache_ttl_weather = int(os.getenv("CACHE_TTL_WEATHER", "300"))  # 5 minutes
        self.cache_ttl_flight_status = int(os.getenv("CACHE_TTL_FLIGHT_STATUS", "60"))  # 1 minute
        self.cache_ttl_hotel_search = int(os.getenv("CACHE_TTL_HOTEL_SEARCH", "600"))  # 10 minutes
        
        # Circuit breaker configurations
        self.circuit_breaker_enabled = os.getenv("CIRCUIT_BREAKER_ENABLED", "true").lower() == "true"
        self.circuit_breaker_failure_threshold = int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"))
        self.circuit_breaker_recovery_timeout = int(os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "60"))  # seconds
        self.circuit_breaker_expected_exception = os.getenv("CIRCUIT_BREAKER_EXPECTED_EXCEPTION", "httpx.HTTPError")
        
        # Feature flags
        self.enable_weather_integration = os.getenv("ENABLE_WEATHER_INTEGRATION", "true").lower() == "true"
        self.enable_pss_integration = os.getenv("ENABLE_PSS_INTEGRATION", "true").lower() == "true"
        self.enable_hotel_integration = os.getenv("ENABLE_HOTEL_INTEGRATION", "true").lower() == "true"
        self.enable_transport_integration = os.getenv("ENABLE_TRANSPORT_INTEGRATION", "true").lower() == "true"
        
        # Logging and monitoring
        self.log_api_requests = os.getenv("LOG_API_REQUESTS", "true").lower() == "true"
        self.log_api_responses = os.getenv("LOG_API_RESPONSES", "false").lower() == "true"
        self.collect_metrics = os.getenv("COLLECT_API_METRICS", "true").lower() == "true"
        
        # Security
        self.verify_ssl = os.getenv("VERIFY_SSL", "true").lower() == "true"
        self.use_proxy = os.getenv("USE_PROXY", "false").lower() == "true"
        self.proxy_url = os.getenv("PROXY_URL", "")
        
        # Emergency contacts and fallbacks
        self.emergency_hotel_phone = os.getenv("EMERGENCY_HOTEL_PHONE", "+44800123456")
        self.emergency_transport_phone = os.getenv("EMERGENCY_TRANSPORT_PHONE", "+44800654321")
        self.fallback_notification_email = os.getenv("FALLBACK_NOTIFICATION_EMAIL", "operations@airline.com")
    
    def get_weather_config(self) -> dict:
        """Get weather API specific configuration"""
        return {
            'api_key': self.weather_api_key,
            'base_url': self.weather_api_url,
            'timeout': self.weather_timeout,
            'rate_limit': self.weather_rate_limit,
            'cache_ttl': self.cache_ttl_weather,
            'enabled': self.enable_weather_integration
        }
    
    def get_pss_config(self) -> dict:
        """Get PSS API specific configuration"""
        return {
            'provider': self.pss_provider,
            'api_key': self.pss_api_key,
            'base_url': self.pss_api_url,
            'username': self.pss_username,
            'password': self.pss_password,
            'timeout': self.pss_timeout,
            'rate_limit': self.pss_rate_limit,
            'enabled': self.enable_pss_integration
        }
    
    def get_hotel_config(self) -> dict:
        """Get hotel API specific configuration"""
        return {
            'provider': self.hotel_provider,
            'api_key': self.hotel_api_key,
            'base_url': self.hotel_api_url,
            'timeout': self.hotel_timeout,
            'rate_limit': self.hotel_rate_limit,
            'cache_ttl': self.cache_ttl_hotel_search,
            'enabled': self.enable_hotel_integration
        }
    
    def get_transport_config(self) -> dict:
        """Get transport API specific configuration"""
        return {
            'provider': self.transport_provider,
            'api_key': self.transport_api_key,
            'base_url': self.transport_api_url,
            'timeout': self.transport_timeout,
            'rate_limit': self.transport_rate_limit,
            'enabled': self.enable_transport_integration
        }
    
    def get_circuit_breaker_config(self) -> dict:
        """Get circuit breaker configuration"""
        return {
            'enabled': self.circuit_breaker_enabled,
            'failure_threshold': self.circuit_breaker_failure_threshold,
            'recovery_timeout': self.circuit_breaker_recovery_timeout,
            'expected_exception': self.circuit_breaker_expected_exception
        }
    
    def get_retry_config(self) -> dict:
        """Get retry configuration"""
        return {
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'backoff_factor': self.backoff_factor
        }
    
    def get_http_client_config(self) -> dict:
        """Get HTTP client configuration"""
        config = {
            'timeout': self.default_timeout,
            'verify': self.verify_ssl,
            'max_redirects': 3,
            'limits': {
                'max_keepalive_connections': 20,
                'max_connections': 100
            }
        }
        
        if self.use_proxy and self.proxy_url:
            config['proxies'] = {
                'http://': self.proxy_url,
                'https://': self.proxy_url
            }
        
        return config
    
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode"""
        return self.demo_mode
    
    def should_log_requests(self) -> bool:
        """Check if API requests should be logged"""
        return self.log_api_requests
    
    def should_log_responses(self) -> bool:
        """Check if API responses should be logged"""
        return self.log_api_responses
    
    def should_collect_metrics(self) -> bool:
        """Check if API metrics should be collected"""
        return self.collect_metrics