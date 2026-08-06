"""FastAPI Application Entry Point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import APIConnectionError, APITimeoutError, RateLimitError

from doc_intelligence.api.exceptions import (
    rate_limit_handler,
    self_healing_error_handler,
    timeout_handler,
    unhandled_exception_handler,
)
from doc_intelligence.api.middleware import ProcessTimeAndCorrelationMiddleware
from doc_intelligence.api.routes import router
from doc_intelligence.extractor.engine import SelfHealingExtractionError

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="Enterprise Document Intelligence Service",
    description=(
        "Production-grade AI extraction service featuring self-healing Pydantic v2 "
        "schema validation, Langfuse observability, and Azure AI Foundry integration."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 1. CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Custom Middleware
app.add_middleware(ProcessTimeAndCorrelationMiddleware)

# 3. Register Custom Exception Handlers
app.add_exception_handler(SelfHealingExtractionError, self_healing_error_handler)
app.add_exception_handler(RateLimitError, rate_limit_handler)
app.add_exception_handler(APITimeoutError, timeout_handler)
app.add_exception_handler(APIConnectionError, timeout_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# 4. Include Routers
app.include_router(router)


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint for container probes."""
    return {"status": "healthy", "service": "enterprise-doc-intelligence"}
