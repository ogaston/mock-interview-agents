"""
Configuration settings for the Mock Interview Agent backend.
"""
import os
from typing import Literal
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_list(value: str) -> list[str]:
    """Parse comma-separated string into list, or return ['*'] if value is '*'."""
    return ["*"] if value == "*" else [item.strip() for item in value.split(",")]


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # model_config configures the Pydantic model's behavior
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # LLM Provider Settings
    llm_provider: Literal["openai", "anthropic", "google", "mock"] = "openai"
    use_mock_llm: bool = False  # Enable mock LLM responses (overrides provider)
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    google_api_key: str | None = None
    google_model: str = "gemini-1.5-flash"

    # Application Settings
    environment: str = "development"
    log_level: str = "INFO"

    # LangSmith Tracing
    langsmith_tracing: str | None = None
    langsmith_project: str | None = None
    langsmith_api_key: str | None = None
    langsmith_endpoint: str | None = None
    langchain_tracing_v2: str = "true"
    langchain_project: str = "mock-interview-agent"
    langchain_api_key: str | None = None

    # Interview Settings
    max_questions_per_interview: int = 10
    default_interview_duration_minutes: int = 30

    # CORS Settings
    cors_allow_origins: str = "*"
    cors_allow_credentials: bool = True
    cors_allow_methods: str = "*"
    cors_allow_headers: str = "*"

    # Voice Feature Settings
    enable_voice_features: bool = True
    tts_provider: Literal["elevenlabs", "openai", "mock"] = "elevenlabs"
    use_mock_tts: bool = False  # Enable mock TTS responses (overrides provider)
    stt_provider: Literal["browser", "openai"] = "openai"
    elevenlabs_api_key: str | None = None
    elevenlabs_model: str = "eleven_multilingual_v2"
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    elevenlabs_stability: float = 0.5
    elevenlabs_similarity_boost: float = 0.75

    def get_llm_config(self) -> dict:
        """Get LLM configuration based on the selected provider."""
        # Check if mock mode is enabled
        effective_provider = "mock" if self.use_mock_llm else self.llm_provider
        
        provider_configs = {
            "openai": {"api_key": self.openai_api_key, "model": self.openai_model},
            "anthropic": {"api_key": self.anthropic_api_key, "model": self.anthropic_model},
            "google": {"api_key": self.google_api_key, "model": self.google_model},
            "mock": {"api_key": None, "model": "mock-model"},
        }
        if effective_provider not in provider_configs:
            raise ValueError(f"Unsupported LLM provider: {effective_provider}")
        return {"provider": effective_provider, **provider_configs[effective_provider]}

    @computed_field
    @property
    def cors_origins_list(self) -> list[str]:
        return _parse_list(self.cors_allow_origins)

    @computed_field
    @property
    def cors_methods_list(self) -> list[str]:
        return _parse_list(self.cors_allow_methods)

    @computed_field
    @property
    def cors_headers_list(self) -> list[str]:
        return _parse_list(self.cors_allow_headers)


# Initialize settings
settings = Settings()

# Set LangSmith environment variables (LangChain reads from os.environ)
# Prefer LANGSMITH_ prefixed variables, fallback to LANGCHAIN_ prefixed ones
langsmith_vars = {
    "LANGCHAIN_TRACING_V2": settings.langsmith_tracing or settings.langchain_tracing_v2,
    "LANGSMITH_TRACING": settings.langsmith_tracing or settings.langchain_tracing_v2,
    "LANGSMITH_PROJECT": settings.langsmith_project or settings.langchain_project,
    "LANGCHAIN_PROJECT": settings.langsmith_project or settings.langchain_project,
    "LANGSMITH_API_KEY": settings.langsmith_api_key or settings.langchain_api_key,
    "LANGCHAIN_API_KEY": settings.langsmith_api_key or settings.langchain_api_key,
    "LANGSMITH_ENDPOINT": settings.langsmith_endpoint,
}

for key, value in langsmith_vars.items():
    if value:
        os.environ[key] = value
