# 📄 Enterprise Document Intelligence & Extraction Pipeline

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.7+-e92063.svg)](https://docs.pydantic.dev/)
[![Azure OpenAI](https://img.shields.io/badge/Azure_OpenAI-GPT--4o--mini-0078D4.svg?logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/en-us/products/ai-services/openai-service)
[![Langfuse](https://img.shields.io/badge/Observability-Langfuse-black.svg)](https://langfuse.com)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

An end-to-end, enterprise-ready microservice that transforms unstructured, noisy business documents (PDFs, invoices, contracts) into strictly typed, validated JSON objects using Azure OpenAI and Pydantic v2. 

Unlike basic LLM wrapper scripts, this system is engineered with **production hygiene at its core**: dual-provider resilience, automated text cleaning, multi-engine PDF fallback parsing, self-healing JSON retry loops, and full LLM execution tracing.

---

## 🏗️ Architectural Differentiators

* **🛡️ Dual-Provider Resilient Client:** Built-in factory pattern prioritizing **Azure OpenAI Service** (enterprise SLA & data privacy) with zero-downtime fallback to direct **OpenAI API** if Azure credentials are unconfigured or offline.
* **🔒 Strict Schema Enforcement (Pydantic v2):** Uses `pydantic-settings` for fail-at-startup environment loading and Pydantic models for strict structured output extraction (preventing malformed JSON payloads).
* **🧼 Preprocessing & Text Normalization:** Multi-engine PDF extractor (`pdfplumber` with `pypdf` fallback) coupled with regex sanitization to strip zero-width characters, page header noise, and token bloat before calling the LLM.
* **📊 Telemetry & Observability:** Integrated **Langfuse** tracing at the client boundary to capture token costs, latency distributions, and input/output prompts across execution spans.
* **⚡ Modern Python Tooling Stack:** Dependency locking managed via `uv`, PEP 604 type hints, strict linting/formatting via `Ruff`, and containerized deployment with `Dockerfile`.

---

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