"""Resilient multi-engine PDF text extractor with layout preservation."""

from pathlib import Path
from typing import Any

import pdfplumber
from pypdf import PdfReader

from doc_intelligence.preprocessor.cleaner import TextCleaner


class PDFExtractionError(Exception):
    """Raised when all PDF extraction backends fail to parse a document."""

    pass


class PDFParser:
    """PDF Extractor utilizing pdfplumber as primary engine with pypdf fallback."""

    def __init__(self, cleaner: TextCleaner | None = None) -> None:
        self.cleaner = cleaner or TextCleaner()

    def extract_from_file(self, file_path: str | Path) -> dict[str, Any]:
        """Extracts, cleans, and counts tokens from a local PDF file path.

        Primary Strategy: pdfplumber (preserves visual positioning and tables).
        Fallback Strategy: pypdf (resilient to minor stream corruption).
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found at path: {path}")

        raw_pages: list[str] = []
        extraction_method = "pdfplumber"

        try:
            # Primary Engine: pdfplumber
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text(layout=True) or ""
                    raw_pages.append(page_text)

        except Exception:
            # Fallback Engine: pypdf
            extraction_method = "pypdf"
            raw_pages = []
            try:
                reader = PdfReader(str(path))
                for page in reader.pages:
                    raw_pages.append(page.extract_text() or "")
            except Exception as err:
                raise PDFExtractionError(
                    f"Failed to extract text from '{path.name}' using both pdfplumber and pypdf."
                ) from err

        raw_combined = "\n\n".join(raw_pages)
        cleaned_text = self.cleaner.clean(raw_combined)
        token_count = self.cleaner.count_tokens(cleaned_text)

        return {
            "file_name": path.name,
            "raw_character_count": len(raw_combined),
            "cleaned_character_count": len(cleaned_text),
            "token_count": token_count,
            "extraction_method": extraction_method,
            "cleaned_text": cleaned_text,
        }
