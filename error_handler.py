"""
Enterprise Error Handling and Monitoring
"""

import logging
import traceback
from datetime import datetime
from functools import wraps
from typing import Any, Dict

from flask import jsonify, request

logger = logging.getLogger(__name__)


class ErrorCode:
    """Standardized error codes"""

    # Authentication errors (1000-1099)
    INVALID_CREDENTIALS = 1001
    ACCOUNT_LOCKED = 1002
    SESSION_EXPIRED = 1003
    INSUFFICIENT_PERMISSIONS = 1004

    # Validation errors (1100-1199)
    INVALID_INPUT = 1101
    MISSING_REQUIRED_FIELD = 1102
    INVALID_WALLET_ADDRESS = 1103
    INVALID_PRIVATE_KEY = 1104
    INVALID_MNEMONIC = 1105

    # Blockchain errors (1200-1299)
    BLOCKCHAIN_CONNECTION_FAILED = 1201
    WALLET_VALIDATION_FAILED = 1202
    INSUFFICIENT_BALANCE = 1203
    TRANSACTION_FAILED = 1204

    # System errors (1300-1399)
    DATABASE_ERROR = 1301
    EXTERNAL_SERVICE_ERROR = 1302
    FILE_OPERATION_ERROR = 1303
    RATE_LIMIT_EXCEEDED = 1304

    # Business logic errors (1400-1499)
    WALLET_ALREADY_CONNECTED = 1401
    DOWNLOAD_NOT_FOUND = 1402
    INVALID_DOWNLOAD_TOKEN = 1403


class BFGMinerException(Exception):
    """Base exception for BFGMiner application"""

    def __init__(
        self,
        message: str,
        error_code: int,
        details: Dict[str, Any] = None,
        http_status: int = 400,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.http_status = http_status
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response"""
        return {
            "success": False,
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
                "timestamp": self.timestamp.isoformat(),
            },
        }


class ValidationError(BFGMinerException):
    """Validation-related errors"""

    def __init__(self, message: str, field: str = None, value: Any = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)

        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_INPUT,
            details=details,
            http_status=400,
        )


class AuthenticationError(BFGMinerException):
    """Authentication-related errors"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message, error_code=ErrorCode.INVALID_CREDENTIALS, http_status=401
        )


class BlockchainError(BFGMinerException):
    """Blockchain-related errors"""

    def __init__(self, message: str, blockchain: str = "ethereum"):
        super().__init__(
            message=message,
            error_code=ErrorCode.BLOCKCHAIN_CONNECTION_FAILED,
            details={"blockchain": blockchain},
            http_status=503,
        )


class DatabaseError(BFGMinerException):
    """Database-related errors"""

    def __init__(self, message: str, operation: str = None):
        details = {}
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_ERROR,
            details=details,
            http_status=500,
        )


class ErrorHandler:
    """Centralized error handling"""

    def __init__(self, app=None, audit_logger=None):
        self.app = app
        self.audit_logger = audit_logger
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize error handlers for Flask app"""
        app.errorhandler(BFGMinerException)(self.handle_bfgminer_exception)
        app.errorhandler(400)(self.handle_bad_request)
        app.errorhandler(401)(self.handle_unauthorized)
        app.errorhandler(403)(self.handle_forbidden)
        app.errorhandler(404)(self.handle_not_found)
        app.errorhandler(429)(self.handle_rate_limit)
        app.errorhandler(500)(self.handle_internal_error)
        app.errorhandler(Exception)(self.handle_generic_exception)

    def handle_bfgminer_exception(self, error: BFGMinerException):
        """Handle custom BFGMiner exceptions"""
        self._log_error(error, "BFGMiner Exception")
        return jsonify(error.to_dict()), error.http_status

    def handle_bad_request(self, error):
        """Handle 400 Bad Request"""
        return self._create_error_response(ErrorCode.INVALID_INPUT, "Bad request", 400)

    def handle_unauthorized(self, error):
        """Handle 401 Unauthorized"""
        return self._create_error_response(
            ErrorCode.INVALID_CREDENTIALS, "Authentication required", 401
        )

    def handle_forbidden(self, error):
        """Handle 403 Forbidden"""
        return self._create_error_response(
            ErrorCode.INSUFFICIENT_PERMISSIONS, "Access forbidden", 403
        )

    def handle_not_found(self, error):
        """Handle 404 Not Found"""
        return self._create_error_response(
            ErrorCode.INVALID_INPUT, "Resource not found", 404
        )

    def handle_rate_limit(self, error):
        """Handle 429 Rate Limit Exceeded"""
        return self._create_error_response(
            ErrorCode.RATE_LIMIT_EXCEEDED, "Rate limit exceeded", 429
        )

    def handle_internal_error(self, error):
        """Handle 500 Internal Server Error"""
        self._log_error(error, "Internal Server Error")
        return self._create_error_response(
            ErrorCode.DATABASE_ERROR, "Internal server error", 500
        )

    def handle_generic_exception(self, error: Exception):
        """Handle any unhandled exception"""
        self._log_error(error, "Unhandled Exception")
        return self._create_error_response(
            ErrorCode.DATABASE_ERROR, "An unexpected error occurred", 500
        )

    def _create_error_response(self, error_code: int, message: str, status_code: int):
        """Create standardized error response"""
        response = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
        return jsonify(response), status_code

    def _log_error(self, error: Exception, error_type: str):
        """Log error with context information"""
        try:
            error_info = {
                "type": error_type,
                "message": str(error),
                "traceback": traceback.format_exc(),
                "request_url": request.url if request else None,
                "request_method": request.method if request else None,
                "request_ip": request.remote_addr if request else None,
                "user_agent": request.headers.get("User-Agent") if request else None,
            }

            logger.error(f"{error_type}: {error}", extra=error_info)

            # Log to audit system if available
            if self.audit_logger:
                self.audit_logger.log_security_event(
                    event_type="APPLICATION_ERROR",
                    severity=(
                        "HIGH"
                        if isinstance(error, BFGMinerException)
                        and error.http_status >= 500
                        else "MEDIUM"
                    ),
                    source_ip=request.remote_addr if request else None,
                    details=error_info,
                )

        except Exception as log_error:
            # Fallback logging if main logging fails
            print(f"Failed to log error: {log_error}")
            print(f"Original error: {error}")


def handle_exceptions(func):
    """Decorator for handling exceptions in route functions"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BFGMinerException:
            raise  # Re-raise custom exceptions
        except ValueError as e:
            raise ValidationError(f"Invalid value: {str(e)}")
        except KeyError as e:
            raise ValidationError(f"Missing required field: {str(e)}")
        except Exception as e:
            logger.error(f"Unhandled exception in {func.__name__}: {e}")
            raise BFGMinerException(
                message="An unexpected error occurred",
                error_code=ErrorCode.DATABASE_ERROR,
                http_status=500,
            )

    return wrapper


def validate_required_fields(required_fields: list):
    """Decorator to validate required fields in request data"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if request.is_json:
                data = request.get_json()
                missing_fields = [
                    field
                    for field in required_fields
                    if field not in data or not data[field]
                ]
                if missing_fields:
                    raise ValidationError(
                        f"Missing required fields: {', '.join(missing_fields)}",
                        field=missing_fields[0] if len(missing_fields) == 1 else None,
                    )
            return func(*args, **kwargs)

        return wrapper

    return decorator
