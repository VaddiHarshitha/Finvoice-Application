import logging
from datetime import datetime
from fastapi import HTTPException
from typing import Optional, Dict, Any
import traceback
import json
from pathlib import Path

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.FileHandler('logs/errors.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
error_logger = logging.getLogger('errors')

class AppError(Exception):
    """Base application error"""
    def __init__(self, message: str, status_code: int = 500, details: Dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(AppError):
    """Validation error (400)"""
    def __init__(self, message: str, field: str = None, details: Dict = None):
        details = details or {}
        if field:
            details['field'] = field
        super().__init__(message, 400, details)

class AuthenticationError(AppError):
    """Authentication error (401)"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401)

class AuthorizationError(AppError):
    """Authorization error (403)"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, 403)

class NotFoundError(AppError):
    """Not found error (404)"""
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, 404, {"resource": resource, "identifier": identifier})

class BankingError(AppError):
    """Banking operation error (500)"""
    def __init__(self, message: str, operation: str = None, details: Dict = None):
        details = details or {}
        if operation:
            details['operation'] = operation
        super().__init__(message, 500, details)
class ServiceUnavailableError(AppError):
    """Service unavailable error (503)"""
    def __init__(self, service: str):
        super().__init__(f"{service} is currently unavailable", 503, {"service": service})

def log_error(
    error: Exception,
    user_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    include_traceback: bool = True
) -> Dict[str, Any]:
    """
    Log error with full context
    
    Args:
        error: Exception object
        user_id: User identifier
        endpoint: API endpoint where error occurred
        context: Additional context data
        include_traceback: Include full traceback
        
    Returns:
        dict: Error information
    """
    error_data = {
        "timestamp": datetime.now().isoformat(),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "user_id": user_id,
        "endpoint": endpoint,
        "context": context or {},
    }
    
    # Add traceback if requested
    if include_traceback:
        error_data["traceback"] = traceback.format_exc()
    
    # Add custom error details if available
    if isinstance(error, AppError):
        error_data["status_code"] = error.status_code
        error_data["details"] = error.details
    
    # Log to appropriate file
    if isinstance(error, (ValidationError, NotFoundError)):
        logger.warning(json.dumps(error_data, indent=2))
    else:
        error_logger.error(json.dumps(error_data, indent=2))
    
    return error_data

def log_warning(
    message: str,
    user_id: Optional[str] = None,
    context: Optional[Dict] = None
):
    """Log warning message"""
    warning_data = {
        "timestamp": datetime.now().isoformat(),
        "message": message,
        "user_id": user_id,
        "context": context or {}
    }
    logger.warning(json.dumps(warning_data, indent=2))


def log_info(
    message: str,
    user_id: Optional[str] = None,
    context: Optional[Dict] = None
):
    """Log info message"""
    info_data = {
        "timestamp": datetime.now().isoformat(),
        "message": message,
        "user_id": user_id,
        "context": context or {}
    }
    logger.info(json.dumps(info_data, indent=2))

def handle_api_error(
    error: Exception,
    user_id: str = None,
    endpoint: str = None,
    context: Dict = None
) -> HTTPException:
    """
    Convert exception to HTTPException with proper logging
    
    Args:
        error: Exception to handle
        user_id: User identifier
        endpoint: API endpoint
        context: Additional context
        
    Returns:
        HTTPException with appropriate status code and message
    """
    # Log the error
    error_info = log_error(error, user_id, endpoint, context, include_traceback=True)
    
    # Convert to HTTPException
    if isinstance(error, HTTPException):
        return error
    
    elif isinstance(error, AppError):
        return HTTPException(
            status_code=error.status_code,
            detail={
                "error": error.message,
                "details": error.details,
                "timestamp": error_info["timestamp"]
            }
        )
    
    elif isinstance(error, ValueError):
        return HTTPException(
            status_code=400,
            detail={
                "error": "Invalid input",
                "message": str(error),
                "timestamp": error_info["timestamp"]
            }
        )
    
    elif isinstance(error, KeyError):
        return HTTPException(
            status_code=400,
            detail={
                "error": "Missing required field",
                "message": str(error),
                "timestamp": error_info["timestamp"]
            }
        )
    
    else:
        # Unknown error - don't expose details to user
        return HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred. Please try again later.",
                "timestamp": error_info["timestamp"],
                "error_id": error_info["timestamp"]  # For support reference
            }
        )

error_counts = {}

def track_error(endpoint: str, error_type: str):
    """Track error rates by endpoint"""
    key = f"{endpoint}:{error_type}"
    error_counts[key] = error_counts.get(key, 0) + 1


def get_error_stats() -> Dict[str, Any]:
    """Get error statistics"""
    return {
        "total_errors": sum(error_counts.values()),
        "by_endpoint": error_counts,
        "timestamp": datetime.now().isoformat()
    }

def validate_required_fields(data: Dict, required_fields: list) -> None:
    """
    Validate that all required fields are present
    
    Raises:
        ValidationError: If any required field is missing
    """
    missing = [field for field in required_fields if field not in data or not data[field]]
    
    if missing:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing)}",
            details={"missing_fields": missing}
        )


def validate_positive_number(value: float, field_name: str) -> None:
    """
    Validate that a number is positive
    
    Raises:
        ValidationError: If number is not positive
    """
    if value <= 0:
        raise ValidationError(
            f"{field_name} must be positive",
            field=field_name,
            details={"value": value}
        )


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """Safely divide two numbers, return default if division by zero"""
    try:
        return a / b
    except ZeroDivisionError:
        return default

if __name__ == "__main__":
    # Test error handling
    print(" Testing Error Handler...\n")
    
    # Test 1: ValidationError
    try:
        raise ValidationError("Invalid amount", field="amount")
    except Exception as e:
        http_exc = handle_api_error(e, "test_user", "/test")
        print(f"Test 1 - ValidationError: {http_exc.status_code}")
        print(f"   Detail: {http_exc.detail}\n")
    
    # Test 2: NotFoundError
    try:
        raise NotFoundError("User", "user123")
    except Exception as e:
        http_exc = handle_api_error(e, "test_user", "/test")
        print(f"Test 2 - NotFoundError: {http_exc.status_code}")
        print(f"   Detail: {http_exc.detail}\n")
    
    # Test 3: BankingError
    try:
        raise BankingError("Insufficient funds", operation="transfer", details={"balance": 100})
    except Exception as e:
        http_exc = handle_api_error(e, "test_user", "/test")
        print(f"Test 3 - BankingError: {http_exc.status_code}")
        print(f"   Detail: {http_exc.detail}\n")
    
    print(" Error handler tests complete!")

    print(f" Check logs/app.log and logs/errors.log")
