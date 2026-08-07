# 🏢 Enterprise Document Intelligence Microservice

[![CI Pipeline](https://github.com/<YOUR_USERNAME>/enterprise-doc-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/<YOUR_USERNAME>/enterprise-doc-intelligence/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.0%2B-red.svg)](https://docs.pydantic.dev/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](Dockerfile)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An asynchronous, enterprise-grade AI extraction service engineered to convert unstructured financial documents (Invoices, Receipts, Purchase Orders) into strongly typed, mathematically validated JSON schemas.

Built with **Pydantic v2 self-healing error recovery**, **non-blocking threadpool ingestion**, **tiktoken context budget enforcement**, and **network-level observability with Langfuse**.

---

## 🏗️ System Architecture & Workflow

```text
 Client (cURL / ERP / Web App)
              │
              ▼ [POST /api/v1/extract/invoice]
 ┌────────────────────────────────────────────────────────┐
 │ FastAPI Middleware Layer (api/middleware.py)           │
 │  • Inject Correlation ID (X-Request-ID: UUID4)        │
 │  • Track Latency (X-Process-Time-MS)                  │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │ Ingestion & Security Guardrails (api/routes.py)        │
 │  • Enforce 10MB Payload Limit                          │
 │  • Offload pypdf Parsing to Worker Threadpool          │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │ Text Normalization & Token Budgeting                  │
 │  • Unicode NFC Normalization & Control Char Stripping  │
 │  • Tiktoken Context Budget Validator (< 8,000 Tokens) │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │ Self-Healing Extraction Engine [Langfuse Traced]      │
 │  • Dual-Routing Client Factory (Azure Foundry / OpenAI)│
 │  • Pydantic v2 Cross-Field Mathematical Validation     │
 │  • Tenacity Exponential Backoff Retry Loop             │
 │  • Re-injects Validation Trace on Schema Exceptions    │
 └───────────────────────────┬────────────────────────────┘
                             │
                             ▼
 ┌────────────────────────────────────────────────────────┐
 │ API Envelope Response (HTTP 200 / Mapped 4xx/5xx)      │
 └────────────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack & Dependencies

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **API Backend** | FastAPI + Uvicorn | Asynchronous REST endpoints, interactive OpenAPI docs (`/docs`) |
| **LLM Provider** | Azure OpenAI / Direct OpenAI | GPT-4o-mini structured data extraction |
| **Data Validation** | Pydantic v2 + Pydantic Settings | Input/output validation and environment management |
| **PDF Extraction** | `pdfplumber` & `pypdf` | Multi-strategy text extraction with table layout preservation |
| **Tokenization** | `tiktoken` | Context window budgeting and token cost estimation |
| **Observability** | Langfuse | Full-stack trace trees, token counts, and latency tracking |
| **Tooling & CI** | `uv` + `ruff` + `hatchling` | Package management, strict linting, and build backends |

---

## 📊 Quantitative Quality Benchmarks

The microservice is evaluated against a ground-truth dataset (`tests/eval/dataset.json`) across 7 primary entity fields (`invoice_number`, `invoice_date`, `subtotal`, `tax_amount`, `total`, `vendor_name`, `line_items_count`).

| Benchmark Metric | Target Threshold | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **Schema Compliance Rate** | $\ge 90.0\%$ | 100.00% (10/10) | 🟢 PASS |
| **Exact Field Match Rate** | $\ge 90.0\%$ | 100.00% (70/70) | 🟢 PASS |
| **Self-Healing Error Recovery** | $\le 3	ext{ attempts}$ | 100.00% | 🟢 PASS |
| **Mean End-to-End Latency** | $< 2500	ext{ ms}$ | ~1140 ms | 🟢 PASS |

---

## ⚡ Quickstart (1-Command Docker Setup)

### Prerequisites
- Docker & Docker Compose installed

### 1. Launch Service

```bash
# Clone repository
git clone https://github.com/<YOUR_USERNAME>/enterprise-doc-intelligence.git
cd enterprise-doc-intelligence

# Start API container
docker compose up -d --build
```

Access interactive Swagger documentation at: `http://localhost:8000/docs`

---

## 🧪 Local Development & Testing

```bash
# Install dependencies via uv
uv sync

# Run linter
uv run ruff check .

# Run unit tests
uv run pytest -v

# Run evaluation benchmark
uv run python tests/eval/run_evals.py
```

---

## 📝 API Usage Example

```bash
curl -X POST "http://localhost:8000/api/v1/extract/invoice"   -H "accept: application/json"   -F "file=@sample_invoice.pdf;type=application/pdf"
```

### Example Response Payload

```json
{
  "success": true,
  "request_id": "c1f7a0b2-3e4d-4f1a-8c90-9f123456789a",
  "process_time_ms": 1140.22,
  "data": {
    "vendor": {
      "name": "Acme Industrial Tools Inc.",
      "tax_id": "US-987654321",
      "address": "100 Innovation Way, Austin, TX 78701"
    },
    "invoice_number": "INV-2026-08912",
    "invoice_date": "2026-08-01",
    "due_date": "2026-08-31",
    "currency": "USD",
    "subtotal": 1200.00,
    "tax_amount": 96.00,
    "total": 1296.00,
    "line_items": [
      {
        "description": "Server Rack Cabinet 42U",
        "quantity": 2.0,
        "unit_price": 600.00,
        "line_total": 1200.00
      }
    ]
  }
}
```