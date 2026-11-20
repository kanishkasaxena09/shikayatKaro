"""In-memory sliding-window rate limiter for Project Shikayat Karo.

Suitable for free-tier / single-instance cloud hosting (e.g. Render, Railway, Fly.io).
Note: Counters are held in memory and reset whenever the application process restarts.
For multi-instance horizontal scaling, a Redis-backed storage engine would be required.
"""

import os
import time
from collections import defaultdict
from typing import Dict, List, Optional
from fastapi import Request, HTTPException, status


class InMemoryRateLimiter:
    """Sliding-window in-memory rate limiter per client IP address."""

    def __init__(self, requests_limit: int, window_seconds: int, name: str = "endpoint"):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.name = name
        self.history: Dict[str, List[float]] = defaultdict(list)

    def check(self, request: Request, client_key: Optional[str] = None):
        """Enforces rate limit. Raises HTTP 429 if the request limit is exceeded."""
        # Allow disabling rate limiting during specific test suites via DISABLE_RATE_LIMIT=1
        if os.getenv("DISABLE_RATE_LIMIT") == "1":
            return

        now = time.time()
        # Derive client IP or provided key
        if client_key:
            key = client_key
        elif request and request.client and request.client.host:
            key = request.client.host
        else:
            key = "127.0.0.1"

        # Purge timestamps outside the active sliding window
        cutoff = now - self.window_seconds
        self.history[key] = [t for t in self.history[key] if t > cutoff]

        if len(self.history[key]) >= self.requests_limit:
            oldest_in_window = self.history[key][0]
            retry_after = max(1, int(self.window_seconds - (now - oldest_in_window)) + 1)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests for {self.name}. Rate limit exceeded ({self.requests_limit} per {self.window_seconds}s). Please try again later.",
                headers={"Retry-After": str(retry_after)}
            )

        self.history[key].append(now)

    def reset(self):
        """Resets in-memory history. Used between test runs."""
        self.history.clear()


# Default rate limiters configured from environment or safe defaults:
# 1. Login endpoint: 5 attempts per 60 seconds by default (prevents brute-force credential stuffing)
LOGIN_RATE_LIMIT = int(os.getenv("RATE_LIMIT_LOGIN_PER_MINUTE", "5"))
login_limiter = InMemoryRateLimiter(requests_limit=LOGIN_RATE_LIMIT, window_seconds=60, name="login")

# 2. Anonymous tracking endpoint: 10 requests per 60 seconds by default (prevents tracking code enumeration)
TRACK_RATE_LIMIT = int(os.getenv("RATE_LIMIT_TRACK_PER_MINUTE", "10"))
track_limiter = InMemoryRateLimiter(requests_limit=TRACK_RATE_LIMIT, window_seconds=60, name="anonymous tracking")
