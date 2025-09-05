"""
Base API Client with Retry Logic and Error Handling
Foundation for all external API integrations
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from enum import Enum

import aiohttp
import backoff
from pydantic import BaseModel, ValidationError


class APIStatus(str, Enum):
    """API status indicators"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies"""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


@dataclass
class APIConfig:
    """Configuration for API clients"""
    base_url: str
    api_key: Optional[str] = None
    timeout: float = 30.0
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    circuit_breaker_threshold: int = 5
    circuit_breaker_reset_timeout: int = 60
    mock_mode: bool = False
    
    # Headers
    default_headers: Dict[str, str] = None
    
    def __post_init__(self):
        if self.default_headers is None:
            self.default_headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'FlightDisruptionSystem/1.0'
            }
        
        if self.api_key:
            self.default_headers['Authorization'] = f'Bearer {self.api_key}'


@dataclass
class APIResponse:
    """Standardized API response"""
    success: bool
    status_code: int
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    response_time_ms: float = 0.0
    headers: Optional[Dict[str, str]] = None
    cached: bool = False


class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.reset_timeout:
                self.state = 'HALF_OPEN'
                self.failure_count = 0
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
            
            raise e


class RateLimiter:
    """Rate limiter implementation"""
    
    def __init__(self, max_requests: int, window_seconds: int, strategy: RateLimitStrategy = RateLimitStrategy.FIXED_WINDOW):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.strategy = strategy
        self.requests = []
        self.tokens = max_requests
        self.last_refill = time.time()
    
    def is_allowed(self) -> bool:
        """Check if request is allowed"""
        current_time = time.time()
        
        if self.strategy == RateLimitStrategy.FIXED_WINDOW:
            # Remove old requests outside the window
            window_start = current_time - self.window_seconds
            self.requests = [req_time for req_time in self.requests if req_time > window_start]
            
            if len(self.requests) < self.max_requests:
                self.requests.append(current_time)
                return True
            return False
        
        elif self.strategy == RateLimitStrategy.TOKEN_BUCKET:
            # Refill tokens
            time_passed = current_time - self.last_refill
            tokens_to_add = time_passed * (self.max_requests / self.window_seconds)
            self.tokens = min(self.max_requests, self.tokens + tokens_to_add)
            self.last_refill = current_time
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
        
        return True


class BaseAPIClient(ABC):
    """Base class for all external API clients"""
    
    def __init__(self, config: APIConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiting and circuit breaker
        self.rate_limiter = RateLimiter(
            config.rate_limit_requests,
            config.rate_limit_window
        )
        self.circuit_breaker = CircuitBreaker(
            config.circuit_breaker_threshold,
            config.circuit_breaker_reset_timeout
        )
        
        # Health monitoring
        self.status = APIStatus.HEALTHY
        self.last_health_check = None
        self.consecutive_failures = 0
        
        # Performance metrics
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'last_request_time': None
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def connect(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.config.default_headers
        )
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3,
        max_time=300
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> APIResponse:
        """Make HTTP request with retry logic"""
        
        # Check rate limit
        if not self.rate_limiter.is_allowed():
            return APIResponse(
                success=False,
                status_code=429,
                error_message="Rate limit exceeded"
            )
        
        # Prepare request
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        request_headers = {**self.config.default_headers}
        if headers:
            request_headers.update(headers)
        
        start_time = time.time()
        
        try:
            # Use circuit breaker
            response = await self.circuit_breaker.call(
                self._execute_request,
                method,
                url,
                data,
                params,
                request_headers
            )
            
            response_time = (time.time() - start_time) * 1000
            
            # Parse response
            response_data = None
            if response.content_type == 'application/json':
                response_data = await response.json()
            else:
                response_data = {'content': await response.text()}
            
            # Update metrics
            self._update_metrics(True, response_time)
            
            # Create response object
            api_response = APIResponse(
                success=200 <= response.status < 300,
                status_code=response.status,
                data=response_data,
                response_time_ms=response_time,
                headers=dict(response.headers)
            )
            
            if not api_response.success:
                api_response.error_message = f"HTTP {response.status}: {response_data.get('message', 'Unknown error')}"
            
            return api_response
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._update_metrics(False, response_time)
            
            self.logger.error(f"Request failed: {method} {url} - {str(e)}")
            
            return APIResponse(
                success=False,
                status_code=0,
                error_message=str(e),
                response_time_ms=response_time
            )
    
    async def _execute_request(
        self,
        method: str,
        url: str,
        data: Optional[Dict[str, Any]],
        params: Optional[Dict[str, Any]],
        headers: Dict[str, str]
    ):
        """Execute the actual HTTP request"""
        if not self.session:
            await self.connect()
        
        kwargs = {
            'url': url,
            'headers': headers,
            'params': params
        }
        
        if data:
            kwargs['json'] = data
        
        async with self.session.request(method, **kwargs) as response:
            return response
    
    def _update_metrics(self, success: bool, response_time: float):
        """Update performance metrics"""
        self.metrics['total_requests'] += 1
        self.metrics['last_request_time'] = datetime.now()
        
        if success:
            self.metrics['successful_requests'] += 1
            self.consecutive_failures = 0
            if self.status != APIStatus.HEALTHY:
                self.status = APIStatus.HEALTHY
        else:
            self.metrics['failed_requests'] += 1
            self.consecutive_failures += 1
            
            # Update status based on failure rate
            if self.consecutive_failures >= 3:
                self.status = APIStatus.DEGRADED
            if self.consecutive_failures >= 5:
                self.status = APIStatus.UNHEALTHY
        
        # Update average response time (exponential moving average)
        if self.metrics['average_response_time'] == 0:
            self.metrics['average_response_time'] = response_time
        else:
            alpha = 0.1  # Smoothing factor
            self.metrics['average_response_time'] = (
                alpha * response_time + 
                (1 - alpha) * self.metrics['average_response_time']
            )
    
    async def health_check(self) -> bool:
        """Perform health check"""
        try:
            response = await self._make_request('GET', self._get_health_endpoint())
            self.last_health_check = datetime.now()
            
            if response.success:
                self.status = APIStatus.HEALTHY
                return True
            else:
                self.status = APIStatus.DEGRADED
                return False
                
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            self.status = APIStatus.UNHEALTHY
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics"""
        return {
            **self.metrics,
            'status': self.status.value,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'consecutive_failures': self.consecutive_failures,
            'circuit_breaker_state': self.circuit_breaker.state,
            'rate_limiter_tokens': getattr(self.rate_limiter, 'tokens', None)
        }
    
    @abstractmethod
    def _get_health_endpoint(self) -> str:
        """Get health check endpoint for this API"""
        pass
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the API"""
        pass


class CachedAPIClient(BaseAPIClient):
    """API client with caching capabilities"""
    
    def __init__(self, config: APIConfig, cache_ttl: int = 300):
        super().__init__(config)
        self.cache = {}
        self.cache_ttl = cache_ttl
    
    def _get_cache_key(self, method: str, endpoint: str, params: Optional[Dict] = None) -> str:
        """Generate cache key"""
        key_parts = [method.upper(), endpoint]
        if params:
            # Sort params for consistent key
            sorted_params = sorted(params.items())
            key_parts.append(json.dumps(sorted_params, sort_keys=True))
        return ':'.join(key_parts)
    
    def _is_cache_valid(self, cached_item: Dict[str, Any]) -> bool:
        """Check if cached item is still valid"""
        cache_time = cached_item.get('timestamp', 0)
        return time.time() - cache_time < self.cache_ttl
    
    async def _make_cached_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        cache_override: bool = False
    ) -> APIResponse:
        """Make request with caching support"""
        
        # Only cache GET requests
        if method.upper() != 'GET' or cache_override:
            return await self._make_request(method, endpoint, data, params, headers)
        
        cache_key = self._get_cache_key(method, endpoint, params)
        
        # Check cache
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            cached_response = self.cache[cache_key]['response']
            cached_response.cached = True
            return cached_response
        
        # Make fresh request
        response = await self._make_request(method, endpoint, data, params, headers)
        
        # Cache successful responses
        if response.success:
            self.cache[cache_key] = {
                'response': response,
                'timestamp': time.time()
            }
        
        return response
    
    def clear_cache(self):
        """Clear all cached responses"""
        self.cache.clear()
    
    def clear_expired_cache(self):
        """Clear expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self.cache.items()
            if current_time - item['timestamp'] >= self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]


class MockableAPIClient(BaseAPIClient):
    """API client that can use mock data for testing"""
    
    def __init__(self, config: APIConfig):
        super().__init__(config)
        self.mock_responses = {}
    
    def add_mock_response(
        self,
        endpoint: str,
        method: str = 'GET',
        response_data: Dict[str, Any] = None,
        status_code: int = 200,
        delay_ms: float = 0
    ):
        """Add mock response for testing"""
        key = f"{method.upper()}:{endpoint}"
        self.mock_responses[key] = {
            'data': response_data or {},
            'status_code': status_code,
            'delay_ms': delay_ms
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> APIResponse:
        """Make request with mock support"""
        
        if self.config.mock_mode:
            return await self._make_mock_request(method, endpoint, data, params, headers)
        else:
            return await super()._make_request(method, endpoint, data, params, headers)
    
    async def _make_mock_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> APIResponse:
        """Generate mock response"""
        key = f"{method.upper()}:{endpoint}"
        
        if key in self.mock_responses:
            mock_config = self.mock_responses[key]
            
            # Simulate delay
            if mock_config['delay_ms'] > 0:
                await asyncio.sleep(mock_config['delay_ms'] / 1000)
            
            return APIResponse(
                success=200 <= mock_config['status_code'] < 300,
                status_code=mock_config['status_code'],
                data=mock_config['data'],
                response_time_ms=mock_config['delay_ms']
            )
        else:
            # Default mock response
            return APIResponse(
                success=True,
                status_code=200,
                data={'message': f'Mock response for {method} {endpoint}'},
                response_time_ms=10
            )


def create_api_config_from_env(service_name: str) -> APIConfig:
    """Create API config from environment variables"""
    import os
    
    prefix = f"{service_name.upper()}_API"
    
    return APIConfig(
        base_url=os.getenv(f'{prefix}_URL', 'http://localhost:8000'),
        api_key=os.getenv(f'{prefix}_KEY'),
        timeout=float(os.getenv(f'{prefix}_TIMEOUT', '30.0')),
        max_retries=int(os.getenv(f'{prefix}_MAX_RETRIES', '3')),
        rate_limit_requests=int(os.getenv(f'{prefix}_RATE_LIMIT', '100')),
        rate_limit_window=int(os.getenv(f'{prefix}_RATE_WINDOW', '60')),
        mock_mode=os.getenv(f'{prefix}_MOCK_MODE', 'false').lower() == 'true'
    )