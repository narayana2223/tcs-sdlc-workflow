"""
Flight Disruption Management System - API Gateway

Production-ready API Gateway with JWT authentication, rate limiting,
request routing, and comprehensive monitoring for airline operations.
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
import os
import json
import structlog

from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import uvicorn
import httpx
import redis.asyncio as redis
import jwt
from jwt import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel, Field
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge
import slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import shared components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from shared.database import get_async_db_session, get_database_health

# Configure structured logging
logger = structlog.get_logger()

# Security configuration
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Metrics
REQUEST_COUNT = Counter('api_gateway_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('api_gateway_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
ACTIVE_CONNECTIONS = Gauge('api_gateway_active_connections', 'Active connections')
RATE_LIMIT_EXCEEDED = Counter('api_gateway_rate_limit_exceeded_total', 'Rate limit exceeded events', ['endpoint'])
JWT_VALIDATION_FAILURES = Counter('api_gateway_jwt_validation_failures_total', 'JWT validation failures', ['reason'])

# Service registry for microservices
SERVICE_REGISTRY = {
    'disruption-predictor': {
        'url': os.getenv('DISRUPTION_PREDICTOR_URL', 'http://localhost:8001'),
        'health_check': '/health',
        'timeout': 30
    },
    'passenger-management': {
        'url': os.getenv('PASSENGER_MANAGEMENT_URL', 'http://localhost:8002'),
        'health_check': '/health',
        'timeout': 15
    },
    'cost-optimizer': {
        'url': os.getenv('COST_OPTIMIZER_URL', 'http://localhost:8003'),
        'health_check': '/health',
        'timeout': 10
    },
    'compliance': {
        'url': os.getenv('COMPLIANCE_URL', 'http://localhost:8004'),
        'health_check': '/health',
        'timeout': 15
    },
    'notification': {
        'url': os.getenv('NOTIFICATION_URL', 'http://localhost:8005'),
        'health_check': '/health',
        'timeout': 10
    }
}


class GatewayConfig:
    """API Gateway configuration"""
    
    def __init__(self):
        self.jwt_secret_key = os.getenv('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production')
        self.jwt_algorithm = 'HS256'
        self.jwt_expiration_hours = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
        
        # Redis configuration for caching and rate limiting
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
        # Security settings
        self.allowed_hosts = os.getenv('ALLOWED_HOSTS', '*').split(',')
        self.cors_origins = os.getenv('CORS_ORIGINS', '*').split(',')
        
        # Rate limiting
        self.rate_limit_requests_per_minute = int(os.getenv('RATE_LIMIT_RPM', '100'))
        self.rate_limit_burst = int(os.getenv('RATE_LIMIT_BURST', '20'))
        
        # Circuit breaker settings
        self.circuit_breaker_failure_threshold = int(os.getenv('CIRCUIT_BREAKER_FAILURE_THRESHOLD', '5'))
        self.circuit_breaker_recovery_timeout = int(os.getenv('CIRCUIT_BREAKER_RECOVERY_TIMEOUT', '60'))


config = GatewayConfig()


# Pydantic models
class TokenRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    expires_at: datetime


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=6)
    role: str = Field(default='user', regex=r'^(admin|operator|user)$')


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    services: Dict[str, Any]
    database: Dict[str, Any]
    redis: Dict[str, Any]


# Global instances
app = FastAPI(
    title="Flight Disruption Management API Gateway",
    description="Production-ready API Gateway for airline disruption management system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

redis_client: Optional[redis.Redis] = None
circuit_breaker_state: Dict[str, Dict[str, Any]] = {}


# Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=config.allowed_hosts
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Authentication and authorization
class JWTManager:
    """JWT token management"""
    
    @staticmethod
    def create_access_token(data: dict) -> str:
        """Create a new JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=config.jwt_expiration_hours)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, config.jwt_secret_key, algorithm=config.jwt_algorithm)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, config.jwt_secret_key, algorithms=[config.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            JWT_VALIDATION_FAILURES.labels(reason="expired").inc()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except InvalidTokenError:
            JWT_VALIDATION_FAILURES.labels(reason="invalid").inc()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    token = credentials.credentials
    payload = JWTManager.verify_token(token)
    
    user_id = payload.get("sub")
    if user_id is None:
        JWT_VALIDATION_FAILURES.labels(reason="no_subject").inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    return payload


async def require_role(required_role: str):
    """Dependency to require specific role"""
    async def check_role(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", "user")
        if user_role != required_role and user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role}"
            )
        return current_user
    return check_role


# Circuit breaker implementation
class CircuitBreaker:
    """Circuit breaker for service resilience"""
    
    @staticmethod
    def get_circuit_state(service_name: str) -> Dict[str, Any]:
        """Get circuit breaker state for a service"""
        if service_name not in circuit_breaker_state:
            circuit_breaker_state[service_name] = {
                'state': 'CLOSED',  # CLOSED, OPEN, HALF_OPEN
                'failure_count': 0,
                'last_failure_time': None,
                'success_count': 0
            }
        return circuit_breaker_state[service_name]
    
    @staticmethod
    async def call_service(service_name: str, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Call a service through circuit breaker"""
        circuit_state = CircuitBreaker.get_circuit_state(service_name)
        
        # Check if circuit is open
        if circuit_state['state'] == 'OPEN':
            if (datetime.utcnow().timestamp() - circuit_state['last_failure_time']) < config.circuit_breaker_recovery_timeout:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Service {service_name} is currently unavailable (circuit breaker open)"
                )
            else:
                circuit_state['state'] = 'HALF_OPEN'
                circuit_state['success_count'] = 0
        
        try:
            service_config = SERVICE_REGISTRY[service_name]
            url = f"{service_config['url']}{endpoint}"
            timeout = service_config.get('timeout', 30)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(method, url, **kwargs)
            
            # Success - update circuit breaker
            if circuit_state['state'] == 'HALF_OPEN':
                circuit_state['success_count'] += 1
                if circuit_state['success_count'] >= 3:  # Require 3 successes to close
                    circuit_state['state'] = 'CLOSED'
                    circuit_state['failure_count'] = 0
            elif circuit_state['state'] == 'CLOSED':
                circuit_state['failure_count'] = 0
            
            return response
        
        except Exception as e:
            logger.error(f"Service call failed", service=service_name, endpoint=endpoint, error=str(e))
            
            # Update failure count
            circuit_state['failure_count'] += 1
            circuit_state['last_failure_time'] = datetime.utcnow().timestamp()
            
            # Open circuit if threshold exceeded
            if circuit_state['failure_count'] >= config.circuit_breaker_failure_threshold:
                circuit_state['state'] = 'OPEN'
                logger.warning(f"Circuit breaker opened for service {service_name}")
            
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service {service_name} call failed: {str(e)}"
            )


# Redis utilities
async def get_redis_client() -> redis.Redis:
    """Get Redis client"""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(config.redis_url, decode_responses=True)
    return redis_client


# Middleware
@app.middleware("http")
async def monitoring_middleware(request: Request, call_next: Callable):
    """Monitoring and metrics middleware"""
    start_time = time.time()
    ACTIVE_CONNECTIONS.inc()
    
    try:
        response = await call_next(request)
        
        # Record metrics
        duration = time.time() - start_time
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        return response
    
    finally:
        ACTIVE_CONNECTIONS.dec()


@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next: Callable):
    """Enhanced rate limiting middleware"""
    client_ip = get_remote_address(request)
    redis_conn = await get_redis_client()
    
    # Check rate limit
    current_requests = await redis_conn.get(f"rate_limit:{client_ip}")
    if current_requests and int(current_requests) > config.rate_limit_requests_per_minute:
        RATE_LIMIT_EXCEEDED.labels(endpoint=request.url.path).inc()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    # Increment counter
    await redis_conn.incr(f"rate_limit:{client_ip}")
    await redis_conn.expire(f"rate_limit:{client_ip}", 60)
    
    response = await call_next(request)
    return response


# Health check endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {},
        "database": {},
        "redis": {}
    }
    
    # Check database
    try:
        db_health = await get_database_health()
        health_status["database"] = db_health
        if db_health["status"] != "healthy":
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"
    
    # Check Redis
    try:
        redis_conn = await get_redis_client()
        await redis_conn.ping()
        health_status["redis"] = {"status": "healthy"}
    except Exception as e:
        health_status["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    # Check microservices
    for service_name, service_config in SERVICE_REGISTRY.items():
        try:
            response = await CircuitBreaker.call_service(
                service_name, 
                "GET", 
                service_config["health_check"]
            )
            health_status["services"][service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
        except Exception as e:
            health_status["services"][service_name] = {
                "status": "unhealthy",
                "error": str(e)
            }
            if health_status["status"] == "healthy":
                health_status["status"] = "degraded"
    
    return health_status


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        prometheus_client.generate_latest(),
        media_type="text/plain"
    )


# Authentication endpoints
@app.post("/auth/token", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, token_request: TokenRequest):
    """Authenticate user and return JWT token"""
    # In production, validate against database
    # For now, simple hardcoded validation
    valid_users = {
        "admin": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
        "operator": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
        "demo": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # secret
    }
    
    username = token_request.username
    password = token_request.password
    
    if username not in valid_users or not pwd_context.verify(password, valid_users[username]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create token
    token_data = {
        "sub": username,
        "role": "admin" if username == "admin" else "operator",
        "iat": datetime.utcnow().timestamp()
    }
    
    access_token = JWTManager.create_access_token(token_data)
    expires_at = datetime.utcnow() + timedelta(hours=config.jwt_expiration_hours)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=config.jwt_expiration_hours * 3600,
        expires_at=expires_at
    )


# Service proxy endpoints
@app.api_route("/api/v1/predictions/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_predictions(
    path: str, 
    request: Request, 
    current_user: dict = Depends(get_current_user)
):
    """Proxy requests to disruption predictor service"""
    body = await request.body()
    headers = dict(request.headers)
    
    # Add user context to headers
    headers["X-User-ID"] = current_user["sub"]
    headers["X-User-Role"] = current_user["role"]
    
    response = await CircuitBreaker.call_service(
        "disruption-predictor",
        request.method,
        f"/{path}",
        content=body,
        headers=headers,
        params=dict(request.query_params)
    )
    
    return JSONResponse(
        content=response.json() if response.content else {},
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@app.api_route("/api/v1/passengers/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_passengers(
    path: str, 
    request: Request, 
    current_user: dict = Depends(get_current_user)
):
    """Proxy requests to passenger management service"""
    body = await request.body()
    headers = dict(request.headers)
    
    headers["X-User-ID"] = current_user["sub"]
    headers["X-User-Role"] = current_user["role"]
    
    response = await CircuitBreaker.call_service(
        "passenger-management",
        request.method,
        f"/{path}",
        content=body,
        headers=headers,
        params=dict(request.query_params)
    )
    
    return JSONResponse(
        content=response.json() if response.content else {},
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@app.api_route("/api/v1/rebookings/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_rebookings(
    path: str, 
    request: Request, 
    current_user: dict = Depends(get_current_user)
):
    """Proxy requests to passenger management service for rebookings"""
    body = await request.body()
    headers = dict(request.headers)
    
    headers["X-User-ID"] = current_user["sub"]
    headers["X-User-Role"] = current_user["role"]
    
    response = await CircuitBreaker.call_service(
        "passenger-management",
        request.method,
        f"/rebookings/{path}",
        content=body,
        headers=headers,
        params=dict(request.query_params)
    )
    
    return JSONResponse(
        content=response.json() if response.content else {},
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@app.api_route("/api/v1/cost-optimization/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_cost_optimization(
    path: str, 
    request: Request, 
    current_user: dict = Depends(get_current_user)
):
    """Proxy requests to cost optimizer service"""
    body = await request.body()
    headers = dict(request.headers)
    
    headers["X-User-ID"] = current_user["sub"]
    headers["X-User-Role"] = current_user["role"]
    
    response = await CircuitBreaker.call_service(
        "cost-optimizer",
        request.method,
        f"/{path}",
        content=body,
        headers=headers,
        params=dict(request.query_params)
    )
    
    return JSONResponse(
        content=response.json() if response.content else {},
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@app.api_route("/api/v1/compliance/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_compliance(
    path: str, 
    request: Request, 
    current_user: dict = Depends(get_current_user)
):
    """Proxy requests to compliance service"""
    body = await request.body()
    headers = dict(request.headers)
    
    headers["X-User-ID"] = current_user["sub"]
    headers["X-User-Role"] = current_user["role"]
    
    response = await CircuitBreaker.call_service(
        "compliance",
        request.method,
        f"/{path}",
        content=body,
        headers=headers,
        params=dict(request.query_params)
    )
    
    return JSONResponse(
        content=response.json() if response.content else {},
        status_code=response.status_code,
        headers=dict(response.headers)
    )


@app.api_route("/api/v1/notifications/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_notifications(
    path: str, 
    request: Request, 
    current_user: dict = Depends(get_current_user)
):
    """Proxy requests to notification service"""
    body = await request.body()
    headers = dict(request.headers)
    
    headers["X-User-ID"] = current_user["sub"]
    headers["X-User-Role"] = current_user["role"]
    
    response = await CircuitBreaker.call_service(
        "notification",
        request.method,
        f"/{path}",
        content=body,
        headers=headers,
        params=dict(request.query_params)
    )
    
    return JSONResponse(
        content=response.json() if response.content else {},
        status_code=response.status_code,
        headers=dict(response.headers)
    )


# Administrative endpoints
@app.get("/admin/circuit-breakers")
async def get_circuit_breaker_status(current_user: dict = Depends(require_role("admin"))):
    """Get circuit breaker status for all services"""
    return circuit_breaker_state


@app.post("/admin/circuit-breakers/{service_name}/reset")
async def reset_circuit_breaker(
    service_name: str,
    current_user: dict = Depends(require_role("admin"))
):
    """Reset circuit breaker for a specific service"""
    if service_name in circuit_breaker_state:
        circuit_breaker_state[service_name] = {
            'state': 'CLOSED',
            'failure_count': 0,
            'last_failure_time': None,
            'success_count': 0
        }
        return {"message": f"Circuit breaker reset for {service_name}"}
    else:
        raise HTTPException(status_code=404, detail="Service not found")


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    logger.info("API Gateway starting up...")
    
    # Initialize Redis connection
    global redis_client
    redis_client = await get_redis_client()
    
    try:
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
    
    logger.info("API Gateway started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown"""
    logger.info("API Gateway shutting down...")
    
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")
    
    logger.info("API Gateway shut down completed")


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )