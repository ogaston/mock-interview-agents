"""
Configuration settings for the Mock Interview Agent backend.
"""
import os
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Provider Settings
    llm_provider: Literal["openai", "anthropic", "google"] = "openai"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    google_api_key: str | None = None
    google_model: str = "gemini-1.5-flash"

    # Application Settings
    environment: str = "development"
    log_level: str = "INFO"

    # LangSmith Tracing (support both LANGCHAIN_ and LANGSMITH_ prefixes)
    langchain_tracing_v2: str = "true"
    langchain_project: str = "mock-interview-agent"
    langchain_api_key: str | None = None
    
    # Also read LANGSMITH_ prefixed variables (these take precedence if set)
    langsmith_tracing: str | None = None
    langsmith_project: str | None = None
    langsmith_api_key: str | None = None
    langsmith_endpoint: str | None = None

    # Interview Settings
    max_questions_per_interview: int = 10
    default_interview_duration_minutes: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def get_llm_config(self) -> dict:
        """Get LLM configuration based on the selected provider."""
        if self.llm_provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.openai_model
            }
        elif self.llm_provider == "anthropic":
            return {
                "provider": "anthropic",
                "api_key": self.anthropic_api_key,
                "model": self.anthropic_model
            }
        elif self.llm_provider == "google":
            return {
                "provider": "google",
                "api_key": self.google_api_key,
                "model": self.google_model
            }
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")


# Initialize settings
settings = Settings()

# CRITICAL: Set LangSmith environment variables in os.environ
# LangChain reads these directly from os.environ, not from the Settings object
# Prefer LANGSMITH_ prefixed variables, fallback to LANGCHAIN_ prefixed ones

# Set tracing flag
tracing_value = settings.langsmith_tracing or settings.langchain_tracing_v2
if tracing_value:
    os.environ["LANGCHAIN_TRACING_V2"] = tracing_value
    os.environ["LANGSMITH_TRACING"] = tracing_value

# Set project name
project_value = settings.langsmith_project or settings.langchain_project
if project_value:
    os.environ["LANGSMITH_PROJECT"] = project_value
    os.environ["LANGCHAIN_PROJECT"] = project_value

# Set API key
api_key_value = settings.langsmith_api_key or settings.langchain_api_key
if api_key_value:
    os.environ["LANGSMITH_API_KEY"] = api_key_value
    os.environ["LANGCHAIN_API_KEY"] = api_key_value

# Set endpoint if provided
if settings.langsmith_endpoint:
    os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
