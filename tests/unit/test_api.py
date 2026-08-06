"""Unit and integration tests for FastAPI REST endpoints and custom exception handlers."""

from fastapi.testclient import TestClient

from doc_intelligence.main import app

client = TestClient(app)


def test_health_check_endpoint():
    """Verifies that the system health check returns HTTP 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "enterprise-doc-intelligence",
    }


def test_extract_invoice_missing_inputs():
    """Verifies HTTP 400 when neither file nor raw_text is provided."""
    response = client.post("/api/v1/extract/invoice")
    assert response.status_code == 400
    assert "Either 'file' or 'raw_text' must be provided" in response.json()["detail"]


def test_extract_invoice_with_raw_text(monkeypatch):
    """Verifies successful extraction response envelope using raw_text form data."""
    sample_text = (
        "INVOICE #INV-1001 Date: 2026-08-01 "
        "Vendor: Test Vendor LLC Subtotal: $100.00 Tax: $8.00 Total: $108.00 "
        "Item: Widget Qty: 1 Unit Price: $100.00 Total: $100.00"
    )

    response = client.post(
        "/api/v1/extract/invoice",
        data={"raw_text": sample_text},
    )

    assert response.status_code == 200
    json_data = response.json()

    assert json_data["success"] is True
    assert "request_id" in json_data
    assert "process_time_ms" in json_data
    assert json_data["data"]["invoice_number"] == "INV-1001"
    assert json_data["data"]["grand_total"] == 108.0

    # Verify response headers set by middleware
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time-MS" in response.headers
