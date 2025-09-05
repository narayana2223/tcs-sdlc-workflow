"""
Performance Monitoring System - Phase 3
Production-ready performance monitoring and observability platform

Features:
- Real-time system performance monitoring
- Advanced metrics collection and aggregation
- Service health monitoring with alerting
- Performance analytics and trend analysis
- SLA monitoring and reporting
- Predictive performance analysis
- Automated performance optimization
- Comprehensive dashboards and visualization
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import uvicorn
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
from enum import Enum
import asyncpg
import redis
import json
import uuid
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CollectorRegistry, REGISTRY
import httpx
import os
from collections import defaultdict, deque
import statistics
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom metrics registry for isolation
metrics_registry = CollectorRegistry()

# Metrics
REQUEST_COUNT = Counter('monitor_requests_total', 'Total monitoring requests', ['method', 'endpoint'], registry=metrics_registry)
REQUEST_DURATION = Histogram('monitor_request_duration_seconds', 'Request duration', registry=metrics_registry)
SYSTEM_HEALTH = Gauge('system_health_score', 'Overall system health score', registry=metrics_registry)
SERVICE_AVAILABILITY = Gauge('service_availability', 'Service availability percentage', ['service'], registry=metrics_registry)
ALERT_COUNT = Counter('alerts_generated_total', 'Total alerts generated', ['severity', 'service'], registry=metrics_registry)

# Enums
class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DOWN = "down"

class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class MonitoringInterval(str, Enum):
    REAL_TIME = "real_time"
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    ONE_HOUR = "1h"
    ONE_DAY = "1d"

# Data Models
@dataclass
class ServiceMetrics:
    service_name: str
    timestamp: datetime
    response_time: float
    error_rate: float
    throughput: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    availability: float

@dataclass
class PerformanceAlert:
    alert_id: str
    service_name: str
    severity: AlertSeverity
    message: str
    threshold_value: float
    actual_value: float
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None

@dataclass
class SLAMetric:
    sla_name: str
    target_value: float
    current_value: float
    compliance_percentage: float
    time_period: str
    last_updated: datetime

class MonitoringConfig(BaseModel):
    service_name: str
    monitoring_interval: MonitoringInterval = MonitoringInterval.ONE_MINUTE
    alert_thresholds: Dict[str, float] = Field(default_factory=dict)
    sla_targets: Dict[str, float] = Field(default_factory=dict)
    custom_metrics: List[str] = Field(default_factory=list)

class PerformanceReport(BaseModel):
    report_id: str
    time_period: str
    services: List[str]
    metrics_summary: Dict[str, Any]
    sla_compliance: Dict[str, float]
    alerts_summary: Dict[str, int]
    recommendations: List[str]
    generated_at: datetime

class HealthCheckRequest(BaseModel):
    services: List[str] = Field(default_factory=list)
    include_dependencies: bool = True
    timeout: float = 30.0

# Performance Monitoring System
class PerformanceMonitoringSystem:
    def __init__(self):
        self.monitored_services = {}
        self.metrics_history = defaultdict(lambda: deque(maxlen=10000))  # Keep 10k data points
        self.active_alerts = {}
        self.sla_metrics = {}
        self.websocket_connections = set()
        
        # Initialize Redis for metrics storage
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True
        )
        
        # Database connection
        self.db_pool = None
        
        # Monitoring configuration
        self.monitoring_enabled = True
        self.alert_cooldown = {}  # Prevent alert spam
        
        # System performance baselines
        self.performance_baselines = {}
        
        # Predictive models for performance forecasting
        self.performance_predictors = {}
        
        # Service registry with health check endpoints
        self.service_registry = self._initialize_service_registry()
    
    def _initialize_service_registry(self) -> Dict[str, Dict[str, Any]]:
        """Initialize service registry with health check endpoints"""
        return {
            "api-gateway": {
                "url": "http://api-gateway:8000/health",
                "port": 8000,
                "critical": True,
                "dependencies": []
            },
            "disruption-predictor": {
                "url": "http://disruption-predictor:8001/health",
                "port": 8001,
                "critical": True,
                "dependencies": ["postgres", "redis"]
            },
            "passenger-management": {
                "url": "http://passenger-management:8002/health",
                "port": 8002,
                "critical": True,
                "dependencies": ["postgres", "kafka"]
            },
            "cost-optimizer": {
                "url": "http://cost-optimizer:8003/health",
                "port": 8003,
                "critical": True,
                "dependencies": ["postgres", "redis"]
            },
            "compliance-service": {
                "url": "http://compliance:8004/health",
                "port": 8004,
                "critical": True,
                "dependencies": ["postgres"]
            },
            "notification-service": {
                "url": "http://notification:8005/health",
                "port": 8005,
                "critical": True,
                "dependencies": ["kafka", "redis"]
            },
            "advanced-orchestrator": {
                "url": "http://advanced-orchestrator:8006/health",
                "port": 8006,
                "critical": True,
                "dependencies": ["redis"]
            },
            "analytics-dashboard": {
                "url": "http://analytics-dashboard:8007/health",
                "port": 8007,
                "critical": False,
                "dependencies": ["postgres", "redis"]
            },
            "ml-pipeline": {
                "url": "http://ml-pipeline:8010/health",
                "port": 8010,
                "critical": False,
                "dependencies": ["postgres", "redis"]
            },
            "optimization-engine": {
                "url": "http://optimization-engine:8011/health",
                "port": 8011,
                "critical": False,
                "dependencies": ["postgres", "redis"]
            },
            "decision-engine": {
                "url": "http://decision-engine:8012/health",
                "port": 8012,
                "critical": True,
                "dependencies": ["postgres", "redis"]
            },
            "postgres": {
                "url": None,  # Database check
                "port": 5432,
                "critical": True,
                "dependencies": []
            },
            "redis": {
                "url": None,  # Redis check
                "port": 6379,
                "critical": True,
                "dependencies": []
            },
            "kafka": {
                "url": None,  # Kafka check
                "port": 9092,
                "critical": True,
                "dependencies": []
            }
        }
    
    async def initialize_db_pool(self):
        """Initialize database connection pool"""
        try:
            database_url = os.getenv('DATABASE_URL')
            self.db_pool = await asyncpg.create_pool(
                database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("Database pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close_db_pool(self):
        """Close database connection pool"""
        if self.db_pool:
            await self.db_pool.close()
    
    async def start_monitoring(self):
        """Start performance monitoring background tasks"""
        if self.monitoring_enabled:
            # Start service health monitoring
            asyncio.create_task(self._monitor_service_health())
            
            # Start metrics collection
            asyncio.create_task(self._collect_system_metrics())
            
            # Start SLA monitoring
            asyncio.create_task(self._monitor_sla_compliance())
            
            # Start predictive analysis
            asyncio.create_task(self._predictive_performance_analysis())
            
            # Start alert processing
            asyncio.create_task(self._process_alerts())
            
            logger.info("Performance monitoring started")
    
    async def _monitor_service_health(self):
        """Monitor health of all registered services"""
        while self.monitoring_enabled:
            try:
                health_results = {}
                
                for service_name, config in self.service_registry.items():
                    try:
                        health_status = await self._check_service_health(service_name, config)
                        health_results[service_name] = health_status
                        
                        # Update service availability metric
                        availability = 100.0 if health_status['status'] == ServiceStatus.HEALTHY else 0.0
                        SERVICE_AVAILABILITY.labels(service=service_name).set(availability)
                        
                        # Store metrics
                        if health_status['response_time'] is not None:
                            metrics = ServiceMetrics(
                                service_name=service_name,
                                timestamp=datetime.now(),
                                response_time=health_status['response_time'],
                                error_rate=health_status.get('error_rate', 0.0),
                                throughput=health_status.get('throughput', 0.0),
                                cpu_usage=health_status.get('cpu_usage', 0.0),
                                memory_usage=health_status.get('memory_usage', 0.0),
                                disk_usage=health_status.get('disk_usage', 0.0),
                                availability=availability
                            )
                            
                            self.metrics_history[service_name].append(metrics)
                            
                            # Check for alerts
                            await self._check_service_alerts(service_name, metrics)
                    
                    except Exception as e:
                        logger.error(f"Error monitoring service {service_name}: {e}")
                        health_results[service_name] = {
                            'status': ServiceStatus.DOWN,
                            'error': str(e)
                        }
                
                # Calculate overall system health
                overall_health = await self._calculate_system_health(health_results)
                SYSTEM_HEALTH.set(overall_health)
                
                # Broadcast health updates
                await self._broadcast_health_update(health_results, overall_health)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in service health monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _check_service_health(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check health of individual service"""
        start_time = datetime.now()
        
        try:
            if config['url']:
                # HTTP health check
                timeout = httpx.Timeout(10.0)
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(config['url'])
                    
                    response_time = (datetime.now() - start_time).total_seconds()
                    
                    if response.status_code == 200:
                        health_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                        
                        return {
                            'status': ServiceStatus.HEALTHY,
                            'response_time': response_time,
                            'details': health_data,
                            'last_check': datetime.now()
                        }
                    else:
                        return {
                            'status': ServiceStatus.UNHEALTHY,
                            'response_time': response_time,
                            'error': f"HTTP {response.status_code}",
                            'last_check': datetime.now()
                        }
            
            else:
                # TCP connection check for databases
                return await self._check_tcp_service(service_name, config)
        
        except httpx.TimeoutException:
            return {
                'status': ServiceStatus.UNHEALTHY,
                'response_time': None,
                'error': "Timeout",
                'last_check': datetime.now()
            }
        except Exception as e:
            return {
                'status': ServiceStatus.DOWN,
                'response_time': None,
                'error': str(e),
                'last_check': datetime.now()
            }
    
    async def _check_tcp_service(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check TCP-based service health"""
        try:
            start_time = datetime.now()
            
            if service_name == "postgres":
                # PostgreSQL health check
                if self.db_pool:
                    async with self.db_pool.acquire() as conn:
                        await conn.fetchval("SELECT 1")
                    response_time = (datetime.now() - start_time).total_seconds()
                    return {
                        'status': ServiceStatus.HEALTHY,
                        'response_time': response_time,
                        'last_check': datetime.now()
                    }
                else:
                    return {
                        'status': ServiceStatus.DOWN,
                        'response_time': None,
                        'error': "No database connection pool",
                        'last_check': datetime.now()
                    }
            
            elif service_name == "redis":
                # Redis health check
                await asyncio.wait_for(self.redis_client.ping(), timeout=5.0)
                response_time = (datetime.now() - start_time).total_seconds()
                return {
                    'status': ServiceStatus.HEALTHY,
                    'response_time': response_time,
                    'last_check': datetime.now()
                }
            
            elif service_name == "kafka":
                # Kafka health check (simplified)
                # In production, use proper Kafka client
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection('kafka', config['port']), 
                    timeout=5.0
                )
                writer.close()
                await writer.wait_closed()
                response_time = (datetime.now() - start_time).total_seconds()
                return {
                    'status': ServiceStatus.HEALTHY,
                    'response_time': response_time,
                    'last_check': datetime.now()
                }
            
            else:
                return {
                    'status': ServiceStatus.UNKNOWN,
                    'response_time': None,
                    'error': "Unknown service type",
                    'last_check': datetime.now()
                }
        
        except asyncio.TimeoutError:
            return {
                'status': ServiceStatus.UNHEALTHY,
                'response_time': None,
                'error': "Connection timeout",
                'last_check': datetime.now()
            }
        except Exception as e:
            return {
                'status': ServiceStatus.DOWN,
                'response_time': None,
                'error': str(e),
                'last_check': datetime.now()
            }
    
    async def _collect_system_metrics(self):
        """Collect system-level performance metrics"""
        while self.monitoring_enabled:
            try:
                # System metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                system_metrics = {
                    'timestamp': datetime.now(),
                    'cpu_usage': cpu_percent,
                    'memory_usage': memory.percent,
                    'disk_usage': disk.percent,
                    'memory_available': memory.available,
                    'disk_free': disk.free
                }
                
                # Store in Redis
                await self.redis_client.setex(
                    "system_metrics",
                    300,  # 5 minutes TTL
                    json.dumps(system_metrics, default=str)
                )
                
                # Process metrics
                network_io = psutil.net_io_counters()
                
                # Store network metrics
                network_metrics = {
                    'timestamp': datetime.now(),
                    'bytes_sent': network_io.bytes_sent,
                    'bytes_recv': network_io.bytes_recv,
                    'packets_sent': network_io.packets_sent,
                    'packets_recv': network_io.packets_recv
                }
                
                await self.redis_client.setex(
                    "network_metrics",
                    300,
                    json.dumps(network_metrics, default=str)
                )
                
                await asyncio.sleep(30)  # Collect every 30 seconds
                
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_sla_compliance(self):
        """Monitor SLA compliance across services"""
        while self.monitoring_enabled:
            try:
                sla_results = {}
                
                # Define SLA targets
                sla_targets = {
                    'response_time': 2.0,  # seconds
                    'availability': 99.5,  # percentage
                    'error_rate': 1.0,     # percentage
                    'throughput': 100.0    # requests per minute
                }
                
                for service_name in self.service_registry.keys():
                    if service_name in self.metrics_history:
                        recent_metrics = list(self.metrics_history[service_name])[-60:]  # Last hour
                        
                        if recent_metrics:
                            # Calculate SLA metrics
                            avg_response_time = statistics.mean(m.response_time for m in recent_metrics if m.response_time > 0)
                            avg_availability = statistics.mean(m.availability for m in recent_metrics)
                            avg_error_rate = statistics.mean(m.error_rate for m in recent_metrics)
                            avg_throughput = statistics.mean(m.throughput for m in recent_metrics)
                            
                            sla_compliance = {}
                            
                            # Response time compliance
                            sla_compliance['response_time'] = {
                                'target': sla_targets['response_time'],
                                'actual': avg_response_time,
                                'compliant': avg_response_time <= sla_targets['response_time'],
                                'compliance_percentage': min(100, (sla_targets['response_time'] / max(avg_response_time, 0.1)) * 100)
                            }
                            
                            # Availability compliance
                            sla_compliance['availability'] = {
                                'target': sla_targets['availability'],
                                'actual': avg_availability,
                                'compliant': avg_availability >= sla_targets['availability'],
                                'compliance_percentage': avg_availability
                            }
                            
                            sla_results[service_name] = sla_compliance
                            
                            # Store SLA metrics
                            for metric_name, data in sla_compliance.items():
                                sla_metric = SLAMetric(
                                    sla_name=f"{service_name}_{metric_name}",
                                    target_value=data['target'],
                                    current_value=data['actual'],
                                    compliance_percentage=data['compliance_percentage'],
                                    time_period="1h",
                                    last_updated=datetime.now()
                                )
                                
                                self.sla_metrics[sla_metric.sla_name] = sla_metric
                
                # Store SLA results
                await self.redis_client.setex(
                    "sla_compliance",
                    300,
                    json.dumps(sla_results, default=str)
                )
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error monitoring SLA compliance: {e}")
                await asyncio.sleep(300)
    
    async def _check_service_alerts(self, service_name: str, metrics: ServiceMetrics):
        """Check if service metrics trigger any alerts"""
        try:
            alert_thresholds = {
                'response_time': 5.0,      # seconds
                'error_rate': 5.0,         # percentage
                'cpu_usage': 80.0,         # percentage
                'memory_usage': 90.0,      # percentage
                'disk_usage': 90.0,        # percentage
                'availability': 95.0       # percentage (below threshold triggers alert)
            }
            
            alerts_to_generate = []
            
            # Check response time
            if metrics.response_time > alert_thresholds['response_time']:
                alerts_to_generate.append({
                    'metric': 'response_time',
                    'severity': AlertSeverity.WARNING,
                    'threshold': alert_thresholds['response_time'],
                    'actual': metrics.response_time,
                    'message': f"High response time: {metrics.response_time:.2f}s"
                })
            
            # Check error rate
            if metrics.error_rate > alert_thresholds['error_rate']:
                severity = AlertSeverity.CRITICAL if metrics.error_rate > 10.0 else AlertSeverity.WARNING
                alerts_to_generate.append({
                    'metric': 'error_rate',
                    'severity': severity,
                    'threshold': alert_thresholds['error_rate'],
                    'actual': metrics.error_rate,
                    'message': f"High error rate: {metrics.error_rate:.1f}%"
                })
            
            # Check CPU usage
            if metrics.cpu_usage > alert_thresholds['cpu_usage']:
                severity = AlertSeverity.CRITICAL if metrics.cpu_usage > 95.0 else AlertSeverity.WARNING
                alerts_to_generate.append({
                    'metric': 'cpu_usage',
                    'severity': severity,
                    'threshold': alert_thresholds['cpu_usage'],
                    'actual': metrics.cpu_usage,
                    'message': f"High CPU usage: {metrics.cpu_usage:.1f}%"
                })
            
            # Check memory usage
            if metrics.memory_usage > alert_thresholds['memory_usage']:
                severity = AlertSeverity.CRITICAL if metrics.memory_usage > 95.0 else AlertSeverity.WARNING
                alerts_to_generate.append({
                    'metric': 'memory_usage',
                    'severity': severity,
                    'threshold': alert_thresholds['memory_usage'],
                    'actual': metrics.memory_usage,
                    'message': f"High memory usage: {metrics.memory_usage:.1f}%"
                })
            
            # Check availability
            if metrics.availability < alert_thresholds['availability']:
                severity = AlertSeverity.EMERGENCY if metrics.availability == 0.0 else AlertSeverity.CRITICAL
                alerts_to_generate.append({
                    'metric': 'availability',
                    'severity': severity,
                    'threshold': alert_thresholds['availability'],
                    'actual': metrics.availability,
                    'message': f"Low availability: {metrics.availability:.1f}%"
                })
            
            # Generate alerts
            for alert_data in alerts_to_generate:
                await self._generate_alert(service_name, alert_data)
        
        except Exception as e:
            logger.error(f"Error checking alerts for {service_name}: {e}")
    
    async def _generate_alert(self, service_name: str, alert_data: Dict[str, Any]):
        """Generate performance alert"""
        try:
            alert_key = f"{service_name}_{alert_data['metric']}"
            
            # Check alert cooldown
            if alert_key in self.alert_cooldown:
                last_alert = self.alert_cooldown[alert_key]
                if (datetime.now() - last_alert).total_seconds() < 300:  # 5 minute cooldown
                    return
            
            alert = PerformanceAlert(
                alert_id=str(uuid.uuid4()),
                service_name=service_name,
                severity=alert_data['severity'],
                message=alert_data['message'],
                threshold_value=alert_data['threshold'],
                actual_value=alert_data['actual'],
                timestamp=datetime.now()
            )
            
            # Store alert
            self.active_alerts[alert.alert_id] = alert
            self.alert_cooldown[alert_key] = datetime.now()
            
            # Update metrics
            ALERT_COUNT.labels(severity=alert.severity.value, service=service_name).inc()
            
            # Store in database
            if self.db_pool:
                async with self.db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO performance_alerts (
                            id, service_name, severity, message, threshold_value,
                            actual_value, timestamp, resolved
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    alert.alert_id, alert.service_name, alert.severity.value,
                    alert.message, alert.threshold_value, alert.actual_value,
                    alert.timestamp, alert.resolved
                    )
            
            # Broadcast alert
            await self._broadcast_alert(alert)
            
            logger.warning(f"Generated alert: {service_name} - {alert.message}")
            
        except Exception as e:
            logger.error(f"Error generating alert: {e}")
    
    async def _process_alerts(self):
        """Process and manage active alerts"""
        while self.monitoring_enabled:
            try:
                resolved_alerts = []
                
                for alert_id, alert in self.active_alerts.items():
                    # Check if alert should be auto-resolved
                    if not alert.resolved:
                        service_metrics = self.metrics_history.get(alert.service_name)
                        if service_metrics and len(service_metrics) > 0:
                            latest_metric = service_metrics[-1]
                            
                            # Check if condition is resolved
                            should_resolve = False
                            
                            if 'response_time' in alert.message and latest_metric.response_time < alert.threshold_value:
                                should_resolve = True
                            elif 'error_rate' in alert.message and latest_metric.error_rate < alert.threshold_value:
                                should_resolve = True
                            elif 'cpu_usage' in alert.message and latest_metric.cpu_usage < alert.threshold_value:
                                should_resolve = True
                            elif 'memory_usage' in alert.message and latest_metric.memory_usage < alert.threshold_value:
                                should_resolve = True
                            elif 'availability' in alert.message and latest_metric.availability > alert.threshold_value:
                                should_resolve = True
                            
                            if should_resolve:
                                alert.resolved = True
                                alert.resolution_time = datetime.now()
                                resolved_alerts.append(alert_id)
                
                # Update resolved alerts in database
                for alert_id in resolved_alerts:
                    if self.db_pool:
                        async with self.db_pool.acquire() as conn:
                            await conn.execute(
                                "UPDATE performance_alerts SET resolved = TRUE, resolution_time = $1 WHERE id = $2",
                                datetime.now(), alert_id
                            )
                
                await asyncio.sleep(60)  # Process every minute
                
            except Exception as e:
                logger.error(f"Error processing alerts: {e}")
                await asyncio.sleep(60)
    
    async def _calculate_system_health(self, health_results: Dict[str, Dict[str, Any]]) -> float:
        """Calculate overall system health score"""
        try:
            if not health_results:
                return 0.0
            
            health_scores = []
            
            for service_name, health_data in health_results.items():
                service_config = self.service_registry.get(service_name, {})
                is_critical = service_config.get('critical', False)
                
                # Base score
                if health_data['status'] == ServiceStatus.HEALTHY:
                    score = 1.0
                elif health_data['status'] == ServiceStatus.DEGRADED:
                    score = 0.7
                elif health_data['status'] == ServiceStatus.UNHEALTHY:
                    score = 0.3
                else:  # DOWN
                    score = 0.0
                
                # Weight critical services more heavily
                weight = 2.0 if is_critical else 1.0
                weighted_score = score * weight
                
                health_scores.append(weighted_score)
            
            # Calculate weighted average
            if health_scores:
                total_weight = sum(2.0 if self.service_registry.get(svc, {}).get('critical', False) else 1.0 
                                 for svc in health_results.keys())
                overall_health = sum(health_scores) / total_weight
                return min(1.0, max(0.0, overall_health))
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating system health: {e}")
            return 0.5
    
    async def _predictive_performance_analysis(self):
        """Perform predictive analysis on performance trends"""
        while self.monitoring_enabled:
            try:
                # Analyze trends for each service
                for service_name, metrics_data in self.metrics_history.items():
                    if len(metrics_data) >= 10:  # Need minimum data points
                        recent_metrics = list(metrics_data)[-100:]  # Last 100 data points
                        
                        # Analyze response time trend
                        response_times = [m.response_time for m in recent_metrics if m.response_time > 0]
                        if len(response_times) >= 5:
                            trend = self._calculate_trend(response_times)
                            
                            # Predict if response time will exceed threshold
                            if trend > 0.1:  # Increasing trend
                                predicted_value = response_times[-1] + (trend * 10)  # 10 data points ahead
                                if predicted_value > 5.0:
                                    await self._generate_predictive_alert(
                                        service_name, 
                                        'response_time',
                                        predicted_value,
                                        'Predicted response time degradation'
                                    )
                
                await asyncio.sleep(900)  # Analyze every 15 minutes
                
            except Exception as e:
                logger.error(f"Error in predictive analysis: {e}")
                await asyncio.sleep(900)
    
    def _calculate_trend(self, data_points: List[float]) -> float:
        """Calculate trend using simple linear regression slope"""
        try:
            n = len(data_points)
            if n < 2:
                return 0.0
            
            x = list(range(n))
            y = data_points
            
            # Calculate slope
            x_mean = statistics.mean(x)
            y_mean = statistics.mean(y)
            
            numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
            
            if denominator == 0:
                return 0.0
            
            slope = numerator / denominator
            return slope
            
        except Exception:
            return 0.0
    
    async def _generate_predictive_alert(self, service_name: str, metric: str, predicted_value: float, message: str):
        """Generate predictive alert"""
        try:
            alert = PerformanceAlert(
                alert_id=str(uuid.uuid4()),
                service_name=service_name,
                severity=AlertSeverity.INFO,
                message=f"PREDICTIVE: {message} (predicted: {predicted_value:.2f})",
                threshold_value=0.0,  # No current threshold exceeded
                actual_value=predicted_value,
                timestamp=datetime.now()
            )
            
            await self._broadcast_alert(alert)
            logger.info(f"Generated predictive alert: {service_name} - {message}")
            
        except Exception as e:
            logger.error(f"Error generating predictive alert: {e}")
    
    async def _broadcast_health_update(self, health_results: Dict[str, Any], overall_health: float):
        """Broadcast health updates to WebSocket clients"""
        if self.websocket_connections:
            message = {
                'type': 'health_update',
                'timestamp': datetime.now().isoformat(),
                'overall_health': overall_health,
                'services': health_results
            }
            
            await self._broadcast_message(message)
    
    async def _broadcast_alert(self, alert: PerformanceAlert):
        """Broadcast alert to WebSocket clients"""
        if self.websocket_connections:
            message = {
                'type': 'alert',
                'alert': asdict(alert),
                'timestamp': datetime.now().isoformat()
            }
            
            await self._broadcast_message(message)
    
    async def _broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all WebSocket clients"""
        if self.websocket_connections:
            disconnected = set()
            
            for websocket in self.websocket_connections:
                try:
                    await websocket.send_text(json.dumps(message, default=str))
                except Exception:
                    disconnected.add(websocket)
            
            # Remove disconnected clients
            self.websocket_connections -= disconnected
    
    async def get_service_metrics(self, service_name: str, time_range: str = '1h') -> Dict[str, Any]:
        """Get metrics for a specific service"""
        try:
            if service_name not in self.metrics_history:
                return {'error': f'No metrics available for service: {service_name}'}
            
            # Time range mapping
            time_mappings = {
                '5m': 5,
                '15m': 15,
                '1h': 60,
                '4h': 240,
                '1d': 1440
            }
            
            minutes = time_mappings.get(time_range, 60)
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            
            # Filter metrics by time range
            recent_metrics = [
                m for m in self.metrics_history[service_name] 
                if m.timestamp >= cutoff_time
            ]
            
            if not recent_metrics:
                return {'error': f'No recent metrics for service: {service_name}'}
            
            # Calculate statistics
            response_times = [m.response_time for m in recent_metrics if m.response_time > 0]
            
            metrics_summary = {
                'service_name': service_name,
                'time_range': time_range,
                'data_points': len(recent_metrics),
                'response_time': {
                    'avg': statistics.mean(response_times) if response_times else 0,
                    'min': min(response_times) if response_times else 0,
                    'max': max(response_times) if response_times else 0,
                    'p95': np.percentile(response_times, 95) if response_times else 0
                },
                'availability': {
                    'avg': statistics.mean(m.availability for m in recent_metrics),
                    'min': min(m.availability for m in recent_metrics)
                },
                'error_rate': {
                    'avg': statistics.mean(m.error_rate for m in recent_metrics),
                    'max': max(m.error_rate for m in recent_metrics)
                },
                'resource_usage': {
                    'cpu_avg': statistics.mean(m.cpu_usage for m in recent_metrics),
                    'memory_avg': statistics.mean(m.memory_usage for m in recent_metrics),
                    'disk_avg': statistics.mean(m.disk_usage for m in recent_metrics)
                }
            }
            
            return metrics_summary
            
        except Exception as e:
            logger.error(f"Error getting service metrics: {e}")
            return {'error': str(e)}

# Initialize Performance Monitoring System
performance_monitor = PerformanceMonitoringSystem()

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await performance_monitor.initialize_db_pool()
    await performance_monitor.start_monitoring()
    logger.info("Performance Monitoring System started")
    yield
    # Shutdown
    performance_monitor.monitoring_enabled = False
    await performance_monitor.close_db_pool()
    logger.info("Performance Monitoring System stopped")

# Create FastAPI app
app = FastAPI(
    title="Performance Monitoring System",
    description="Production-ready performance monitoring and observability platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "service": "performance-monitor",
        "monitoring_enabled": performance_monitor.monitoring_enabled,
        "monitored_services": len(performance_monitor.service_registry),
        "active_alerts": len(performance_monitor.active_alerts),
        "database_connected": performance_monitor.db_pool is not None
    }

@app.get("/health/services")
async def get_services_health(request: HealthCheckRequest):
    """Get health status of all or specific services"""
    REQUEST_COUNT.labels(method="GET", endpoint="/health/services").inc()
    
    with REQUEST_DURATION.time():
        health_results = {}
        services_to_check = request.services if request.services else list(performance_monitor.service_registry.keys())
        
        for service_name in services_to_check:
            if service_name in performance_monitor.service_registry:
                config = performance_monitor.service_registry[service_name]
                health_status = await performance_monitor._check_service_health(service_name, config)
                health_results[service_name] = health_status
        
        overall_health = await performance_monitor._calculate_system_health(health_results)
        
        return {
            "overall_health_score": overall_health,
            "services": health_results,
            "timestamp": datetime.now()
        }

@app.get("/metrics/{service_name}")
async def get_service_metrics(service_name: str, time_range: str = "1h"):
    """Get performance metrics for a specific service"""
    REQUEST_COUNT.labels(method="GET", endpoint="/metrics/service").inc()
    
    with REQUEST_DURATION.time():
        return await performance_monitor.get_service_metrics(service_name, time_range)

@app.get("/metrics/system")
async def get_system_metrics():
    """Get system-level performance metrics"""
    REQUEST_COUNT.labels(method="GET", endpoint="/metrics/system").inc()
    
    try:
        # Get cached system metrics
        system_metrics_str = await performance_monitor.redis_client.get("system_metrics")
        network_metrics_str = await performance_monitor.redis_client.get("network_metrics")
        
        response = {}
        
        if system_metrics_str:
            response['system'] = json.loads(system_metrics_str)
        
        if network_metrics_str:
            response['network'] = json.loads(network_metrics_str)
        
        response['timestamp'] = datetime.now()
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")

@app.get("/sla")
async def get_sla_compliance():
    """Get SLA compliance status"""
    REQUEST_COUNT.labels(method="GET", endpoint="/sla").inc()
    
    try:
        sla_data_str = await performance_monitor.redis_client.get("sla_compliance")
        
        if sla_data_str:
            sla_data = json.loads(sla_data_str)
            return {
                "sla_compliance": sla_data,
                "timestamp": datetime.now()
            }
        else:
            return {
                "message": "No SLA data available",
                "timestamp": datetime.now()
            }
    
    except Exception as e:
        logger.error(f"Error getting SLA compliance: {e}")
        raise HTTPException(status_code=500, detail="Failed to get SLA compliance")

@app.get("/alerts")
async def get_active_alerts():
    """Get all active alerts"""
    REQUEST_COUNT.labels(method="GET", endpoint="/alerts").inc()
    
    alerts = [asdict(alert) for alert in performance_monitor.active_alerts.values()]
    
    return {
        "alerts": alerts,
        "count": len(alerts),
        "timestamp": datetime.now()
    }

@app.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Manually resolve an alert"""
    REQUEST_COUNT.labels(method="POST", endpoint="/alerts/resolve").inc()
    
    if alert_id in performance_monitor.active_alerts:
        alert = performance_monitor.active_alerts[alert_id]
        alert.resolved = True
        alert.resolution_time = datetime.now()
        
        # Update database
        if performance_monitor.db_pool:
            async with performance_monitor.db_pool.acquire() as conn:
                await conn.execute(
                    "UPDATE performance_alerts SET resolved = TRUE, resolution_time = $1 WHERE id = $2",
                    alert.resolution_time, alert_id
                )
        
        return {"status": "resolved", "alert_id": alert_id}
    else:
        raise HTTPException(status_code=404, detail="Alert not found")

@app.websocket("/ws/monitoring")
async def websocket_monitoring(websocket: WebSocket):
    """WebSocket endpoint for real-time monitoring updates"""
    await websocket.accept()
    performance_monitor.websocket_connections.add(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        performance_monitor.websocket_connections.discard(websocket)

@app.get("/report/performance")
async def generate_performance_report(time_period: str = "24h", services: str = ""):
    """Generate comprehensive performance report"""
    REQUEST_COUNT.labels(method="GET", endpoint="/report/performance").inc()
    
    try:
        service_list = services.split(",") if services else list(performance_monitor.service_registry.keys())
        
        # Collect metrics for each service
        metrics_summary = {}
        for service_name in service_list:
            if service_name in performance_monitor.metrics_history:
                metrics = await performance_monitor.get_service_metrics(service_name, time_period)
                metrics_summary[service_name] = metrics
        
        # SLA compliance
        sla_compliance = {}
        for sla_name, sla_metric in performance_monitor.sla_metrics.items():
            sla_compliance[sla_name] = sla_metric.compliance_percentage
        
        # Alert summary
        alerts_summary = {
            'total': len(performance_monitor.active_alerts),
            'critical': len([a for a in performance_monitor.active_alerts.values() if a.severity == AlertSeverity.CRITICAL]),
            'warning': len([a for a in performance_monitor.active_alerts.values() if a.severity == AlertSeverity.WARNING])
        }
        
        # Generate recommendations
        recommendations = []
        for service_name, metrics in metrics_summary.items():
            if isinstance(metrics, dict) and 'response_time' in metrics:
                if metrics['response_time']['avg'] > 2.0:
                    recommendations.append(f"{service_name}: Consider optimizing response time (avg: {metrics['response_time']['avg']:.2f}s)")
                
                if metrics['availability']['avg'] < 99.0:
                    recommendations.append(f"{service_name}: Improve availability (current: {metrics['availability']['avg']:.1f}%)")
        
        report = PerformanceReport(
            report_id=str(uuid.uuid4()),
            time_period=time_period,
            services=service_list,
            metrics_summary=metrics_summary,
            sla_compliance=sla_compliance,
            alerts_summary=alerts_summary,
            recommendations=recommendations,
            generated_at=datetime.now()
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")

@app.get("/metrics")
async def get_prometheus_metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(metrics_registry)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8013,
        reload=True
    )