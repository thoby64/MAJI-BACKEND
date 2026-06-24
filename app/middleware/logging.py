"""
Logging Middleware
Request and response logging middleware
"""

import logging
import time
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Log request and response details"""
        
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.info(
            f"→ {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query": dict(request.query_params),
                "client": request.client.host if request.client else "unknown",
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"← {request.method} {request.url.path} - {response.status_code}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "elapsed_time_ms": round(elapsed_time * 1000, 2),
            }
        )
        
        # Add response headers
        response.headers["X-Process-Time"] = str(elapsed_time)
        
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to each request"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Add request ID to request and response"""
        import uuid
        
        # Generate or get request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Add to request
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add to response header
        response.headers["X-Request-ID"] = request_id
        
        return response


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
