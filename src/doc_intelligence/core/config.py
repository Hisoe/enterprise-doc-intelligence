"""Application settings managed via Pydantic v2."""

from enum import StrEnum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentType(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Core Application Settings
    APP_NAME: str = "Enterprise Document Intelligence"
    ENVIRONMENT: EnvironmentType = EnvironmentType.DEVELOPMENT
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Azure OpenAI Configuration (Primary Provider)
    AZURE_OPENAI_ENDPOINT: str | None = Field(
        default=None,
        description="Azure OpenAI endpoint URL, e.g., https://your-resource.openai.azure.com/",
    )
    AZURE_OPENAI_API_KEY: str | None = Field(default=None)
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4o-mini"

    # Direct OpenAI Configuration (Fallback Provider)
    OPENAI_API_KEY: str | None = Field(default=None)
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Observability & Tracing (Langfuse)
    LANGFUSE_PUBLIC_KEY: str | None = Field(default=None)
    LANGFUSE_SECRET_KEY: str | None = Field(default=None)
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"

    @property
    def is_azure_configured(self) -> bool:
        """Check if Azure OpenAI credentials are available."""
        return bool(self.AZURE_OPENAI_ENDPOINT and self.AZURE_OPENAI_API_KEY)


# Singleton instance loaded once on module import
settings = Settings()
