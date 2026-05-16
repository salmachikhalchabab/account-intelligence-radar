from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import time
import re
import os
import logging

logger = logging.getLogger(__name__)


class RateLimitStore:
    def __init__(self):
        self.requests: dict = defaultdict(list)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        now = time.time()
        window_start = now - window_seconds
        self.requests[key] = [t for t in self.requests[key] if t > window_start]
        if len(self.requests[key]) >= max_requests:
            return False
        self.requests[key].append(now)
        return True

    def get_retry_after(self, key: str, window_seconds: int) -> int:
        if not self.requests[key]:
            return 0
        oldest = min(self.requests[key])
        return max(int(oldest + window_seconds - time.time()) + 1, 1)


rate_store = RateLimitStore()

# FIX 1: Raised register limit from 3 to 10 — was too strict for real users
RATE_LIMITS = {
    "/api/auth/login":    {"max": 5,   "window": 60},
    "/api/auth/register": {"max": 10,  "window": 300},  # was 3 — too strict
    "/api/company":       {"max": 10,  "window": 60},
    "/api/geography":     {"max": 5,   "window": 60},
    "default":            {"max": 100, "window": 60},
}


def get_rate_limit_rule(path: str) -> dict:
    for pattern, rule in RATE_LIMITS.items():
        if pattern != "default" and path.startswith(pattern):
            return rule
    return RATE_LIMITS["default"]


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # FIX 2: Skip rate limiting in test environment
        if os.getenv("TESTING") == "1":
            return await call_next(request)

        ip = get_client_ip(request)
        path = request.url.path
        rule = get_rate_limit_rule(path)
        key = f"{ip}:{path}"

        if not rate_store.is_allowed(key, rule["max"], rule["window"]):
            retry_after = rate_store.get_retry_after(key, rule["window"])
            logger.warning(f"Rate limit exceeded: {ip} on {path}")
            return JSONResponse(
                status_code=429,
                content={"detail": f"Too many requests. Retry after {retry_after} seconds."},
                headers={"Retry-After": str(retry_after)}
            )
        return await call_next(request)


INJECTION_PATTERNS = [
    r"<script.*?>.*?</script>",
    r"javascript:",
    r"on\w+\s*=",
    r"(\bDROP\b|\bDELETE\b|\bINSERT\b|\bUPDATE\b|\bSELECT\b.*\bFROM\b)",
    r"\.\./",
    r"\x00",
]
COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in INJECTION_PATTERNS]


def sanitize_string(value: str) -> str:
    if not isinstance(value, str):
        return value
    value = value.strip()
    for pattern in COMPILED_PATTERNS:
        if pattern.search(value):
            raise HTTPException(status_code=400, detail="Invalid input detected.")
    if len(value) > 500:
        raise HTTPException(status_code=400, detail="Input too long (max 500 characters).")
    return value


def sanitize_dict(data: dict) -> dict:
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        else:
            sanitized[key] = value
    return sanitized


# FIX: Added OpenRouter pattern sk-or-
API_KEY_PATTERNS = [
    r"(sk-or-[a-zA-Z0-9\-]{20,})",    # OpenRouter
    r"(sk-[a-zA-Z0-9]{20,})",          # OpenAI style
    r"(gsk_[a-zA-Z0-9]{20,})",         # Groq
    r"(Bearer\s+[a-zA-Z0-9._-]{20,})", # JWT tokens
]
REDACT_PATTERNS = [re.compile(p) for p in API_KEY_PATTERNS]


def safe_log(message: str) -> str:
    for pattern in REDACT_PATTERNS:
        message = pattern.sub("[REDACTED]", message)
    return message


class SafeLogger(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = safe_log(str(record.msg))
        return True
