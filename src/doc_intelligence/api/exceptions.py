"""Custom exception handlers for mapping AI/Engine exceptions to HTTP responses."""

import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse
from openai import APIConnectionError, APITimeoutError, RateLimitError

from doc_intelligence.api.middleware import get_request_id
from doc_intelligence.extractor.engine import SelfHealingExtractionError
from doc_intelligence.schemas.api import ErrorDetail

logger = logging.getLogger(__name__)


async def self_healing_error_handler(
    request: Request, exc: SelfHealingExtractionError
) -> JSONResponse:
    """Handles schema validation failures that could not be self-healed after max retries."""
    request_id = get_request_id(request)
    logger.error("[%s] Self-Healing extraction failed: %s", request_id, exc)

    payload = ErrorDetail(
        request_id=request_id,
        error_code="SCHEMA_VALIDATION_FAILED",
        message="The document text could not be converted into a valid schema payload after retries.",
        details=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=payload.model_dump(),
    )


async def rate_limit_handler(request: Request, exc: RateLimitError) -> JSONResponse:
    """Handles LLM rate-limiting (HTTP 429) from Azure / OpenAI."""
    request_id = get_request_id(request)
    logger.warning("[%s] Provider rate limit exceeded: %s", request_id, exc)

    payload = ErrorDetail(
        request_id=request_id,
        error_code="LLM_RATE_LIMIT_EXCEEDED",
        message="The underlying AI model quota or Tokens-Per-Minute (TPM) limit was exceeded.",
        details="Please retry your request after a short wait.",
    )
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=payload.model_dump(),
        headers={"Retry-After": "10"},
    )


async def timeout_handler(
    request: Request, exc: APITimeoutError | APIConnectionError | TimeoutError
) -> JSONResponse:
    """Handles API timeouts or upstream provider connectivity dropouts."""
    request_id = get_request_id(request)
    logger.error("[%s] Upstream API timeout or connection failure: %s", request_id, exc)

    payload = ErrorDetail(
        request_id=request_id,
        error_code="UPSTREAM_TIMEOUT",
        message="The request to the AI model provider timed out or failed to connect.",
        details=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content=payload.model_dump(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global catch-all for unhandled internal server exceptions."""
    request_id = get_request_id(request)
    logger.exception("[%s] Unhandled internal server error occurred: %s", request_id, exc)

    payload = ErrorDetail(
        request_id=request_id,
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected internal server error occurred.",
        details=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=payload.model_dump(),
    )
