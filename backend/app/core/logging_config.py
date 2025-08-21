"""
Structured Logging Configuration
F002-US001 Slice 3 Task 18: Comprehensive error logging for backtesting and indicators
Provides structured logging with context for better debugging and monitoring
"""

import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger
from app.core.config import settings

class StructuredLogger:
    """
    Structured logger for backtesting and indicator operations
    F002-US001 Slice 3 Task 18: Enhanced error logging with context
    
    Features:
    - JSON structured logging
    - Context-aware error tracking
    - Performance metrics logging
    - Error categorization
    - Correlation IDs for tracing
    """
    
    def __init__(self):
        """Initialize structured logging configuration"""
        self.setup_logging()
        self.correlation_id_counter = 0
        
        # Error categories for classification
        self.error_categories = {
            'DATA_ERROR': 'Data fetch or quality issues',
            'CALCULATION_ERROR': 'Technical indicator calculation errors',
            'BACKTEST_ERROR': 'Backtesting engine errors', 
            'VALIDATION_ERROR': 'Data validation failures',
            'TIMEOUT_ERROR': 'Operation timeout errors',
            'API_ERROR': 'External API errors',
            'SYSTEM_ERROR': 'System/infrastructure errors'
        }
    
    def setup_logging(self):
        """Configure loguru for structured logging"""
        # Remove default logger
        logger.remove()
        
        # Add structured JSON logger for file output
        logger.add(
            "logs/trading_platform.json",
            rotation="100 MB",
            retention="30 days",
            format=self._json_formatter,
            level="INFO",
            enqueue=True,
            serialize=True
        )
        
        # Add human-readable logger for console (development)
        if settings.DEBUG:
            logger.add(
                sys.stderr,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
                level="DEBUG"
            )
        else:
            logger.add(
                sys.stderr,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
                level="WARNING"
            )
        
        # Add error-specific logger for critical issues
        logger.add(
            "logs/errors.json",
            rotation="50 MB",
            retention="90 days",
            format=self._json_formatter,
            level="ERROR",
            enqueue=True,
            serialize=True
        )
    
    def _json_formatter(self, record):
        """Format log records as structured JSON"""
        # Extract extra data
        extra = record.get("extra", {})
        
        # Build structured log entry
        log_entry = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "logger": record["name"],
            "function": record["function"],
            "line": record["line"],
            "message": record["message"],
            "module": record["module"],
            "thread_id": record["thread"].id if record.get("thread") else None,
            "process_id": record["process"].id if record.get("process") else None
        }
        
        # Add context data if available
        if extra:
            log_entry["context"] = extra
        
        # Add exception info if present
        if record.get("exception"):
            log_entry["exception"] = {
                "type": record["exception"].type.__name__ if record["exception"].type else None,
                "value": str(record["exception"].value) if record["exception"].value else None,
                "traceback": record["exception"].traceback if record["exception"].traceback else None
            }
        
        return json.dumps(log_entry, default=str)
    
    def generate_correlation_id(self) -> str:
        """Generate unique correlation ID for request tracing"""
        self.correlation_id_counter += 1
        timestamp = int(datetime.utcnow().timestamp() * 1000)
        return f"req_{timestamp}_{self.correlation_id_counter:04d}"
    
    def log_backtest_start(
        self, 
        correlation_id: str,
        symbol: str, 
        strategy: str, 
        parameters: Dict[str, Any],
        data_period: Dict[str, str]
    ):
        """Log backtest operation start with context"""
        logger.info(
            "Backtest operation started",
            correlation_id=correlation_id,
            operation="backtest_start",
            symbol=symbol,
            strategy=strategy,
            parameters=parameters,
            data_period=data_period,
            category="BACKTEST_OPERATION"
        )
    
    def log_backtest_success(
        self,
        correlation_id: str,
        symbol: str,
        strategy: str,
        performance_metrics: Dict[str, Any],
        execution_time: float
    ):
        """Log successful backtest completion with metrics"""
        logger.info(
            "Backtest operation completed successfully",
            correlation_id=correlation_id,
            operation="backtest_success",
            symbol=symbol,
            strategy=strategy,
            performance_metrics=performance_metrics,
            execution_time_seconds=execution_time,
            category="BACKTEST_OPERATION"
        )
    
    def log_backtest_error(
        self,
        correlation_id: str,
        symbol: str,
        strategy: str,
        error: Exception,
        error_category: str = "BACKTEST_ERROR",
        context: Optional[Dict[str, Any]] = None
    ):
        """Log backtest operation error with detailed context"""
        error_context = {
            "correlation_id": correlation_id,
            "operation": "backtest_error", 
            "symbol": symbol,
            "strategy": strategy,
            "error_category": error_category,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "category": "BACKTEST_ERROR"
        }
        
        if context:
            error_context.update(context)
        
        logger.error(
            f"Backtest operation failed for {strategy} on {symbol}: {str(error)}",
            **error_context
        )
    
    def log_indicator_calculation(
        self,
        correlation_id: str,
        indicator_name: str,
        symbol: str,
        parameters: Dict[str, Any],
        data_points: int,
        execution_time: float
    ):
        """Log technical indicator calculation"""
        logger.info(
            f"Technical indicator {indicator_name} calculated",
            correlation_id=correlation_id,
            operation="indicator_calculation",
            indicator_name=indicator_name,
            symbol=symbol,
            parameters=parameters,
            data_points=data_points,
            execution_time_seconds=execution_time,
            category="INDICATOR_OPERATION"
        )
    
    def log_indicator_error(
        self,
        correlation_id: str,
        indicator_name: str,
        symbol: str,
        error: Exception,
        parameters: Optional[Dict[str, Any]] = None,
        data_points: Optional[int] = None
    ):
        """Log technical indicator calculation error"""
        error_context = {
            "correlation_id": correlation_id,
            "operation": "indicator_error",
            "indicator_name": indicator_name,
            "symbol": symbol,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "category": "CALCULATION_ERROR"
        }
        
        if parameters:
            error_context["parameters"] = parameters
        if data_points:
            error_context["data_points"] = data_points
        
        logger.error(
            f"Technical indicator {indicator_name} calculation failed for {symbol}: {str(error)}",
            **error_context
        )
    
    def log_data_quality_validation(
        self,
        correlation_id: str,
        symbol: str,
        validation_result: Dict[str, Any],
        data_source: str,
        execution_time: float
    ):
        """Log data quality validation results"""
        logger.info(
            f"Data quality validation completed for {symbol}",
            correlation_id=correlation_id,
            operation="data_quality_validation",
            symbol=symbol,
            validation_passed=validation_result.get('data_quality_passed', False),
            data_source=data_source,
            errors_count=len(validation_result.get('quality_errors', [])),
            warnings_count=len(validation_result.get('quality_warnings', [])),
            execution_time_seconds=execution_time,
            category="DATA_VALIDATION"
        )
    
    def log_data_fetch_error(
        self,
        correlation_id: str,
        symbol: str,
        data_source: str,
        error: Exception,
        fallback_used: bool = False,
        retry_attempt: Optional[int] = None
    ):
        """Log data fetching errors with fallback context"""
        error_context = {
            "correlation_id": correlation_id,
            "operation": "data_fetch_error",
            "symbol": symbol,
            "data_source": data_source,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "fallback_used": fallback_used,
            "category": "DATA_ERROR"
        }
        
        if retry_attempt is not None:
            error_context["retry_attempt"] = retry_attempt
        
        logger.error(
            f"Data fetch failed for {symbol} from {data_source}: {str(error)}",
            **error_context
        )
    
    def log_timeout_error(
        self,
        correlation_id: str,
        operation: str,
        timeout_seconds: float,
        elapsed_seconds: float,
        context: Optional[Dict[str, Any]] = None
    ):
        """Log timeout errors with performance context"""
        error_context = {
            "correlation_id": correlation_id,
            "operation": f"{operation}_timeout",
            "timeout_limit_seconds": timeout_seconds,
            "elapsed_seconds": elapsed_seconds,
            "timeout_exceeded_by": elapsed_seconds - timeout_seconds,
            "category": "TIMEOUT_ERROR"
        }
        
        if context:
            error_context.update(context)
        
        logger.error(
            f"Operation {operation} timed out after {elapsed_seconds:.1f}s (limit: {timeout_seconds}s)",
            **error_context
        )
    
    def log_performance_metrics(
        self,
        correlation_id: str,
        operation: str,
        metrics: Dict[str, Any]
    ):
        """Log performance metrics for monitoring"""
        logger.info(
            f"Performance metrics for {operation}",
            correlation_id=correlation_id,
            operation="performance_metrics",
            measured_operation=operation,
            metrics=metrics,
            category="PERFORMANCE"
        )
    
    def log_api_error(
        self,
        correlation_id: str,
        api_name: str,
        endpoint: str,
        status_code: Optional[int],
        error: Exception,
        response_time: Optional[float] = None
    ):
        """Log external API errors"""
        error_context = {
            "correlation_id": correlation_id,
            "operation": "api_error",
            "api_name": api_name,
            "endpoint": endpoint,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "category": "API_ERROR"
        }
        
        if status_code:
            error_context["status_code"] = status_code
        if response_time:
            error_context["response_time_seconds"] = response_time
        
        logger.error(
            f"API error for {api_name} at {endpoint}: {str(error)}",
            **error_context
        )

# Global structured logger instance
structured_logger = StructuredLogger()