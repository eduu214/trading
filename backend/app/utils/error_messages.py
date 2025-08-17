"""
User-friendly error message generation and formatting
"""
from typing import Dict, List, Optional, Any
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorCategory(Enum):
    NETWORK = "network"
    API_LIMIT = "api_limit"
    DATA_VALIDATION = "data_validation"
    CONFIGURATION = "configuration"
    TIMEOUT = "timeout"
    AUTHENTICATION = "authentication"
    SYSTEM = "system"
    USER_INPUT = "user_input"

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class UserError:
    """Represents a user-friendly error"""
    
    def __init__(self,
                 code: str,
                 title: str,
                 message: str,
                 category: ErrorCategory,
                 severity: ErrorSeverity,
                 suggestions: List[str] = None,
                 technical_details: str = None,
                 timestamp: datetime = None):
        self.code = code
        self.title = title
        self.message = message
        self.category = category
        self.severity = severity
        self.suggestions = suggestions or []
        self.technical_details = technical_details
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "error_code": self.code,
            "title": self.title,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "suggestions": self.suggestions,
            "technical_details": self.technical_details,
            "timestamp": self.timestamp.isoformat()
        }

class ErrorMessageGenerator:
    """Generate user-friendly error messages"""
    
    def __init__(self):
        self.error_templates = self._load_error_templates()
    
    def _load_error_templates(self) -> Dict:
        """Load error message templates"""
        return {
            # Network errors
            "network_connection_failed": {
                "title": "Connection Failed",
                "message": "Unable to connect to the market data service. Please check your internet connection.",
                "category": ErrorCategory.NETWORK,
                "severity": ErrorSeverity.MEDIUM,
                "suggestions": [
                    "Check your internet connection",
                    "Verify that the service is not blocked by firewall",
                    "Try again in a few moments"
                ]
            },
            
            "network_timeout": {
                "title": "Request Timed Out",
                "message": "The request took too long to complete. The service may be experiencing high load.",
                "category": ErrorCategory.NETWORK,
                "severity": ErrorSeverity.MEDIUM,
                "suggestions": [
                    "Try again with a smaller request",
                    "Check if the service is experiencing issues",
                    "Wait a few minutes before retrying"
                ]
            },
            
            # API limit errors
            "api_rate_limit_exceeded": {
                "title": "Rate Limit Exceeded",
                "message": "You've made too many requests in a short time. Please wait before trying again.",
                "category": ErrorCategory.API_LIMIT,
                "severity": ErrorSeverity.MEDIUM,
                "suggestions": [
                    "Wait {wait_time} seconds before retrying",
                    "Consider upgrading your API plan for higher limits",
                    "Reduce the frequency of your requests"
                ]
            },
            
            "api_quota_exceeded": {
                "title": "API Quota Exceeded",
                "message": "You've reached your daily API usage limit.",
                "category": ErrorCategory.API_LIMIT,
                "severity": ErrorSeverity.HIGH,
                "suggestions": [
                    "Wait until tomorrow for your quota to reset",
                    "Upgrade to a higher tier plan",
                    "Use cached data when possible"
                ]
            },
            
            # Authentication errors
            "api_key_invalid": {
                "title": "Invalid API Key",
                "message": "The API key you provided is not valid or has expired.",
                "category": ErrorCategory.AUTHENTICATION,
                "severity": ErrorSeverity.HIGH,
                "suggestions": [
                    "Check that your API key is entered correctly",
                    "Verify that your API key hasn't expired",
                    "Generate a new API key if needed"
                ]
            },
            
            # Data validation errors
            "invalid_ticker": {
                "title": "Invalid Ticker Symbol",
                "message": "The ticker symbol '{ticker}' is not recognized or supported.",
                "category": ErrorCategory.DATA_VALIDATION,
                "severity": ErrorSeverity.LOW,
                "suggestions": [
                    "Check the spelling of the ticker symbol",
                    "Verify that the symbol exists on the exchange",
                    "Try using the full company name to search"
                ]
            },
            
            "invalid_date_range": {
                "title": "Invalid Date Range",
                "message": "The date range you specified is not valid.",
                "category": ErrorCategory.DATA_VALIDATION,
                "severity": ErrorSeverity.LOW,
                "suggestions": [
                    "Ensure the start date is before the end date",
                    "Check that dates are not in the future",
                    "Use the format YYYY-MM-DD for dates"
                ]
            },
            
            # Configuration errors
            "scan_config_invalid": {
                "title": "Invalid Scan Configuration",
                "message": "One or more scan parameters are not valid.",
                "category": ErrorCategory.CONFIGURATION,
                "severity": ErrorSeverity.MEDIUM,
                "suggestions": [
                    "Check that all numeric values are within valid ranges",
                    "Ensure required fields are filled",
                    "Reset to default configuration if needed"
                ]
            },
            
            # Timeout errors
            "scan_timeout": {
                "title": "Scan Timed Out",
                "message": "The market scan took too long to complete and was stopped.",
                "category": ErrorCategory.TIMEOUT,
                "severity": ErrorSeverity.MEDIUM,
                "suggestions": [
                    "Try reducing the scope of your scan",
                    "Use fewer asset classes",
                    "Increase timeout limits in settings"
                ]
            },
            
            # System errors
            "database_error": {
                "title": "Database Error",
                "message": "There was a problem accessing the database.",
                "category": ErrorCategory.SYSTEM,
                "severity": ErrorSeverity.HIGH,
                "suggestions": [
                    "Try refreshing the page",
                    "Contact support if the problem persists",
                    "Check system status page"
                ]
            },
            
            "service_unavailable": {
                "title": "Service Temporarily Unavailable",
                "message": "The service is currently unavailable. We're working to restore it.",
                "category": ErrorCategory.SYSTEM,
                "severity": ErrorSeverity.HIGH,
                "suggestions": [
                    "Try again in a few minutes",
                    "Check the system status page",
                    "Use cached data if available"
                ]
            }
        }
    
    def generate_error(self,
                      error_code: str,
                      context: Dict = None,
                      technical_details: str = None) -> UserError:
        """Generate a user-friendly error message"""
        
        if error_code not in self.error_templates:
            return self._generate_generic_error(error_code, technical_details)
        
        template = self.error_templates[error_code]
        context = context or {}
        
        # Format message with context
        message = template["message"].format(**context)
        
        # Format suggestions with context
        suggestions = []
        for suggestion in template.get("suggestions", []):
            try:
                suggestions.append(suggestion.format(**context))
            except KeyError:
                suggestions.append(suggestion)
        
        return UserError(
            code=error_code,
            title=template["title"],
            message=message,
            category=template["category"],
            severity=template["severity"],
            suggestions=suggestions,
            technical_details=technical_details
        )
    
    def _generate_generic_error(self, error_code: str, technical_details: str = None) -> UserError:
        """Generate a generic error message"""
        return UserError(
            code=error_code,
            title="An Error Occurred",
            message="Something went wrong while processing your request.",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            suggestions=[
                "Try refreshing the page",
                "Check your internet connection",
                "Contact support if the problem persists"
            ],
            technical_details=technical_details
        )
    
    def generate_from_exception(self, exception: Exception, context: Dict = None) -> UserError:
        """Generate error from Python exception"""
        error_code = self._map_exception_to_error_code(exception)
        technical_details = f"{type(exception).__name__}: {str(exception)}"
        
        return self.generate_error(error_code, context, technical_details)
    
    def _map_exception_to_error_code(self, exception: Exception) -> str:
        """Map Python exceptions to error codes"""
        exception_mappings = {
            "ConnectionError": "network_connection_failed",
            "TimeoutError": "network_timeout",
            "HTTPError": self._map_http_error,
            "ValueError": "invalid_data",
            "KeyError": "missing_required_field",
            "FileNotFoundError": "resource_not_found",
            "PermissionError": "access_denied"
        }
        
        exception_name = type(exception).__name__
        
        if exception_name in exception_mappings:
            mapper = exception_mappings[exception_name]
            if callable(mapper):
                return mapper(exception)
            return mapper
        
        return "unknown_error"
    
    def _map_http_error(self, exception) -> str:
        """Map HTTP errors to specific error codes"""
        if hasattr(exception, 'response') and hasattr(exception.response, 'status_code'):
            status_code = exception.response.status_code
            
            if status_code == 401:
                return "api_key_invalid"
            elif status_code == 403:
                return "access_denied"
            elif status_code == 429:
                return "api_rate_limit_exceeded"
            elif status_code >= 500:
                return "service_unavailable"
        
        return "network_connection_failed"

class ErrorResponseBuilder:
    """Build structured error responses for API"""
    
    def __init__(self):
        self.generator = ErrorMessageGenerator()
    
    def build_error_response(self,
                           error_code: str,
                           context: Dict = None,
                           technical_details: str = None,
                           request_id: str = None) -> Dict:
        """Build a complete error response"""
        user_error = self.generator.generate_error(error_code, context, technical_details)
        
        response = {
            "success": False,
            "error": user_error.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
        
        if request_id:
            response["request_id"] = request_id
        
        return response
    
    def build_validation_error_response(self, validation_errors: List[str]) -> Dict:
        """Build response for validation errors"""
        return {
            "success": False,
            "error": {
                "error_code": "validation_failed",
                "title": "Validation Failed",
                "message": "One or more input values are invalid.",
                "category": ErrorCategory.USER_INPUT.value,
                "severity": ErrorSeverity.LOW.value,
                "validation_errors": validation_errors,
                "suggestions": [
                    "Check all input fields for errors",
                    "Ensure all required fields are filled",
                    "Use the correct format for dates and numbers"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def build_success_response(self, data: Any, message: str = None) -> Dict:
        """Build a success response"""
        response = {
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        if message:
            response["message"] = message
        
        return response

# Global instances
error_generator = ErrorMessageGenerator()
error_response_builder = ErrorResponseBuilder()

def create_user_error(error_code: str, context: Dict = None, technical_details: str = None) -> UserError:
    """Convenience function to create user error"""
    return error_generator.generate_error(error_code, context, technical_details)

def create_error_response(error_code: str, context: Dict = None, technical_details: str = None) -> Dict:
    """Convenience function to create error response"""
    return error_response_builder.build_error_response(error_code, context, technical_details)