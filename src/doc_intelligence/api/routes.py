"""API router for document intelligence extraction endpoints."""

import io
import logging
from typing import Annotated

import pypdf
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from starlette.concurrency import run_in_threadpool

from doc_intelligence.api.middleware import get_request_id
from doc_intelligence.extractor.engine import ExtractionEngine
from doc_intelligence.preprocessor.cleaner import TextCleaner
from doc_intelligence.schemas.api import APIResponseEnvelope, ErrorDetail
from doc_intelligence.schemas.extraction import InvoiceExtractionData

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Document Extraction"])

# Singleton instances for route layer
extraction_engine = ExtractionEngine()
text_cleaner = TextCleaner()

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB payload limit
MAX_TOKEN_BUDGET = 8000  # Token limit per request payload


def _extract_text_from_pdf_bytes_sync(pdf_bytes: bytes) -> str:
    """Synchronous CPU-bound helper for parsing PDF streams using pypdf."""
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        extracted_pages = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                extracted_pages.append(page_text)
        return "\n\n".join(extracted_pages)
    except Exception as exc:
        logger.error("Failed to parse PDF binary stream: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not extract text from the provided PDF file: {exc}",
        ) from exc


@router.post(
    "/extract/invoice",
    response_model=APIResponseEnvelope[InvoiceExtractionData],
    status_code=status.HTTP_200_OK,
    summary="Extract Structured Data from Invoice Document",
    description=(
        "Processes an invoice document provided either as a raw file upload (.pdf, .txt) "
        "or as a raw text string. Returns structured JSON matching InvoiceExtractionData."
    ),
    responses={
        400: {
            "model": ErrorDetail,
            "description": "Bad Request - Invalid payload or file size exceeded",
        },
        422: {
            "model": ErrorDetail,
            "description": "Unprocessable Entity - Schema validation failed",
        },
        429: {
            "model": ErrorDetail,
            "description": "Too Many Requests - Provider rate limit exceeded",
        },
        504: {"model": ErrorDetail, "description": "Gateway Timeout - Upstream AI model timed out"},
    },
)
async def extract_invoice(
    request: Request,
    file: Annotated[
        UploadFile | None,
        File(description="Invoice file upload (.pdf or .txt format)."),
    ] = None,
    raw_text: Annotated[
        str | None,
        Form(description="Raw document text string if no file is uploaded."),
    ] = None,
    max_attempts: Annotated[
        int,
        Form(description="Maximum self-healing attempts if schema validation fails."),
    ] = 3,
) -> APIResponseEnvelope[InvoiceExtractionData]:
    """Extracts structured invoice metrics from file upload or raw text."""
    request_id = get_request_id(request)

    # 1. Input Validation
    if not file and not raw_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'file' or 'raw_text' must be provided in the request body.",
        )

    document_content = ""

    # 2. File Ingestion & Size Guardrail
    if file:
        logger.info("[%s] Processing uploaded file: %s", request_id, file.filename)

        # Fail fast if file size header is declared over limit
        if file.size and file.size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB.",
            )

        file_bytes = await file.read()

        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB.",
            )

        filename_lower = (file.filename or "").lower()
        if filename_lower.endswith(".pdf"):
            # Offload CPU-bound PDF parsing to worker threadpool
            document_content = await run_in_threadpool(
                _extract_text_from_pdf_bytes_sync, file_bytes
            )
        else:
            document_content = file_bytes.decode("utf-8", errors="replace")
    else:
        logger.info("[%s] Processing raw text input parameter", request_id)
        document_content = raw_text or ""

    # 3. Preprocessing & Normalization
    cleaned_text = TextCleaner.clean(document_content)

    if not cleaned_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Extracted document content was empty after text preprocessing. "
                "If uploading a scanned PDF, ensure an OCR text layer is present."
            ),
        )

    # Token Budget Guardrail
    token_count = text_cleaner.count_tokens(cleaned_text)
    logger.info("[%s] Ingested document token count: %d tokens", request_id, token_count)
    if token_count > MAX_TOKEN_BUDGET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Document token count ({token_count}) exceeds maximum allowed budget "
                f"of {MAX_TOKEN_BUDGET} tokens."
            ),
        )

    # 4. Phase 3 Extraction Engine Execution
    extracted_data = extraction_engine.extract(
        cleaned_text=cleaned_text,
        schema=InvoiceExtractionData,
        max_attempts=max_attempts,
    )

    process_time_ms = getattr(request.state, "process_time_ms", 0.0)

    # 5. Envelope Response Return
    return APIResponseEnvelope[InvoiceExtractionData](
        success=True,
        request_id=request_id,
        process_time_ms=process_time_ms,
        data=extracted_data,
    )
