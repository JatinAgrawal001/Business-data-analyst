import time
import threading
from typing import Dict, List, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class InMemoryRateLimiter:
    """
    Thread-safe in-memory sliding window rate limiter.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._requests: Dict[str, List[float]] = {}

    def is_allowed(self, client_key: str, max_requests: int, window_seconds: int = 60) -> Tuple[bool, int, int]:
        """
        Determines whether request is within threshold.
        Returns: (is_allowed, remaining_requests, retry_after_seconds)
        """
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            if client_key not in self._requests:
                self._requests[client_key] = []

            # Purge timestamps older than the sliding window
            self._requests[client_key] = [
                ts for ts in self._requests[client_key] if ts > window_start
            ]

            current_count = len(self._requests[client_key])
            if current_count >= max_requests:
                earliest_ts = self._requests[client_key][0]
                retry_after = max(1, int(earliest_ts + window_seconds - now))
                return False, 0, retry_after

            # Record this request
            self._requests[client_key].append(now)
            remaining = max(0, max_requests - len(self._requests[client_key]))
            return True, remaining, 0

    def cleanup(self):
        """Purge idle keys periodically."""
        now = time.time()
        with self._lock:
            empty_keys = [
                k for k, timestamps in self._requests.items()
                if not timestamps or timestamps[-1] < (now - 300)
            ]
            for k in empty_keys:
                del self._requests[k]

limiter = InMemoryRateLimiter()

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI HTTP Middleware enforcing endpoint-specific rate limits.
    """
    async def dispatch(self, request: Request, call_next):
        # 1. Skip rate limits for CORS preflight, health checks and OpenAPI docs
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        if path in ["/api/v1/health", "/", "/docs", "/redoc", "/api/v1/openapi.json"]:
            return await call_next(request)

        # 2. Derive client key (authenticated user ID from header or client IP)
        auth_header = request.headers.get("authorization", "")
        client_ip = request.client.host if request.client else "127.0.0.1"
        client_key = auth_header[:30] if auth_header else client_ip

        # 3. Determine threshold based on endpoint sensitivity
        if "/upload" in path:
            max_limit = 30  # 30 uploads/min
            window = 60
        elif "/ask" in path or "/generate" in path:
            max_limit = 45  # 45 AI queries/min
            window = 60
        else:
            max_limit = 180  # 180 standard API calls/min
            window = 60

        scoped_key = f"{client_key}:{path[:20]}"
        allowed, remaining, retry_after = limiter.is_allowed(scoped_key, max_limit, window)

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Maximum {max_limit} requests allowed per {window} seconds. Please retry after {retry_after}s.",
                        "details": {"retry_after_seconds": retry_after}
                    }
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_limit),
                    "X-RateLimit-Remaining": "0"
                }
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
