"""Automated extraction evaluation benchmark suite using field precision scoring."""

import json
import logging
from pathlib import Path

from dotenv import load_dotenv

from doc_intelligence.extractor.engine import (
    ExtractionEngine,
    SelfHealingExtractionError,
)
from doc_intelligence.schemas.extraction import InvoiceExtractionData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_total_val(extracted: InvoiceExtractionData) -> float:
    """Helper to safely extract the total amount across possible schema attribute variants."""
    for attr in ["grand_total", "total", "total_amount", "amount_due", "total_due"]:
        if hasattr(extracted, attr):
            return getattr(extracted, attr)
    raise AttributeError(
        f"Could not find a valid total metric attribute on InvoiceExtractionData. "
        f"Available fields: {list(extracted.model_fields.keys())}"
    )


def run_evaluation_benchmark() -> None:
    """Executes benchmark suite over ground-truth synthetic dataset and prints metric summary."""
    # 1. Load environment variables first
    load_dotenv()

    # 2. Locate and load ground-truth dataset
    dataset_path = Path(__file__).parent / "dataset.json"
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found at {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)  # 👈 'dataset' defined HERE

    # 3. Instantiate extraction engine after loading env and dataset
    engine = ExtractionEngine()

    total_docs = len(dataset)
    schema_compliant_count = 0
    total_field_checks = 0
    matched_field_checks = 0

    print("\n" + "=" * 65)
    print("🚀 STARTING AUTOMATED EXTRACTION BENCHMARK EVALUATION")
    print(f"Dataset size: {total_docs} ground-truth documents")
    print("=" * 65 + "\n")

    for item in dataset:
        doc_id = item["id"]
        raw_text = item["raw_text"]
        truth = item["ground_truth"]

        logger.info("Evaluating [%s]...", doc_id)

        try:
            extracted: InvoiceExtractionData = engine.extract(
                cleaned_text=raw_text,
                schema=InvoiceExtractionData,
            )
            schema_compliant_count += 1
        except SelfHealingExtractionError as exc:
            logger.error("[%s] FAILED SCHEMA VALIDATION: %s", doc_id, exc)
            continue

        # Extract total value dynamically to prevent attribute drift
        actual_total = _get_total_val(extracted)

        # Evaluate Exact Field Matches
        fields_to_verify = [
            ("invoice_number", extracted.invoice_number, truth["invoice_number"]),
            ("invoice_date", extracted.invoice_date, truth["invoice_date"]),
            ("subtotal", extracted.subtotal, truth["subtotal"]),
            ("tax_amount", extracted.tax_amount, truth["tax_amount"]),
            ("total", actual_total, truth["total_amount"]),
            ("vendor_name", extracted.vendor.name, truth["vendor_name"]),
            ("line_items_count", len(extracted.line_items), truth["line_items_count"]),
        ]

        for field_name, actual_val, expected_val in fields_to_verify:
            total_field_checks += 1
            if actual_val == expected_val:
                matched_field_checks += 1
            else:
                logger.warning(
                    "[%s] Field mismatch on '%s': Expected %s, got %s",
                    doc_id, field_name, expected_val, actual_val,
                )

    # Calculate Metrics
    schema_compliance_rate = (schema_compliant_count / total_docs) * 100.0
    exact_match_rate = (
        (matched_field_checks / total_field_checks) * 100.0
        if total_field_checks > 0
        else 0.0
    )

    print("\n" + "=" * 65)
    print("📊 BENCHMARK EVALUATION SUMMARY")
    print("=" * 65)
    print(f"Total Test Documents:        {total_docs}")
    print(
        f"Schema Compliance Rate:       {schema_compliance_rate:.2f}%"
        f" ({schema_compliant_count}/{total_docs})"
    )
    print(
        f"Exact Field Match Rate:      {exact_match_rate:.2f}%"
        f" ({matched_field_checks}/{total_field_checks} fields)"
    )
    print("=" * 65 + "\n")

    assert (
        schema_compliance_rate >= 90.0
    ), f"Schema compliance below threshold: {schema_compliance_rate}%"
    assert (
        exact_match_rate >= 90.0
    ), f"Exact match rate below threshold: {exact_match_rate}%"


if __name__ == "__main__":
    run_evaluation_benchmark()