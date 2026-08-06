"""API contracts for client requests, response envelopes, and error payloads."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponseEnvelope(BaseModel, Generic[T]):
    """Standardized API response envelope providing request context and metadata."""

    success: bool = Field(..., description="Indicates if the extraction completed successfully.")
    request_id: str = Field(..., description="Unique correlation UUID tracking this request.")
    process_time_ms: float = Field(
        ..., description="Total server-side processing latency in milliseconds."
    )
    data: T = Field(..., description="Extracted payload matching the requested schema.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "request_id": "a1b2c3d4-e5f6-7890-1234-56789abcdef0",
                "process_time_ms": 1420.55,
                "data": {
                    "vendor": {
                        "name": "Acme Industrial Tools Inc.",
                        "tax_id": "US-987654321",
                        "address": "100 Innovation Way, Austin, TX 78701",
                    },
                    "invoice_number": "INV-2026-08912",
                    "invoice_date": "2026-08-01",
                    "due_date": "2026-08-31",
                    "currency": "USD",
                    "subtotal": 1200.00,
                    "tax_amount": 96.00,
                    "total_amount": 1296.00,
                    "line_items": [
                        {
                            "description": "Server Rack Cabinet 42U",
                            "quantity": 2.0,
                            "unit_price": 600.00,
                            "line_total": 1200.00,
                        }
                    ],
                },
            }
        }
    }


class ErrorDetail(BaseModel):
    """Structured error response for API exceptions."""

    success: bool = Field(default=False, description="Always False for error responses.")
    request_id: str = Field(..., description="Unique correlation UUID for error tracing.")
    error_code: str = Field(..., description="Machine-readable error classification code.")
    message: str = Field(..., description="Human-readable error summary.")
    details: str | dict | None = Field(
        default=None, description="Optional diagnostic details or error context."
    )
