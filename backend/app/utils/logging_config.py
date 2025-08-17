"""
Comprehensive logging configuration for the FlowPlane trading platform
"""
import logging
import logging.config
import logging.handlers
import sys
import json
import traceback
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import os

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add custom fields
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        
        if hasattr(record, 'operation'):
            log_entry["operation"] = record.operation
        
        if hasattr(record, 'duration'):
            log_entry["duration_ms"] = record.duration
        
        if hasattr(record, 'service'):
            log_entry["service"] = record.service
        
        if hasattr(record, 'ticker'):
            log_entry["ticker"] = record.ticker
        
        return json.dumps(log_entry)

class ColoredConsoleFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Build log message
        log_message = f"{color}[{timestamp}] {record.levelname:8} {record.name:20} {record.getMessage()}{reset}"
        
        # Add location info for warnings and errors
        if record.levelno >= logging.WARNING:
            log_message += f" ({record.filename}:{record.lineno})"
        
        return log_message

class TradingLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter for trading operations"""
    
    def process(self, msg, kwargs):
        # Add context to the log record
        extra = kwargs.get('extra', {})
        
        # Add default context
        if 'request_id' in self.extra:
            extra['request_id'] = self.extra['request_id']
        
        if 'operation' in self.extra:
            extra['operation'] = self.extra['operation']
        
        kwargs['extra'] = extra
        return msg, kwargs

class PerformanceLogger:
    """Logger for performance metrics"""
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)
    
    def log_scan_performance(self,
                           scan_id: str,
                           duration: float,
                           opportunities_found: int,
                           tickers_scanned: int,
                           success: bool = True):
        """Log scan performance metrics"""
        self.logger.info(
            "Scan completed",
            extra={
                "operation": "market_scan",
                "scan_id": scan_id,
                "duration": duration * 1000,  # Convert to milliseconds
                "opportunities_found": opportunities_found,
                "tickers_scanned": tickers_scanned,
                "success": success,
                "scan_rate": tickers_scanned / duration if duration > 0 else 0
            }
        )
    
    def log_api_call(self,
                    service: str,
                    endpoint: str,
                    duration: float,
                    success: bool = True,
                    status_code: int = None,
                    error: str = None):
        """Log API call performance"""
        extra = {
            "operation": "api_call",
            "service": service,
            "endpoint": endpoint,
            "duration": duration * 1000,
            "success": success
        }
        
        if status_code:
            extra["status_code"] = status_code
        
        if error:
            extra["error"] = error
        
        if success:
            self.logger.info(f"API call to {service} completed", extra=extra)
        else:
            self.logger.error(f"API call to {service} failed", extra=extra)

class SecurityLogger:
    """Logger for security events"""
    
    def __init__(self, logger_name: str = "security"):
        self.logger = logging.getLogger(logger_name)
    
    def log_api_key_usage(self, service: str, success: bool = True):
        """Log API key usage"""
        self.logger.info(
            f"API key used for {service}",
            extra={
                "operation": "api_key_usage",
                "service": service,
                "success": success
            }
        )
    
    def log_rate_limit_hit(self, service: str, limit_type: str):
        """Log rate limit events"""
        self.logger.warning(
            f"Rate limit hit for {service}",
            extra={
                "operation": "rate_limit",
                "service": service,
                "limit_type": limit_type
            }
        )
    
    def log_suspicious_activity(self, activity: str, details: Dict):
        """Log suspicious activity"""
        self.logger.warning(
            f"Suspicious activity detected: {activity}",
            extra={
                "operation": "security_event",
                "activity": activity,
                **details
            }
        )

def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    structured_logs: bool = True,
    log_dir: str = "logs"
) -> None:
    """
    Setup comprehensive logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to files
        log_to_console: Whether to log to console
        structured_logs: Whether to use structured (JSON) logging
        log_dir: Directory for log files
    """
    
    # Create logs directory
    if log_to_file:
        Path(log_dir).mkdir(exist_ok=True)
    
    # Base logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "()": StructuredFormatter,
            },
            "colored_console": {
                "()": ColoredConsoleFormatter,
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {},
        "loggers": {
            "": {  # Root logger
                "level": log_level,
                "handlers": [],
                "propagate": False
            },
            "scanner": {
                "level": log_level,
                "handlers": [],
                "propagate": False
            },
            "api": {
                "level": log_level,
                "handlers": [],
                "propagate": False
            },
            "performance": {
                "level": "INFO",
                "handlers": [],
                "propagate": False
            },
            "security": {
                "level": "INFO",
                "handlers": [],
                "propagate": False
            },
            "database": {
                "level": log_level,
                "handlers": [],
                "propagate": False
            }
        }
    }
    
    # Console handler
    if log_to_console:
        config["handlers"]["console"] = {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "colored_console",
            "stream": "ext://sys.stdout"
        }
        
        # Add console handler to all loggers
        for logger_name in config["loggers"]:
            config["loggers"][logger_name]["handlers"].append("console")
    
    # File handlers
    if log_to_file:
        formatter = "structured" if structured_logs else "simple"
        
        # General application log
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": formatter,
            "filename": f"{log_dir}/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
        
        # Error log
        config["handlers"]["error_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": formatter,
            "filename": f"{log_dir}/error.log",
            "maxBytes": 10485760,
            "backupCount": 5
        }
        
        # Performance log
        config["handlers"]["performance_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": formatter,
            "filename": f"{log_dir}/performance.log",
            "maxBytes": 10485760,
            "backupCount": 5
        }
        
        # Security log
        config["handlers"]["security_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": formatter,
            "filename": f"{log_dir}/security.log",
            "maxBytes": 10485760,
            "backupCount": 5
        }
        
        # Scanner-specific log
        config["handlers"]["scanner_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": formatter,
            "filename": f"{log_dir}/scanner.log",
            "maxBytes": 10485760,
            "backupCount": 5
        }
        
        # Add file handlers to loggers
        config["loggers"][""]["handlers"].extend(["file", "error_file"])
        config["loggers"]["scanner"]["handlers"].append("scanner_file")
        config["loggers"]["performance"]["handlers"].append("performance_file")
        config["loggers"]["security"]["handlers"].append("security_file")
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Log startup
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging system initialized",
        extra={
            "operation": "logging_setup",
            "log_level": log_level,
            "log_to_file": log_to_file,
            "log_to_console": log_to_console,
            "structured_logs": structured_logs
        }
    )

def get_trading_logger(name: str, request_id: str = None, operation: str = None) -> TradingLoggerAdapter:
    """
    Get a trading logger with context
    
    Args:
        name: Logger name
        request_id: Request ID for correlation
        operation: Operation being performed
    
    Returns:
        Configured logger adapter
    """
    logger = logging.getLogger(name)
    
    extra = {}
    if request_id:
        extra["request_id"] = request_id
    if operation:
        extra["operation"] = operation
    
    return TradingLoggerAdapter(logger, extra)

def log_function_call(logger: logging.Logger):
    """Decorator to log function calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            
            logger.debug(
                f"Calling {func.__name__}",
                extra={
                    "operation": "function_call",
                    "function": func.__name__,
                    "args_count": len(args),
                    "kwargs_count": len(kwargs)
                }
            )
            
            try:
                result = func(*args, **kwargs)
                
                duration = (datetime.now() - start_time).total_seconds()
                logger.debug(
                    f"Completed {func.__name__}",
                    extra={
                        "operation": "function_complete",
                        "function": func.__name__,
                        "duration": duration * 1000,
                        "success": True
                    }
                )
                
                return result
                
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(
                    f"Failed {func.__name__}: {e}",
                    extra={
                        "operation": "function_error",
                        "function": func.__name__,
                        "duration": duration * 1000,
                        "success": False,
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator

# Global logger instances
performance_logger = PerformanceLogger()
security_logger = SecurityLogger()

# Initialize logging on import
if __name__ != "__main__":
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_to_file = os.getenv("LOG_TO_FILE", "true").lower() == "true"
    structured_logs = os.getenv("STRUCTURED_LOGS", "true").lower() == "true"
    
    setup_logging(
        log_level=log_level,
        log_to_file=log_to_file,
        structured_logs=structured_logs
    )