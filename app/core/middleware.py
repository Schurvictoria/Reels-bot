"""Custom middleware for the application."""

import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {response.status_code} "
            f"processed in {process_time:.4f}s"
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limits before processing request."""
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean old entries
        self.requests = {
            ip: times for ip, times in self.requests.items()
            if any(t > current_time - 60 for t in times)
        }
        
        # Check current client
        if client_ip in self.requests:
            # Filter recent requests (last minute)
            recent_requests = [
                t for t in self.requests[client_ip]
                if t > current_time - 60
            ]
            
            if len(recent_requests) >= self.requests_per_minute:
                return Response(
                    content='{"error": "Rate limit exceeded"}',
                    status_code=429,
                    media_type="application/json"
                )
            
            self.requests[client_ip] = recent_requests + [current_time]
        else:
            self.requests[client_ip] = [current_time]
        
        return await call_next(request)


def add_middlewares(app: FastAPI) -> None:
    """Add all middlewares to the FastAPI app."""
    # Add logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Add rate limiting middleware
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)