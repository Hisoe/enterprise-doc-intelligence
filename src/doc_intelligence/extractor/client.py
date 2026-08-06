"""Client factory providing Azure OpenAI / Azure Serverless / OpenAI access with Langfuse tracing."""

import logging

from langfuse.openai import AzureOpenAI, OpenAI

from doc_intelligence.core.config import settings

logger = logging.getLogger(__name__)


def get_openai_client() -> tuple[AzureOpenAI | OpenAI, str]:
    """Initializes and returns a Langfuse-traced OpenAI client along with the active deployment/model name."""
    if settings.is_azure_configured:
        endpoint = (settings.AZURE_OPENAI_ENDPOINT or "").strip()

        # 1. Azure Serverless / MaaS Endpoint (Contains /v1 path)
        if "/v1" in endpoint:
            # Guarantee trailing slash so httpx does not strip /v1/ during request joining
            if not endpoint.endswith("/"):
                endpoint += "/"

            logger.info(
                "Initializing Azure Serverless (MaaS) client with Langfuse tracing (endpoint: %s)...",
                endpoint,
            )
            client = OpenAI(
                base_url=endpoint,
                api_key=settings.AZURE_OPENAI_API_KEY,
            )
            return client, settings.AZURE_OPENAI_DEPLOYMENT_NAME

        # 2. Classic Azure OpenAI Service (Managed Compute)
        logger.info("Initializing Classic Azure OpenAI client with Langfuse tracing...")
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
        return client, settings.AZURE_OPENAI_DEPLOYMENT_NAME

    # 3. Direct OpenAI API Fallback
    if settings.OPENAI_API_KEY:
        logger.info("Azure credentials missing. Falling back to Direct OpenAI client...")
        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
        )
        return client, settings.OPENAI_MODEL

    raise ValueError(
        "No valid LLM configuration found! "
        "Please provide AZURE_OPENAI_ENDPOINT & AZURE_OPENAI_API_KEY, or OPENAI_API_KEY in .env"
    )
