"""
Retry handler with exponential backoff and circuit breaker pattern
"""
import asyncio
import time
from typing import Callable, Any, Optional, TypeVar, Union
from functools import wraps
import logging
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject all calls
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures
    """
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker is OPEN. Service unavailable.")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    async def async_call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker is OPEN. Service unavailable.")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should try to reset the circuit"""
        return (
            self.last_failure_time and 
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(
                f"Circuit breaker opened after {self.failure_count} failures"
            )

class RetryConfig:
    """Configuration for retry behavior"""
    def __init__(self,
                 max_retries: int = 3,
                 initial_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_base: float = 2.0,
                 jitter: bool = True):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

async def exponential_backoff_retry(
    func: Callable[..., T],
    config: RetryConfig = RetryConfig(),
    circuit_breaker: Optional[CircuitBreaker] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None
) -> T:
    """
    Retry a function with exponential backoff
    
    Args:
        func: Function to retry
        config: Retry configuration
        circuit_breaker: Optional circuit breaker
        on_retry: Optional callback on each retry
    """
    last_exception = None
    
    for attempt in range(config.max_retries + 1):
        try:
            if circuit_breaker:
                if asyncio.iscoroutinefunction(func):
                    return await circuit_breaker.async_call(func)
                else:
                    return circuit_breaker.call(func)
            else:
                if asyncio.iscoroutinefunction(func):
                    return await func()
                else:
                    return func()
                    
        except Exception as e:
            last_exception = e
            
            if attempt == config.max_retries:
                logger.error(f"Max retries ({config.max_retries}) exceeded. Last error: {e}")
                raise
            
            # Calculate delay with exponential backoff
            delay = min(
                config.initial_delay * (config.exponential_base ** attempt),
                config.max_delay
            )
            
            # Add jitter to prevent thundering herd
            if config.jitter:
                import random
                delay *= (0.5 + random.random())
            
            if on_retry:
                on_retry(attempt + 1, e)
            
            logger.warning(
                f"Retry {attempt + 1}/{config.max_retries} after {delay:.2f}s. "
                f"Error: {e}"
            )
            
            await asyncio.sleep(delay)
    
    raise last_exception

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff
    
    Usage:
        @retry_with_backoff(max_retries=5, initial_delay=2.0)
        async def fetch_data():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            config = RetryConfig(
                max_retries=max_retries,
                initial_delay=initial_delay,
                max_delay=max_delay
            )
            
            last_exception = None
            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_retries:
                        raise
                    
                    delay = min(
                        config.initial_delay * (2 ** attempt),
                        config.max_delay
                    )
                    
                    logger.warning(
                        f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                        f"after {delay:.2f}s. Error: {e}"
                    )
                    
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            config = RetryConfig(
                max_retries=max_retries,
                initial_delay=initial_delay,
                max_delay=max_delay
            )
            
            last_exception = None
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_retries:
                        raise
                    
                    delay = min(
                        config.initial_delay * (2 ** attempt),
                        config.max_delay
                    )
                    
                    logger.warning(
                        f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                        f"after {delay:.2f}s. Error: {e}"
                    )
                    
                    time.sleep(delay)
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

class SmartRetryHandler:
    """
    Smart retry handler that adapts based on error patterns
    """
    def __init__(self):
        self.error_counts = {}
        self.success_counts = {}
        self.circuit_breakers = {}
    
    def get_circuit_breaker(self, service: str) -> CircuitBreaker:
        """Get or create circuit breaker for a service"""
        if service not in self.circuit_breakers:
            self.circuit_breakers[service] = CircuitBreaker()
        return self.circuit_breakers[service]
    
    async def execute_with_retry(
        self,
        service: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with smart retry logic
        """
        circuit_breaker = self.get_circuit_breaker(service)
        
        # Adapt retry config based on recent errors
        if service in self.error_counts:
            error_rate = self.error_counts[service] / max(
                self.success_counts.get(service, 1), 1
            )
            
            # More aggressive retries for services with high error rates
            if error_rate > 0.5:
                config = RetryConfig(max_retries=5, initial_delay=2.0)
            elif error_rate > 0.2:
                config = RetryConfig(max_retries=4, initial_delay=1.5)
            else:
                config = RetryConfig()
        else:
            config = RetryConfig()
        
        try:
            result = await exponential_backoff_retry(
                lambda: func(*args, **kwargs),
                config=config,
                circuit_breaker=circuit_breaker
            )
            
            # Track success
            self.success_counts[service] = self.success_counts.get(service, 0) + 1
            
            return result
            
        except Exception as e:
            # Track error
            self.error_counts[service] = self.error_counts.get(service, 0) + 1
            raise

# Global smart retry handler
smart_retry = SmartRetryHandler()