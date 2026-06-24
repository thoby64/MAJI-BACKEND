"""
Global Exception Handlers
Centralized error handling for all API endpoints
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging


logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI):
    """
    Register all global exception handlers
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle ValueError exceptions"""
        logger.warning(f"ValueError in {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Invalid value",
                "message": str(exc),
                "path": str(request.url.path),
            },
        )
    
    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        """Handle database integrity constraint violations"""
        logger.error(f"Integrity error in {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "Database constraint violation",
                "message": "A resource with this data already exists",
                "path": str(request.url.path),
            },
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
        """Handle SQLAlchemy database errors"""
        logger.error(f"Database error in {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Database error",
                "message": "An error occurred while processing your request",
                "path": str(request.url.path),
            },
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle any unhandled exceptions"""
        logger.error(f"Unhandled exception in {request.url.path}: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "path": str(request.url.path),
            },
        )
