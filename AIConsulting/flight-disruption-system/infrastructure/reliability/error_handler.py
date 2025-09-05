"""
Comprehensive Error Handling and Retry System
Advanced error handling with circuit breakers, dead letter queues, and recovery mechanisms
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Callable, Tuple, Union
from dataclasses import dataclass, asdict
import traceback
import hashlib

from confluent_kafka import Producer, Consumer, KafkaException
import backoff


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Categories of errors"""
    NETWORK = "network"
    DATA_VALIDATION = "data_validation"
    PROCESSING = "processing"
    EXTERNAL_API = "external_api"
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class RetryStrategy(str, Enum):
    """Retry strategies"""
    IMMEDIATE = "immediate"
    LINEAR_BACKOFF = "linear_backoff"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    CUSTOM_BACKOFF = "custom_backoff"
    NO_RETRY = "no_retry"


@dataclass
class ErrorMetadata:
    """Error metadata for tracking and analysis"""
    error_id: str
    timestamp: float
    component: str
    operation: str
    error_type: str
    error_message: str
    stack_trace: str
    severity: ErrorSeverity
    category: ErrorCategory
    context: Dict[str, Any]
    retry_count: int = 0
    last_retry_timestamp: Optional[float] = None
    resolved: bool = False
    resolution_timestamp: Optional[float] = None


@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_attempts: int
    strategy: RetryStrategy
    base_delay_seconds: float
    max_delay_seconds: float
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retry_on_exceptions: List[type] = None
    stop_on_exceptions: List[type] = None
    
    def __post_init__(self):
        if self.retry_on_exceptions is None:
            self.retry_on_exceptions = [Exception]
        if self.stop_on_exceptions is None:
            self.stop_on_exceptions = [KeyboardInterrupt, SystemExit]


class CircuitBreakerState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    success_threshold: int = 3  # For half-open state
    timeout_seconds: float = 60.0
    monitor_window_seconds: float = 300.0  # 5 minutes


class CircuitBreaker:
    """Circuit breaker implementation"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # Rolling window for monitoring
        self.failure_times = deque()
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                self.logger.info(f"Circuit breaker {self.name} moved to HALF_OPEN")
            else:
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is OPEN")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e
    
    async def _on_success(self):
        """Handle successful execution"""
        self.last_success_time = time.time()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.failure_times.clear()
                self.logger.info(f"Circuit breaker {self.name} moved to CLOSED")
        elif self.state == CircuitBreakerState.CLOSED:
            # Reset failure count on success in closed state
            self.failure_count = max(0, self.failure_count - 1)
    
    async def _on_failure(self):
        """Handle failed execution"""
        self.last_failure_time = time.time()
        self.failure_count += 1
        self.failure_times.append(self.last_failure_time)
        
        # Clean old failures outside the monitoring window
        cutoff_time = self.last_failure_time - self.config.monitor_window_seconds
        while self.failure_times and self.failure_times[0] < cutoff_time:
            self.failure_times.popleft()
        
        if self.state == CircuitBreakerState.CLOSED:
            if len(self.failure_times) >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                self.logger.warning(f"Circuit breaker {self.name} moved to OPEN")
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self.logger.warning(f"Circuit breaker {self.name} moved back to OPEN")
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.last_failure_time is None:
            return False
        
        return time.time() - self.last_failure_time >= self.config.timeout_seconds
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time,
            'last_success_time': self.last_success_time,
            'failures_in_window': len(self.failure_times)
        }


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class RetryableError(Exception):
    """Base class for retryable errors"""
    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


class NonRetryableError(Exception):
    """Base class for non-retryable errors"""
    pass


class DeadLetterHandler:
    """Handler for dead letter events"""
    
    def __init__(self, kafka_producer: Producer, dead_letter_topic: str):
        self.producer = kafka_producer
        self.dead_letter_topic = dead_letter_topic
        self.logger = logging.getLogger(__name__)
    
    async def send_to_dead_letter(
        self,
        original_message: Dict[str, Any],
        error_metadata: ErrorMetadata,
        max_retries_exceeded: bool = False
    ):
        """Send failed message to dead letter queue"""
        try:
            dead_letter_data = {
                'original_message': original_message,
                'error_metadata': asdict(error_metadata),
                'dead_letter_timestamp': time.time(),
                'reason': 'max_retries_exceeded' if max_retries_exceeded else 'non_retryable_error',
                'requires_manual_intervention': error_metadata.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
            }
            
            self.producer.produce(
                topic=self.dead_letter_topic,
                key=error_metadata.error_id,
                value=json.dumps(dead_letter_data).encode('utf-8'),
                headers={
                    'error_id': error_metadata.error_id,
                    'component': error_metadata.component,
                    'severity': error_metadata.severity.value,
                    'category': error_metadata.category.value
                }
            )
            
            self.producer.poll(0)
            self.logger.info(f"Sent message to dead letter queue: {error_metadata.error_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to send message to dead letter queue: {e}")


class ErrorAnalyzer:
    """Analyzes errors for patterns and recommendations"""
    
    def __init__(self):
        self.error_patterns: Dict[str, List[ErrorMetadata]] = defaultdict(list)
        self.component_errors: Dict[str, List[ErrorMetadata]] = defaultdict(list)
        self.logger = logging.getLogger(__name__)
    
    def analyze_error(self, error_metadata: ErrorMetadata) -> Dict[str, Any]:
        """Analyze error and provide insights"""
        # Store error for pattern analysis
        error_pattern = self._generate_error_pattern(error_metadata)
        self.error_patterns[error_pattern].append(error_metadata)
        self.component_errors[error_metadata.component].append(error_metadata)
        
        analysis = {
            'error_id': error_metadata.error_id,
            'categorization': self._categorize_error(error_metadata),
            'severity_assessment': self._assess_severity(error_metadata),
            'retry_recommendation': self._recommend_retry_strategy(error_metadata),
            'pattern_analysis': self._analyze_patterns(error_pattern),
            'resolution_suggestions': self._suggest_resolutions(error_metadata),
            'escalation_required': self._should_escalate(error_metadata)
        }
        
        return analysis
    
    def _generate_error_pattern(self, error_metadata: ErrorMetadata) -> str:
        """Generate pattern key for error grouping"""
        pattern_elements = [
            error_metadata.component,
            error_metadata.operation,
            error_metadata.error_type,
            error_metadata.category.value
        ]
        
        pattern_string = '|'.join(pattern_elements)
        return hashlib.md5(pattern_string.encode()).hexdigest()[:8]
    
    def _categorize_error(self, error_metadata: ErrorMetadata) -> ErrorCategory:
        """Categorize error based on its characteristics"""
        error_message = error_metadata.error_message.lower()
        error_type = error_metadata.error_type.lower()
        
        # Network-related errors
        if any(term in error_message for term in ['connection', 'network', 'timeout', 'unreachable']):
            return ErrorCategory.NETWORK
        
        # Authentication/Authorization errors
        if any(term in error_message for term in ['unauthorized', 'forbidden', 'authentication', 'permission']):
            return ErrorCategory.AUTHENTICATION if 'auth' in error_message else ErrorCategory.AUTHORIZATION
        
        # Data validation errors
        if any(term in error_message for term in ['validation', 'invalid', 'malformed', 'schema']):
            return ErrorCategory.DATA_VALIDATION
        
        # Database errors
        if any(term in error_message for term in ['database', 'sql', 'connection pool', 'deadlock']):
            return ErrorCategory.DATABASE
        
        # Resource exhaustion
        if any(term in error_message for term in ['memory', 'disk', 'cpu', 'resource', 'limit']):
            return ErrorCategory.RESOURCE_EXHAUSTION
        
        # External API errors
        if any(term in error_message for term in ['api', 'http', 'rest', 'service unavailable']):
            return ErrorCategory.EXTERNAL_API
        
        return error_metadata.category  # Keep original if no better match
    
    def _assess_severity(self, error_metadata: ErrorMetadata) -> ErrorSeverity:
        """Assess error severity"""
        error_message = error_metadata.error_message.lower()
        
        # Critical errors
        if any(term in error_message for term in ['critical', 'fatal', 'system failure', 'data corruption']):
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if any(term in error_message for term in ['security', 'unauthorized access', 'data breach', 'service down']):
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if any(term in error_message for term in ['warning', 'degraded', 'partial failure']):
            return ErrorSeverity.MEDIUM
        
        return error_metadata.severity  # Keep original assessment
    
    def _recommend_retry_strategy(self, error_metadata: ErrorMetadata) -> RetryStrategy:
        """Recommend retry strategy based on error characteristics"""
        if error_metadata.category == ErrorCategory.AUTHENTICATION:
            return RetryStrategy.NO_RETRY
        
        if error_metadata.category == ErrorCategory.DATA_VALIDATION:
            return RetryStrategy.NO_RETRY
        
        if error_metadata.category in [ErrorCategory.NETWORK, ErrorCategory.EXTERNAL_API]:
            return RetryStrategy.EXPONENTIAL_BACKOFF
        
        if error_metadata.category == ErrorCategory.RESOURCE_EXHAUSTION:
            return RetryStrategy.LINEAR_BACKOFF
        
        return RetryStrategy.EXPONENTIAL_BACKOFF
    
    def _analyze_patterns(self, error_pattern: str) -> Dict[str, Any]:
        """Analyze error patterns"""
        similar_errors = self.error_patterns[error_pattern]
        
        if len(similar_errors) < 2:
            return {'pattern_detected': False}
        
        # Calculate frequency
        recent_errors = [
            e for e in similar_errors 
            if e.timestamp > time.time() - 3600  # Last hour
        ]
        
        return {
            'pattern_detected': True,
            'total_occurrences': len(similar_errors),
            'recent_occurrences': len(recent_errors),
            'frequency_per_hour': len(recent_errors),
            'pattern_trend': 'increasing' if len(recent_errors) > len(similar_errors) / 2 else 'stable'
        }
    
    def _suggest_resolutions(self, error_metadata: ErrorMetadata) -> List[str]:
        """Suggest resolution steps"""
        suggestions = []
        
        if error_metadata.category == ErrorCategory.NETWORK:
            suggestions.extend([
                "Check network connectivity",
                "Verify firewall rules",
                "Consider increasing timeout values",
                "Implement connection pooling"
            ])
        
        elif error_metadata.category == ErrorCategory.AUTHENTICATION:
            suggestions.extend([
                "Verify API credentials",
                "Check token expiration",
                "Refresh authentication tokens",
                "Verify service account permissions"
            ])
        
        elif error_metadata.category == ErrorCategory.RESOURCE_EXHAUSTION:
            suggestions.extend([
                "Scale up resources",
                "Optimize memory usage",
                "Implement resource pooling",
                "Add resource monitoring"
            ])
        
        elif error_metadata.category == ErrorCategory.EXTERNAL_API:
            suggestions.extend([
                "Check external service status",
                "Implement fallback mechanisms",
                "Add circuit breaker",
                "Consider caching responses"
            ])
        
        return suggestions
    
    def _should_escalate(self, error_metadata: ErrorMetadata) -> bool:
        """Determine if error should be escalated"""
        return (
            error_metadata.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] or
            error_metadata.retry_count > 5 or
            error_metadata.category in [ErrorCategory.AUTHENTICATION, ErrorCategory.DATABASE]
        )


class RetryHandler:
    """Handles retry logic with various strategies"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def retry_with_backoff(
        self,
        func: Callable,
        config: RetryConfig,
        error_metadata: ErrorMetadata,
        *args,
        **kwargs
    ):
        """Retry function with specified strategy"""
        last_exception = None
        
        for attempt in range(config.max_attempts):
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                return result
                
            except tuple(config.stop_on_exceptions) as e:
                self.logger.info(f"Non-retryable exception, stopping retries: {e}")
                raise e
                
            except Exception as e:
                last_exception = e
                error_metadata.retry_count = attempt + 1
                error_metadata.last_retry_timestamp = time.time()
                
                if not self._should_retry(e, config):
                    self.logger.info(f"Exception not in retry list, stopping retries: {e}")
                    raise e
                
                if attempt < config.max_attempts - 1:
                    delay = self._calculate_delay(attempt, config)
                    self.logger.info(f"Retry {attempt + 1}/{config.max_attempts} after {delay:.2f}s delay")
                    await asyncio.sleep(delay)
        
        # All retries exhausted
        raise last_exception
    
    def _should_retry(self, exception: Exception, config: RetryConfig) -> bool:
        """Check if exception should trigger a retry"""
        if not config.retry_on_exceptions:
            return True
        
        return any(isinstance(exception, exc_type) for exc_type in config.retry_on_exceptions)
    
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay for retry attempt"""
        if config.strategy == RetryStrategy.IMMEDIATE:
            delay = 0
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay_seconds * (attempt + 1)
        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay_seconds * (config.backoff_multiplier ** attempt)
        else:
            delay = config.base_delay_seconds
        
        # Apply max delay limit
        delay = min(delay, config.max_delay_seconds)
        
        # Add jitter if enabled
        if config.jitter:
            import random
            jitter_factor = random.uniform(0.5, 1.5)
            delay *= jitter_factor
        
        return delay


class ErrorRecoveryManager:
    """Manages error recovery and system healing"""
    
    def __init__(self):
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {}
        self.logger = logging.getLogger(__name__)
        
        # Register default recovery strategies
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """Register default recovery strategies"""
        self.recovery_strategies[ErrorCategory.NETWORK] = self._recover_network_error
        self.recovery_strategies[ErrorCategory.EXTERNAL_API] = self._recover_api_error
        self.recovery_strategies[ErrorCategory.RESOURCE_EXHAUSTION] = self._recover_resource_error
        self.recovery_strategies[ErrorCategory.DATABASE] = self._recover_database_error
    
    async def attempt_recovery(self, error_metadata: ErrorMetadata) -> bool:
        """Attempt automatic recovery from error"""
        recovery_strategy = self.recovery_strategies.get(error_metadata.category)
        
        if recovery_strategy:
            try:
                success = await recovery_strategy(error_metadata)
                if success:
                    error_metadata.resolved = True
                    error_metadata.resolution_timestamp = time.time()
                    self.logger.info(f"Successfully recovered from error: {error_metadata.error_id}")
                return success
            except Exception as e:
                self.logger.error(f"Recovery strategy failed: {e}")
        
        return False
    
    async def _recover_network_error(self, error_metadata: ErrorMetadata) -> bool:
        """Recover from network errors"""
        # Simple network recovery - wait and test connectivity
        await asyncio.sleep(5)
        # In a real implementation, you would test actual connectivity
        return True
    
    async def _recover_api_error(self, error_metadata: ErrorMetadata) -> bool:
        """Recover from API errors"""
        # For API errors, we might refresh tokens or switch endpoints
        # This is a simplified implementation
        await asyncio.sleep(2)
        return False  # Usually requires manual intervention
    
    async def _recover_resource_error(self, error_metadata: ErrorMetadata) -> bool:
        """Recover from resource exhaustion"""
        # Trigger garbage collection, close unused connections, etc.
        import gc
        gc.collect()
        await asyncio.sleep(1)
        return True
    
    async def _recover_database_error(self, error_metadata: ErrorMetadata) -> bool:
        """Recover from database errors"""
        # Database recovery might involve connection pool reset
        await asyncio.sleep(3)
        return False  # Usually requires manual intervention


class ComprehensiveErrorHandler:
    """Main error handling orchestrator"""
    
    def __init__(
        self,
        kafka_producer: Producer,
        dead_letter_topic: str = "dead.letter.queue"
    ):
        self.kafka_producer = kafka_producer
        self.dead_letter_handler = DeadLetterHandler(kafka_producer, dead_letter_topic)
        self.error_analyzer = ErrorAnalyzer()
        self.retry_handler = RetryHandler()
        self.recovery_manager = ErrorRecoveryManager()
        
        # Circuit breakers for different components
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Error tracking
        self.error_history: List[ErrorMetadata] = []
        self.error_stats = defaultdict(int)
        
        self.logger = logging.getLogger(__name__)
    
    def get_circuit_breaker(self, component_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for component"""
        if component_name not in self.circuit_breakers:
            config = CircuitBreakerConfig()
            self.circuit_breakers[component_name] = CircuitBreaker(component_name, config)
        
        return self.circuit_breakers[component_name]
    
    async def handle_error(
        self,
        error: Exception,
        component: str,
        operation: str,
        context: Dict[str, Any] = None,
        original_message: Dict[str, Any] = None
    ) -> ErrorMetadata:
        """Main error handling entry point"""
        context = context or {}
        
        # Create error metadata
        error_metadata = ErrorMetadata(
            error_id=self._generate_error_id(error, component, operation),
            timestamp=time.time(),
            component=component,
            operation=operation,
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            severity=self._determine_severity(error),
            category=self._categorize_error(error),
            context=context
        )
        
        # Add to history
        self.error_history.append(error_metadata)
        self.error_stats[error_metadata.category] += 1
        
        # Analyze error
        analysis = self.error_analyzer.analyze_error(error_metadata)
        
        # Log error
        self._log_error(error_metadata, analysis)
        
        # Attempt automatic recovery
        recovery_attempted = await self.recovery_manager.attempt_recovery(error_metadata)
        
        # Send to dead letter if critical and no recovery
        if (error_metadata.severity == ErrorSeverity.CRITICAL and 
            not recovery_attempted and original_message):
            await self.dead_letter_handler.send_to_dead_letter(
                original_message, error_metadata, max_retries_exceeded=False
            )
        
        return error_metadata
    
    async def execute_with_error_handling(
        self,
        func: Callable,
        component: str,
        operation: str,
        retry_config: Optional[RetryConfig] = None,
        context: Dict[str, Any] = None,
        original_message: Dict[str, Any] = None,
        *args,
        **kwargs
    ):
        """Execute function with comprehensive error handling"""
        circuit_breaker = self.get_circuit_breaker(component)
        
        try:
            # Execute with circuit breaker protection
            if retry_config:
                # With retries
                async def wrapped_func():
                    return await circuit_breaker.call(func, *args, **kwargs)
                
                error_metadata = ErrorMetadata(
                    error_id="",
                    timestamp=time.time(),
                    component=component,
                    operation=operation,
                    error_type="",
                    error_message="",
                    stack_trace="",
                    severity=ErrorSeverity.LOW,
                    category=ErrorCategory.UNKNOWN,
                    context=context or {}
                )
                
                return await self.retry_handler.retry_with_backoff(
                    wrapped_func, retry_config, error_metadata
                )
            else:
                # Without retries
                return await circuit_breaker.call(func, *args, **kwargs)
                
        except Exception as e:
            error_metadata = await self.handle_error(
                e, component, operation, context, original_message
            )
            
            # Send to dead letter if max retries exceeded
            if (retry_config and error_metadata.retry_count >= retry_config.max_attempts 
                and original_message):
                await self.dead_letter_handler.send_to_dead_letter(
                    original_message, error_metadata, max_retries_exceeded=True
                )
            
            raise e
    
    def _generate_error_id(self, error: Exception, component: str, operation: str) -> str:
        """Generate unique error ID"""
        error_string = f"{component}_{operation}_{type(error).__name__}_{time.time()}"
        return hashlib.md5(error_string.encode()).hexdigest()[:12]
    
    def _determine_severity(self, error: Exception) -> ErrorSeverity:
        """Determine error severity from exception"""
        error_message = str(error).lower()
        
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            return ErrorSeverity.CRITICAL
        
        if any(term in error_message for term in ['critical', 'fatal', 'corruption']):
            return ErrorSeverity.CRITICAL
        
        if any(term in error_message for term in ['security', 'unauthorized', 'authentication']):
            return ErrorSeverity.HIGH
        
        if any(term in error_message for term in ['timeout', 'unavailable', 'connection']):
            return ErrorSeverity.MEDIUM
        
        return ErrorSeverity.LOW
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error from exception"""
        error_message = str(error).lower()
        error_type = type(error).__name__.lower()
        
        if 'timeout' in error_message or 'timeout' in error_type:
            return ErrorCategory.TIMEOUT
        
        if any(term in error_message for term in ['connection', 'network', 'unreachable']):
            return ErrorCategory.NETWORK
        
        if any(term in error_message for term in ['validation', 'invalid', 'malformed']):
            return ErrorCategory.DATA_VALIDATION
        
        if any(term in error_message for term in ['unauthorized', 'forbidden', 'permission']):
            return ErrorCategory.AUTHENTICATION
        
        if any(term in error_message for term in ['memory', 'resource', 'limit']):
            return ErrorCategory.RESOURCE_EXHAUSTION
        
        return ErrorCategory.PROCESSING
    
    def _log_error(self, error_metadata: ErrorMetadata, analysis: Dict[str, Any]):
        """Log error with appropriate level"""
        log_data = {
            'error_id': error_metadata.error_id,
            'component': error_metadata.component,
            'operation': error_metadata.operation,
            'category': error_metadata.category.value,
            'severity': error_metadata.severity.value,
            'retry_count': error_metadata.retry_count,
            'escalation_required': analysis.get('escalation_required', False)
        }
        
        if error_metadata.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"Critical error occurred: {error_metadata.error_message}", extra=log_data)
        elif error_metadata.severity == ErrorSeverity.HIGH:
            self.logger.error(f"High severity error: {error_metadata.error_message}", extra=log_data)
        elif error_metadata.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"Medium severity error: {error_metadata.error_message}", extra=log_data)
        else:
            self.logger.info(f"Low severity error: {error_metadata.error_message}", extra=log_data)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and health metrics"""
        recent_errors = [
            e for e in self.error_history 
            if e.timestamp > time.time() - 3600  # Last hour
        ]
        
        return {
            'total_errors': len(self.error_history),
            'recent_errors': len(recent_errors),
            'error_rate_per_hour': len(recent_errors),
            'errors_by_category': dict(self.error_stats),
            'errors_by_severity': {
                severity.value: sum(1 for e in recent_errors if e.severity == severity)
                for severity in ErrorSeverity
            },
            'circuit_breaker_states': {
                name: cb.get_state()
                for name, cb in self.circuit_breakers.items()
            },
            'most_common_errors': self._get_most_common_errors(recent_errors),
            'resolution_rate': self._calculate_resolution_rate()
        }
    
    def _get_most_common_errors(self, errors: List[ErrorMetadata]) -> List[Dict[str, Any]]:
        """Get most common error patterns"""
        error_counts = defaultdict(int)
        for error in errors:
            key = f"{error.component}:{error.error_type}"
            error_counts[key] += 1
        
        return [
            {'pattern': pattern, 'count': count}
            for pattern, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
    
    def _calculate_resolution_rate(self) -> float:
        """Calculate automatic resolution rate"""
        if not self.error_history:
            return 0.0
        
        resolved_count = sum(1 for e in self.error_history if e.resolved)
        return resolved_count / len(self.error_history)


# Helper functions for easy configuration
def create_default_retry_config(max_attempts: int = 3) -> RetryConfig:
    """Create default retry configuration"""
    return RetryConfig(
        max_attempts=max_attempts,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay_seconds=1.0,
        max_delay_seconds=30.0,
        backoff_multiplier=2.0,
        jitter=True
    )


def create_network_retry_config() -> RetryConfig:
    """Create retry configuration optimized for network errors"""
    return RetryConfig(
        max_attempts=5,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay_seconds=2.0,
        max_delay_seconds=60.0,
        backoff_multiplier=2.0,
        jitter=True,
        retry_on_exceptions=[ConnectionError, TimeoutError, KafkaException]
    )


def create_api_retry_config() -> RetryConfig:
    """Create retry configuration optimized for API errors"""
    return RetryConfig(
        max_attempts=3,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay_seconds=1.0,
        max_delay_seconds=20.0,
        backoff_multiplier=2.0,
        jitter=True,
        retry_on_exceptions=[ConnectionError, TimeoutError],
        stop_on_exceptions=[ValueError, TypeError, KeyError]  # Don't retry on data errors
    )