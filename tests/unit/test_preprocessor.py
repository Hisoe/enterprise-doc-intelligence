"""Unit tests for cleaner and pdf_parser modules."""

from doc_intelligence.preprocessor.cleaner import TextCleaner


def test_text_cleaner_sanitizes_control_chars_and_headers() -> None:
    cleaner = TextCleaner()
    dirty_input = (
        "CONFIDENTIAL INVOICE\x00\x0c\n"
        "Page 1 of 5\n\n"
        "Item 1      $150.00\n\n\n\n"
        "Total: $150.00\n"
        "Page 1 of 5"
    )

    cleaned = cleaner.clean(dirty_input)

    assert "\x00" not in cleaned
    assert "\x0c" not in cleaned
    assert "Page 1 of 5" not in cleaned
    assert "CONFIDENTIAL INVOICE" in cleaned
    assert "Total: $150.00" in cleaned


def test_token_counter_returns_positive_int() -> None:
    cleaner = TextCleaner()
    sample_text = "FastAPI, Azure OpenAI, and Pydantic v2 form a robust AI pipeline stack."
    tokens = cleaner.count_tokens(sample_text)

    assert isinstance(tokens, int)
    assert tokens > 0
