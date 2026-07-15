"""
Phase 15.0 T1.2 + T5: API error hierarchy + central handler envelope.

Provides a typed exception hierarchy for API errors, replacing scattered
`raise HTTPException(status_code=..., detail=...)` calls (227 in app.py)
with semantic `raise NotFoundError(...)` / `ValidationError(...)` etc.

`@app.exception_handler(APIError)` (registered in app.py) converts these
into a stable envelope:

    {"code": "...", "message": "...", "detail": "..."}

`detail` is kept as an alias of `message` so existing tests/SDKs that
read response.json()["detail"] keep working.

The actual conversion of 227 inline `raise HTTPException` calls happens in
Phase 15.0 T5; here in T1.2 we only define the classes.
"""
from __future__ import annotations

from typing import Optional


class APIError(Exception):
    """Base class for all dashboard API errors.

    Subclasses hard-code `status_code` and `code`. The central exception
    handler (see dashboard.app.create_app) converts to JSON envelope.

    Args:
        message: human-readable error description (also exposed as `detail`).
        code: optional override of the default error code.
        status_code: optional override of the default HTTP status.
    """

    status_code: int = 500
    code: str = "internal_error"

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(APIError):
    """Resource not found (HTTP 404)."""

    status_code = 404
    code = "not_found"


class ValidationError(APIError):
    """Request validation failed (HTTP 400)."""

    status_code = 400
    code = "validation_error"


class ConflictError(APIError):
    """Resource state conflict (HTTP 409)."""

    status_code = 409
    code = "conflict"


class UnauthorizedError(APIError):
    """Missing or invalid credentials (HTTP 401)."""

    status_code = 401
    code = "unauthorized"


class RateLimitError(APIError):
    """Rate limit exceeded (HTTP 429)."""

    status_code = 429
    code = "rate_limited"


__all__ = [
    "APIError",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "UnauthorizedError",
    "RateLimitError",
]
