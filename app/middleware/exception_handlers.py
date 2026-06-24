"""
Exception Handlers
Global exception handling for the FastAPI application
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime
import logging

from app.utils.exceptions import MajiscopeException
from app.utils.response_models import APIError

logger = logging.getLogger(__name__)


def create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    request_path: str = None,
    details: dict = None,
) -> dict:
    """Create standardized error response"""
    return {
        "success": False,
        "error": error_code,
        "message": message,
        "details": details,
        "timestamp": datetime.utcnow().isoformat(),
        "path": request_path,
    }


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the app"""
    
    @app.exception_handler(MajiscopeException)
    async def majiscope_exception_handler(request: Request, exc: MajiscopeException):
        """Handle Majiscope custom exceptions"""
        logger.warning(
            f"Majiscope Exception: {exc.error_code} - {exc.message}",
            extra={
                "path": str(request.url.path),
                "error_code": exc.error_code,
                "status_code": exc.status_code,
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=create_error_response(
                status_code=exc.status_code,
                error_code=exc.error_code,
                message=exc.message,
                request_path=str(request.url.path),
                details=exc.details,
            ),
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors"""
        logger.warning(
            f"Validation Error at {request.url.path}",
            extra={
                "errors": exc.errors(),
                "body": str(exc.body) if hasattr(exc, 'body') else None,
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=create_error_response(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error_code="VALIDATION_ERROR",
                message="Request validation failed",
                request_path=str(request.url.path),
                details={"errors": exc.errors()},
            ),
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all unhandled exceptions"""
        logger.error(
            f"Unhandled Exception: {str(exc)}",
            exc_info=True,
            extra={"path": str(request.url.path)},
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=create_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred",
                request_path=str(request.url.path),
            ),
        )
