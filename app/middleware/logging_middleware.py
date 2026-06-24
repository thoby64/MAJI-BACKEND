"""
Request Logging Middleware
Logs all incoming requests and outgoing responses
"""

import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Log request details and response details
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler
            
        Returns:
            Response from next middleware/route handler
        """
        # Log request details
        start_time = time.time()
        
        logger.info(
            f"[REQUEST] {request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response details
            logger.info(
                f"[RESPONSE] {request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Duration: {process_time:.3f}s"
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
        
        except Exception as exc:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                f"[ERROR] {request.method} {request.url.path} - "
                f"Duration: {process_time:.3f}s - "
                f"Error: {str(exc)}",
                exc_info=True
            )
            raise
