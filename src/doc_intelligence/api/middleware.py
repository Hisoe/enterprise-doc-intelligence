"""HTTP Middleware for correlation tracking and latency measurement."""

import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


def get_request_id(request: Request) -> str:
    """Extracts the unique request ID stored in request.state."""
    return getattr(request.state, "request_id", "unknown-request-id")


class ProcessTimeAndCorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware that injects X-Request-ID and measures request latency in milliseconds."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Extract existing X-Request-ID header or generate a new UUID4
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()
        response = await call_next(request)
        process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Store process time in request state for downstream handlers
        request.state.process_time_ms = process_time_ms

        # Attach response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-MS"] = str(process_time_ms)

        return response
