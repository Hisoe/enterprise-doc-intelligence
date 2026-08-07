"""Unit test suite for document extraction API routes."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from doc_intelligence.api.routes import get_extraction_engine
from doc_intelligence.main import app
from doc_intelligence.schemas.extraction import InvoiceExtractionData

client = TestClient(app)


@pytest.fixture
def mock_invoice_data() -> InvoiceExtractionData:
    """Provides a deterministic mock InvoiceExtractionData instance."""
    return InvoiceExtractionData(
        vendor={
            "name": "Acme Corp",
            "tax_id": "US-123456789",
            "address": "123 Innovation Way",
        },
        invoice_number="INV-2026-001",
        invoice_date="2026-08-01",
        subtotal=100.0,
        tax_amount=8.0,
        grand_total=108.0,
        line_items=[],
    )


def test_extract_invoice_with_raw_text(
    mock_invoice_data: InvoiceExtractionData,
) -> None:
    """Tests POST /api/v1/extract/invoice with raw text input using FastAPI dependency overrides."""
    mock_engine = MagicMock()
    mock_engine.extract.return_value = mock_invoice_data

    # 🟢 Enterprise FastAPI Mocking: Override dependency on the application instance
    app.dependency_overrides[get_extraction_engine] = lambda: mock_engine

    try:
        response = client.post(
            "/api/v1/extract/invoice",
            data={"raw_text": "INVOICE #INV-2026-001 Total: $108.00"},
        )

        assert response.status_code == 200
        json_resp = response.json()
        assert json_resp["success"] is True
        assert json_resp["data"]["invoice_number"] == "INV-2026-001"
        assert json_resp["data"]["grand_total"] == 108.0
    finally:
        # Clean up dependency overrides to ensure test isolation
        app.dependency_overrides.clear()
