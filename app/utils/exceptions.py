"""
Custom Exceptions
Application-wide exception definitions with HTTP status codes
"""

from typing import Any, Optional


class MajiscopeException(Exception):
    """Base exception for all Majiscope errors"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Any] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)


class AuthenticationError(MajiscopeException):
    """Raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTH_ERROR",
        )


class AuthorizationError(MajiscopeException):
    """Raised when user doesn't have required permissions"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
        )


class ValidationError(MajiscopeException):
    """Raised when data validation fails"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class NotFoundError(MajiscopeException):
    """Raised when a resource is not found"""
    
    def __init__(self, resource_type: str, resource_id: str = None):
        msg = f"{resource_type} not found"
        if resource_id:
            msg += f" (ID: {resource_id})"
        
        super().__init__(
            message=msg,
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class ConflictError(MajiscopeException):
    """Raised when there's a conflict (e.g., duplicate email)"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT_ERROR",
            details=details,
        )


class InternalServerError(MajiscopeException):
    """Raised for internal server errors"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="INTERNAL_ERROR",
            details=details,
        )
