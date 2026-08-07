"""Unit test suite for ExtractionEngine resilience and error recovery."""

from unittest.mock import MagicMock, patch

from doc_intelligence.extractor.engine import ExtractionEngine
from doc_intelligence.schemas.extraction import InvoiceExtractionData


def test_engine_extraction_with_mock_client() -> None:
    """Tests ExtractionEngine extraction logic using a mocked OpenAI client."""
    mock_parsed_data = InvoiceExtractionData(
        vendor={"name": "Test Vendor", "tax_id": None, "address": None},
        invoice_number="INV-999",
        invoice_date="2026-08-01",
        subtotal=50.0,
        tax_amount=4.0,
        grand_total=54.0,  # 🟢 Fixed: grand_total matches schema attribute
        line_items=[],
    )

    with patch(
        "doc_intelligence.extractor.engine.get_openai_client"
    ) as mock_get_client:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()

        # Simulate OpenAI Structured Parsing response payload
        mock_choice.message.refusal = None
        mock_choice.message.parsed = mock_parsed_data
        mock_response.choices = [mock_choice]
        mock_client.beta.chat.completions.parse.return_value = mock_response
        mock_get_client.return_value = (mock_client, "gpt-4o")

        engine = ExtractionEngine()
        result = engine.extract(
            cleaned_text="INVOICE #INV-999 Total $54.00",
            schema=InvoiceExtractionData,
        )

        assert result.invoice_number == "INV-999"
        assert result.grand_total == 54.0
        assert mock_client.beta.chat.completions.parse.called
