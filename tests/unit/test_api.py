"""Unit test suite for document extraction API routes."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

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
        grand_total=108.0,  # 🟢 Fixed: grand_total matches schema attribute
        line_items=[],
    )


def test_extract_invoice_with_raw_text(
    mock_invoice_data: InvoiceExtractionData,
) -> None:
    """Tests POST /api/v1/extract/invoice with raw text input using a mocked engine."""
    with patch(
        "doc_intelligence.api.routes.get_extraction_engine"
    ) as mock_get_engine:
        mock_engine = MagicMock()
        mock_engine.extract.return_value = mock_invoice_data
        mock_get_engine.return_value = mock_engine

        response = client.post(
            "/api/v1/extract/invoice",
            data={"raw_text": "INVOICE #INV-2026-001 Total: $108.00"},
        )

        assert response.status_code == 200
        json_resp = response.json()
        assert json_resp["success"] is True
        assert json_resp["data"]["invoice_number"] == "INV-2026-001"
        assert json_resp["data"]["grand_total"] == 108.0
