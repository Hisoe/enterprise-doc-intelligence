"""Pydantic v2 domain schemas for structured document extraction and validation."""

from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator


class VendorInfo(BaseModel):
    """Details regarding the selling vendor or service provider."""

    name: str = Field(description="Full legal or commercial name of the vendor.")
    tax_id: str | None = Field(
        default=None,
        description="Tax Identification Number, VAT Number, or EIN if present.",
    )
    address: str | None = Field(
        default=None,
        description="Physical or mailing address of the vendor.",
    )


class LineItem(BaseModel):
    """An individual product or service itemized on a document."""

    description: str = Field(description="Detailed item description or service rendered.")
    quantity: Annotated[float, Field(gt=0, description="Quantity purchased.")] = 1.0
    unit_price: Annotated[
        float, Field(ge=0, description="Cost per individual unit in document currency.")
    ] = 0.0
    total_price: Annotated[float, Field(ge=0, description="Extracted line item total price.")] = 0.0

    @model_validator(mode="after")
    def verify_line_item_math(self) -> "LineItem":
        """Validate or adjust line item total pricing math."""
        expected = round(self.quantity * self.unit_price, 2)
        if self.unit_price > 0 and abs(self.total_price - expected) > 0.05:
            # Re-align total price if OCR / extraction has minor rounding error
            self.total_price = expected
        return self


class InvoiceExtractionData(BaseModel):
    """Strict schema for financial document extraction with structural math validation."""

    vendor: VendorInfo = Field(description="Information about the issuing vendor.")
    invoice_number: str = Field(
        description="Unique invoice, receipt, or reference tracking identifier."
    )
    invoice_date: str | None = Field(
        default=None,
        description="Issue date in YYYY-MM-DD format if parseable.",
    )
    currency: str = Field(
        default="USD",
        description="3-letter ISO currency code (e.g. USD, EUR, GBP, CAD).",
    )
    line_items: list[LineItem] = Field(
        default_factory=list,
        description="Itemized list of products or services.",
    )
    subtotal: Annotated[
        float, Field(ge=0, description="Sum of line items prior to tax application.")
    ] = 0.0
    tax_amount: Annotated[float, Field(ge=0, description="Total tax or VAT amount charged.")] = 0.0
    grand_total: Annotated[
        float, Field(ge=0, description="Final total amount including subtotal and taxes.")
    ] = 0.0

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, v: str) -> str:
        """Ensure currency code is uppercase 3-letter ISO code."""
        return v.strip().upper()

    @model_validator(mode="after")
    def validate_financial_integrity(self) -> "InvoiceExtractionData":
        """Enforce domain math constraint: subtotal + tax_amount == grand_total."""
        expected_total = round(self.subtotal + self.tax_amount, 2)
        if expected_total > 0 and abs(self.grand_total - expected_total) > 0.10:
            raise ValueError(
                f"Financial mismatch error: subtotal ({self.subtotal}) + tax ({self.tax_amount}) "
                f"= {expected_total}, but extracted grand_total is {self.grand_total}."
            )
        return self
