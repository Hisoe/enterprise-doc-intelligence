"""Client factory providing Azure OpenAI / OpenAI access with Langfuse tracing."""

import logging

from langfuse.openai import AzureOpenAI, OpenAI

from doc_intelligence.core.config import settings

logger = logging.getLogger(__name__)


def get_openai_client() -> tuple[AzureOpenAI | OpenAI, str]:
    """Initializes and returns a Langfuse-traced OpenAI client along with the active deployment.

    Priority:
    1. Azure OpenAI Service (Enterprise Primary)
    2. Direct OpenAI API (Developer Fallback)

    Raises:
        ValueError: If neither Azure OpenAI nor direct OpenAI credentials are configured.
    """
    if settings.is_azure_configured:
        logger.info("Initializing Azure OpenAI client with Langfuse tracing...")
        client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
        return client, settings.AZURE_OPENAI_DEPLOYMENT_NAME

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
