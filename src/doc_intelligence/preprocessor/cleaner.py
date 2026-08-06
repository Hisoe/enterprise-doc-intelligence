"""Text sanitization, normalization, and token-counting utilities."""

import re
import unicodedata

import tiktoken


class TextCleaner:
    """Production-grade text sanitizer and token budget estimator."""

    def __init__(self, model_name: str = "gpt-4o") -> None:
        """Initialize tiktoken encoder for the target model family."""
        try:
            self.tokenizer = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # Fallback to cl100k_base (standard for GPT-3.5/GPT-4) if model name is unrecognized
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

    @staticmethod
    def sanitize_utf8(text: str) -> str:
        """Normalize Unicode characters to NFC standard and strip ASCII control characters."""
        if not text:
            return ""

        # Standardize Unicode representations (e.g., combining characters)
        text = unicodedata.normalize("NFC", text)

        # Strip non-printable ASCII control characters except tabs (\t) and newlines (\n)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

        return text

    @staticmethod
    def strip_headers_and_footers(text: str) -> str:
        """Remove repeating page numbers, timestamps, and boilerplate headers."""
        # Strip common pagination patterns: "Page 1 of 10", "PAGE 1/5", "Page - 1 -"
        page_pattern = r"(?i)\bpage\s*[-:\s]?\s*\d+\s*(?:of|/|-)?\s*\d*\b"
        text = re.sub(page_pattern, "", text)

        # Strip standalone isolated trailing digits on newlines (often artifact page numbers)
        text = re.sub(r"\n\s*\d+\s*\n", "\n", text)

        return text

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Collapse redundant spaces and excessive newlines while preserving paragraph structure."""
        # Convert runs of spaces or tabs into a single space
        text = re.sub(r"[ \t]+", " ", text)

        # Collapse 3 or more consecutive newlines into 2 (preserving standard paragraph gaps)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    @classmethod
    def clean(cls, raw_text: str) -> str:
        """Execute full cleaning pipeline as a class utility method."""
        text = cls.sanitize_utf8(raw_text)
        text = cls.strip_headers_and_footers(text)
        text = cls.normalize_whitespace(text)
        return text

    def count_tokens(self, text: str) -> int:
        """Calculate exact token count using tiktoken BPE encoding."""
        if not text:
            return 0
        return len(self.tokenizer.encode(text))
