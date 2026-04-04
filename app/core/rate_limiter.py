"""
Rate limiting using SlowAPI.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse


def get_api_key_or_ip(request: Request) -> str:
    """
    Get identifier for rate limiting: API key prefix if present, else IP address.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        # Use the API key prefix (first 8 chars) for rate limiting
        api_key = auth_header[7:]
        if api_key:
            return f"key:{api_key[:8]}"
    # Fall back to IP
    return get_remote_address(request)


# Default limiter instance
limiter = Limiter(key_func=get_api_key_or_ip)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": str(exc.detail),
            "retry_after": getattr(exc, "retry_after", 60),
        },
    )


# Default rate limits
DEFAULT_RATE_LIMIT = "100/minute"
PREMIUM_RATE_LIMIT = "1000/minute"
FREE_RATE_LIMIT = "30/minute"
