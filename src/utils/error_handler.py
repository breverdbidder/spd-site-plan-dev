#!/usr/bin/env python3
"""
Centralized Error Handler for SPD Site Plan Development
P1 Codebase Requirement: Unified error handling across all modules

Features:
- Structured error logging
- Error categorization and severity levels
- Automatic retry with exponential backoff
- Circuit breaker integration
- Supabase error logging
- Sanitization of sensitive data

Author: BidDeed.AI / Everest Capital USA
"""

import os
import sys
import json
import logging
import traceback
import hashlib
from typing import Optional, Dict, Any, Callable, TypeVar, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
import asyncio

# Type variable for generic functions
T = TypeVar('T')


class ErrorSeverity(Enum):
    """Error severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""
    NETWORK = "network"
    DATABASE = "database"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    PARSE = "parse"
    EXTERNAL_API = "external_api"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for an error"""
    module: str
    function: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StructuredError:
    """Structured error representation"""
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    context: ErrorContext
    original_exception: Optional[Exception] = None
    stack_trace: Optional[str] = None
    error_code: Optional[str] = None
    retry_count: int = 0
    is_retryable: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage"""
        return {
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "context": {
                "module": self.context.module,
                "function": self.context.function,
                "timestamp": self.context.timestamp.isoformat(),
                "correlation_id": self.context.correlation_id,
                "user_id": self.context.user_id,
                "request_id": self.context.request_id,
                "additional_data": self.context.additional_data,
            },
            "error_code": self.error_code,
            "retry_count": self.retry_count,
            "is_retryable": self.is_retryable,
            "stack_trace": self.stack_trace,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """Circuit breaker for fault tolerance"""
    name: str
    failure_threshold: int = 5
    recovery_timeout: int = 30
    half_open_max_calls: int = 3
    
    _failure_count: int = field(default=0, init=False)
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _last_failure_time: Optional[datetime] = field(default=None, init=False)
    _half_open_calls: int = field(default=0, init=False)
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state with automatic recovery check"""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time and \
               datetime.utcnow() - self._last_failure_time > timedelta(seconds=self.recovery_timeout):
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
        return self._state
    
    def record_success(self):
        """Record a successful call"""
        if self._state == CircuitState.HALF_OPEN:
            self._half_open_calls += 1
            if self._half_open_calls >= self.half_open_max_calls:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
        elif self._state == CircuitState.CLOSED:
            self._failure_count = 0
    
    def record_failure(self):
        """Record a failed call"""
        self._failure_count += 1
        self._last_failure_time = datetime.utcnow()
        
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
        elif self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
    
    def can_execute(self) -> bool:
        """Check if calls are allowed"""
        state = self.state  # This triggers recovery check
        if state == CircuitState.CLOSED:
            return True
        elif state == CircuitState.HALF_OPEN:
            return self._half_open_calls < self.half_open_max_calls
        return False


# Sensitive patterns to sanitize
SENSITIVE_PATTERNS = [
    r'(?i)password["\s:=]+["\']?[\w@#$%^&*!]+',
    r'(?i)api[_-]?key["\s:=]+["\']?[\w-]+',
    r'(?i)token["\s:=]+["\']?[\w.-]+',
    r'(?i)secret["\s:=]+["\']?[\w-]+',
    r'(?i)bearer\s+[\w.-]+',
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
    r'\b\d{16}\b',  # Credit card
]


class ErrorHandler:
    """
    Centralized error handler for the SPD pipeline.
    
    Usage:
        handler = ErrorHandler(module="bcpao_scraper")
        
        @handler.with_retry(max_retries=3)
        def fetch_data():
            ...
        
        try:
            result = fetch_data()
        except Exception as e:
            handler.handle(e, context={"parcel_id": "123"})
    """
    
    def __init__(
        self,
        module: str,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        log_level: int = logging.INFO,
    ):
        self.module = module
        self.supabase_url = supabase_url or os.environ.get("SUPABASE_URL")
        self.supabase_key = supabase_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        # Configure logging
        self.logger = logging.getLogger(f"spd.{module}")
        self.logger.setLevel(log_level)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(handler)
        
        # Circuit breakers by operation
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Error statistics
        self._error_counts: Dict[str, int] = {}
    
    def get_circuit_breaker(self, operation: str) -> CircuitBreaker:
        """Get or create circuit breaker for an operation"""
        if operation not in self._circuit_breakers:
            self._circuit_breakers[operation] = CircuitBreaker(name=operation)
        return self._circuit_breakers[operation]
    
    def classify_error(self, exception: Exception) -> tuple:
        """Classify an exception into category and severity"""
        exc_type = type(exception).__name__
        exc_msg = str(exception).lower()
        
        # Network errors
        if any(x in exc_type for x in ['Connection', 'Timeout', 'HTTP', 'URL', 'Socket']):
            return ErrorCategory.NETWORK, ErrorSeverity.WARNING, True
        
        # Database errors
        if any(x in exc_type for x in ['Database', 'SQL', 'Postgres', 'Supabase']):
            if 'duplicate' in exc_msg or 'unique' in exc_msg:
                return ErrorCategory.VALIDATION, ErrorSeverity.WARNING, False
            return ErrorCategory.DATABASE, ErrorSeverity.ERROR, True
        
        # Authentication/Authorization
        if any(x in exc_msg for x in ['unauthorized', '401', 'authentication']):
            return ErrorCategory.AUTHENTICATION, ErrorSeverity.ERROR, False
        if any(x in exc_msg for x in ['forbidden', '403', 'permission']):
            return ErrorCategory.AUTHORIZATION, ErrorSeverity.ERROR, False
        
        # Rate limiting
        if any(x in exc_msg for x in ['rate limit', '429', 'too many']):
            return ErrorCategory.RATE_LIMIT, ErrorSeverity.WARNING, True
        
        # Timeout
        if 'timeout' in exc_msg:
            return ErrorCategory.TIMEOUT, ErrorSeverity.WARNING, True
        
        # Parse errors
        if any(x in exc_type for x in ['JSON', 'Parse', 'Decode', 'Value']):
            return ErrorCategory.PARSE, ErrorSeverity.WARNING, False
        
        # Validation
        if any(x in exc_type for x in ['Validation', 'Invalid', 'Value']):
            return ErrorCategory.VALIDATION, ErrorSeverity.WARNING, False
        
        # Default
        return ErrorCategory.UNKNOWN, ErrorSeverity.ERROR, False
    
    def sanitize_message(self, message: str) -> str:
        """Remove sensitive data from error messages"""
        import re
        sanitized = message
        for pattern in SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized)
        return sanitized
    
    def create_error(
        self,
        exception: Exception,
        function: str = "unknown",
        additional_context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> StructuredError:
        """Create a structured error from an exception"""
        category, severity, is_retryable = self.classify_error(exception)
        
        context = ErrorContext(
            module=self.module,
            function=function,
            correlation_id=correlation_id,
            additional_data=additional_context or {},
        )
        
        # Generate error code
        error_hash = hashlib.md5(
            f"{category.value}:{type(exception).__name__}".encode()
        ).hexdigest()[:8]
        error_code = f"SPD-{category.value.upper()[:3]}-{error_hash}"
        
        return StructuredError(
            message=self.sanitize_message(str(exception)),
            category=category,
            severity=severity,
            context=context,
            original_exception=exception,
            stack_trace=traceback.format_exc(),
            error_code=error_code,
            is_retryable=is_retryable,
        )
    
    def handle(
        self,
        exception: Exception,
        function: str = "unknown",
        context: Optional[Dict[str, Any]] = None,
        reraise: bool = False,
    ) -> StructuredError:
        """
        Handle an exception with logging and optional storage.
        
        Args:
            exception: The exception to handle
            function: Name of the function where error occurred
            context: Additional context data
            reraise: Whether to re-raise the exception after handling
        
        Returns:
            StructuredError object
        """
        error = self.create_error(exception, function, context)
        
        # Update statistics
        key = f"{error.category.value}:{error.error_code}"
        self._error_counts[key] = self._error_counts.get(key, 0) + 1
        
        # Log the error
        log_method = getattr(self.logger, error.severity.value)
        log_method(
            f"[{error.error_code}] {error.message}",
            extra={"structured_error": error.to_dict()}
        )
        
        # Store in Supabase if configured
        if self.supabase_url and self.supabase_key:
            self._store_error_async(error)
        
        if reraise:
            raise exception
        
        return error
    
    def _store_error_async(self, error: StructuredError):
        """Store error in Supabase asynchronously"""
        try:
            import urllib.request
            
            data = {
                "error_code": error.error_code,
                "category": error.category.value,
                "severity": error.severity.value,
                "module": error.context.module,
                "function": error.context.function,
                "message": error.message[:500],  # Truncate
                "context": json.dumps(error.context.additional_data),
                "created_at": error.context.timestamp.isoformat(),
            }
            
            req = urllib.request.Request(
                f"{self.supabase_url}/rest/v1/error_logs",
                data=json.dumps(data).encode(),
                headers={
                    "Content-Type": "application/json",
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                },
                method="POST"
            )
            
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            self.logger.debug(f"Failed to store error in Supabase: {e}")
    
    def with_retry(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        operation: Optional[str] = None,
    ):
        """
        Decorator for automatic retry with exponential backoff.
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries (seconds)
            max_delay: Maximum delay between retries (seconds)
            exponential_base: Base for exponential backoff
            operation: Operation name for circuit breaker
        """
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            op_name = operation or func.__name__
            circuit_breaker = self.get_circuit_breaker(op_name)
            
            @wraps(func)
            def wrapper(*args, **kwargs) -> T:
                if not circuit_breaker.can_execute():
                    raise RuntimeError(
                        f"Circuit breaker open for {op_name}. "
                        f"Try again in {circuit_breaker.recovery_timeout}s"
                    )
                
                last_exception = None
                for attempt in range(max_retries + 1):
                    try:
                        result = func(*args, **kwargs)
                        circuit_breaker.record_success()
                        return result
                    except Exception as e:
                        last_exception = e
                        error = self.create_error(e, func.__name__)
                        error.retry_count = attempt + 1
                        
                        if not error.is_retryable or attempt >= max_retries:
                            circuit_breaker.record_failure()
                            self.handle(e, func.__name__, {"attempt": attempt + 1})
                            raise
                        
                        # Calculate delay with exponential backoff
                        delay = min(
                            base_delay * (exponential_base ** attempt),
                            max_delay
                        )
                        
                        self.logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                            f"after {delay:.1f}s: {error.message}"
                        )
                        
                        import time
                        time.sleep(delay)
                
                raise last_exception
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> T:
                if not circuit_breaker.can_execute():
                    raise RuntimeError(
                        f"Circuit breaker open for {op_name}. "
                        f"Try again in {circuit_breaker.recovery_timeout}s"
                    )
                
                last_exception = None
                for attempt in range(max_retries + 1):
                    try:
                        result = await func(*args, **kwargs)
                        circuit_breaker.record_success()
                        return result
                    except Exception as e:
                        last_exception = e
                        error = self.create_error(e, func.__name__)
                        error.retry_count = attempt + 1
                        
                        if not error.is_retryable or attempt >= max_retries:
                            circuit_breaker.record_failure()
                            self.handle(e, func.__name__, {"attempt": attempt + 1})
                            raise
                        
                        delay = min(
                            base_delay * (exponential_base ** attempt),
                            max_delay
                        )
                        
                        self.logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                            f"after {delay:.1f}s: {error.message}"
                        )
                        
                        await asyncio.sleep(delay)
                
                raise last_exception
            
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return wrapper
        
        return decorator
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "error_counts": dict(self._error_counts),
            "circuit_breakers": {
                name: {
                    "state": cb.state.value,
                    "failure_count": cb._failure_count,
                }
                for name, cb in self._circuit_breakers.items()
            },
        }


# Global handler registry
_handlers: Dict[str, ErrorHandler] = {}


def get_error_handler(module: str) -> ErrorHandler:
    """Get or create an error handler for a module"""
    if module not in _handlers:
        _handlers[module] = ErrorHandler(module)
    return _handlers[module]


# Convenience decorator
def with_error_handling(
    module: str,
    max_retries: int = 3,
    reraise: bool = True,
):
    """
    Convenience decorator for error handling with retry.
    
    Usage:
        @with_error_handling("bcpao_scraper", max_retries=3)
        def fetch_parcel_data(account_id):
            ...
    """
    handler = get_error_handler(module)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @handler.with_retry(max_retries=max_retries)
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler.handle(e, func.__name__, reraise=reraise)
        
        return wrapper
    
    return decorator


if __name__ == "__main__":
    # Test the error handler
    logging.basicConfig(level=logging.DEBUG)
    
    handler = ErrorHandler("test_module")
    
    # Test error handling
    try:
        raise ValueError("Test error with password=secret123")
    except Exception as e:
        error = handler.handle(e, "test_function", {"test": "data"})
        print(f"Handled error: {error.error_code}")
        print(f"Sanitized message: {error.message}")
    
    # Test retry decorator
    @handler.with_retry(max_retries=2, base_delay=0.1)
    def flaky_function():
        import random
        if random.random() < 0.7:
            raise ConnectionError("Network failed")
        return "success"
    
    try:
        result = flaky_function()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed after retries: {e}")
    
    # Print statistics
    print(f"\nStatistics: {handler.get_statistics()}")
