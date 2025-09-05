import os
import httpx
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Any, Optional
import time
import redis.asyncio as redis
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Metrics
REQUEST_COUNT = Counter('gateway_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('gateway_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
BACKEND_REQUEST_DURATION = Histogram('gateway_backend_request_duration_seconds', 'Backend request duration', ['service'])

# Configuration
class Settings(BaseModel):
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-here")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Service URLs
    disruption_predictor_url: str = os.getenv("DISRUPTION_PREDICTOR_URL", "http://disruption-predictor:8000")
    passenger_management_url: str = os.getenv("PASSENGER_MANAGEMENT_URL", "http://passenger-management:8000")
    cost_optimizer_url: str = os.getenv("COST_OPTIMIZER_URL", "http://cost-optimizer:8000")
    compliance_url: str = os.getenv("COMPLIANCE_URL", "http://compliance:8000")
    notification_url: str = os.getenv("NOTIFICATION_URL", "http://notification:8000")
    
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "1000"))

settings = Settings()

# Global variables
redis_client: Optional[redis.Redis] = None
http_client: Optional[httpx.AsyncClient] = None

# Service routes mapping
SERVICE_ROUTES = {
    "/api/v1/predictions": settings.disruption_predictor_url,
    "/api/v1/passengers": settings.passenger_management_url,
    "/api/v1/bookings": settings.passenger_management_url,
    "/api/v1/rebookings": settings.passenger_management_url,
    "/api/v1/cost-optimization": settings.cost_optimizer_url,
    "/api/v1/hotels": settings.cost_optimizer_url,
    "/api/v1/transport": settings.cost_optimizer_url,
    "/api/v1/compliance": settings.compliance_url,
    "/api/v1/compensation": settings.compliance_url,
    "/api/v1/notifications": settings.notification_url,
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global redis_client, http_client
    
    redis_client = redis.from_url(settings.redis_url)
    http_client = httpx.AsyncClient(timeout=30.0)
    
    # Test connections
    try:
        await redis_client.ping()
        logger.info("Connected to Redis")
    except Exception as e:
        logger.error("Failed to connect to Redis", error=str(e))
    
    yield
    
    # Shutdown
    if redis_client:
        await redis_client.close()
    if http_client:
        await http_client.aclose()

app = FastAPI(
    title="Flight Disruption Management API Gateway",
    description="API Gateway for Flight Disruption Management System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

class AuthenticationError(Exception):
    pass

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

async def rate_limit(request: Request) -> None:
    """Simple rate limiting using Redis"""
    if not redis_client:
        return
    
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"
    
    try:
        current = await redis_client.get(key)
        if current is None:
            await redis_client.setex(key, 60, 1)
        else:
            count = int(current)
            if count >= settings.rate_limit_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            await redis_client.incr(key)
    except redis.RedisError as e:
        logger.warning("Rate limiting unavailable", error=str(e))

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Log and metrics
    duration = time.time() - start_time
    method = request.method
    path = request.url.path
    status_code = response.status_code
    
    REQUEST_COUNT.labels(method=method, endpoint=path, status=status_code).inc()
    REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)
    
    logger.info(
        "Request processed",
        method=method,
        path=path,
        status_code=status_code,
        duration=duration
    )
    
    return response

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check Redis
    try:
        if redis_client:
            await redis_client.ping()
            health_status["services"]["redis"] = "healthy"
        else:
            health_status["services"]["redis"] = "disconnected"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check backend services
    if http_client:
        for service_path, service_url in SERVICE_ROUTES.items():
            try:
                service_name = service_url.split("//")[1].split(":")[0]
                response = await http_client.get(f"{service_url}/health", timeout=5.0)
                if response.status_code == 200:
                    health_status["services"][service_name] = "healthy"
                else:
                    health_status["services"][service_name] = f"unhealthy: {response.status_code}"
                    health_status["status"] = "degraded"
            except Exception as e:
                service_name = service_url.split("//")[1].split(":")[0]
                health_status["services"][service_name] = f"unreachable: {str(e)}"
                health_status["status"] = "degraded"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/api/v1/auth/token")
async def create_access_token(username: str, password: str):
    """Create JWT access token (simplified for demo)"""
    # In production, verify against database
    if username == "admin" and password == "admin":  # Demo credentials
        payload = {
            "sub": username,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return {"access_token": token, "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password"
    )

async def proxy_request(
    request: Request,
    service_url: str,
    path: str
) -> JSONResponse:
    """Proxy request to backend service"""
    if not http_client:
        raise HTTPException(status_code=503, detail="HTTP client not available")
    
    # Prepare request
    method = request.method
    headers = dict(request.headers)
    
    # Remove hop-by-hop headers
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    # Get request body
    body = None
    if method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
    
    # Make request to backend
    url = f"{service_url}{path}"
    query_params = str(request.url.query) if request.url.query else ""
    if query_params:
        url += f"?{query_params}"
    
    start_time = time.time()
    try:
        response = await http_client.request(
            method=method,
            url=url,
            headers=headers,
            content=body
        )
        
        # Record metrics
        service_name = service_url.split("//")[1].split(":")[0]
        BACKEND_REQUEST_DURATION.labels(service=service_name).observe(time.time() - start_time)
        
        # Return response
        return JSONResponse(
            content=response.json() if response.content else None,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
        
    except httpx.RequestError as e:
        logger.error("Backend request failed", url=url, error=str(e))
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
    except Exception as e:
        logger.error("Unexpected error", url=url, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

# Dynamic route handler
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def route_handler(
    request: Request,
    path: str,
    token: Dict[str, Any] = Depends(verify_token)
):
    """Handle all API routes and proxy to appropriate service"""
    await rate_limit(request)
    
    # Find matching service
    full_path = f"/{path}"
    service_url = None
    
    for route_prefix, url in SERVICE_ROUTES.items():
        if full_path.startswith(route_prefix):
            service_url = url
            break
    
    if not service_url:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Remove API prefix from path for backend service
    backend_path = "/" + path
    
    return await proxy_request(request, service_url, backend_path)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Flight Disruption Management API Gateway",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)