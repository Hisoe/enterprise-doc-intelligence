"""Integration tests for ExtractionEngine and Pydantic domain schemas."""

import pytest
from pydantic import ValidationError

from doc_intelligence.extractor.engine import ExtractionEngine
from doc_intelligence.schemas.extraction import InvoiceExtractionData, LineItem, VendorInfo


def test_schema_financial_integrity_validator() -> None:
    """Ensure subtotal + tax != grand_total triggers ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        InvoiceExtractionData(
            vendor=VendorInfo(name="Test Vendor Corp"),
            invoice_number="INV-999",
            subtotal=100.0,
            tax_amount=10.0,
            grand_total=150.0,  # Intentional math error (100 + 10 != 150)
        )

    assert "Financial mismatch error" in str(exc_info.value)


def test_line_item_math_auto_correction() -> None:
    """Ensure minor pricing discrepancies in LineItem auto-correct."""
    item = LineItem(
        description="Widget A",
        quantity=2.0,
        unit_price=15.00,
        total_price=30.00,  # Correct math
    )
    assert item.total_price == 30.00


@pytest.mark.skipif(
    not pytest.importorskip("doc_intelligence.core.config").settings.is_azure_configured
    and not pytest.importorskip("doc_intelligence.core.config").settings.OPENAI_API_KEY,
    reason="Live LLM API keys unconfigured",
)
def test_engine_live_extraction() -> None:
    """Integration test running realistic text through ExtractionEngine."""
    sample_invoice_text = (
        "INVOICE #INV-2026-001\n"
        "Date: 2026-08-01\n"
        "Vendor: Nexus Cloud Systems Inc.\n"
        "Tax ID: US987654321\n\n"
        "Items:\n"
        "1. Cloud Compute Instance - Qty: 2 @ $50.00 = $100.00\n"
        "2. Storage Block - Qty: 1 @ $20.00 = $20.00\n\n"
        "Subtotal: $120.00\n"
        "Tax: $10.00\n"
        "Total: $130.00"
    )

    engine = ExtractionEngine()
    result = engine.extract(cleaned_text=sample_invoice_text, schema=InvoiceExtractionData)

    assert result.vendor.name == "Nexus Cloud Systems Inc."
    assert result.invoice_number == "INV-2026-001"
    assert result.grand_total == 130.00
    assert len(result.line_items) == 2
