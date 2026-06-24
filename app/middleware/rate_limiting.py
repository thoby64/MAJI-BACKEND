"""
Rate Limiting Middleware
Simple in-memory rate limiting for API protection
"""

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, status
from fastapi.responses import JSONResponse
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
import asyncio

from app.utils.exceptions import MajiscopeException


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        # Store request counts: {ip: [(timestamp, count), ...]}
        self.request_history: Dict[str, list] = defaultdict(list)
        
        # Cleanup old entries every 10 seconds
        asyncio.create_task(self._cleanup_old_entries())
    
    async def dispatch(self, request: Request, call_next):
        """Check rate limit for request"""
        if request.method.upper() == "OPTIONS":
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Skip rate limiting for health checks
        if request.url.path in {"/health", "/api/health", "/api/health/ready", "/api/health/database"}:
            return await call_next(request)
        
        # Check rate limit
        now = datetime.utcnow()
        
        if client_ip not in self.request_history:
            self.request_history[client_ip] = []
        
        # Remove old entries (older than 1 minute)
        cutoff_time = now - timedelta(minutes=1)
        self.request_history[client_ip] = [
            entry for entry in self.request_history[client_ip]
            if entry > cutoff_time
        ]
        
        # Check if limit exceeded
        if len(self.request_history[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded. Max {self.requests_per_minute} requests per minute",
                    "timestamp": now.isoformat(),
                },
            )
        
        # Record this request
        self.request_history[client_ip].append(now)
        
        # Add rate limit headers to response
        response = await call_next(request)
        remaining = self.requests_per_minute - len(self.request_history[client_ip])
        
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(
            int((now + timedelta(minutes=1)).timestamp())
        )
        
        return response
    
    async def _cleanup_old_entries(self):
        """Periodically cleanup old entries"""
        while True:
            await asyncio.sleep(300)  # Cleanup every 5 minutes
            
            now = datetime.utcnow()
            cutoff_time = now - timedelta(minutes=5)
            
            for ip in list(self.request_history.keys()):
                self.request_history[ip] = [
                    entry for entry in self.request_history[ip]
                    if entry > cutoff_time
                ]
                
                # Remove IP if no more entries
                if not self.request_history[ip]:
                    del self.request_history[ip]
