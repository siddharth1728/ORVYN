"""Application configuration management via Pydantic Settings."""

from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application
    app_env: Literal["development", "production", "test"] = "development"
    app_name: str = "ORVYN"
    app_debug: bool = True
    port: int = 8000
    host: str = "0.0.0.0"
    secret_key: str = "change-this-in-production-to-a-secure-random-32-byte-hex"

    # Database & Storage
    database_url: str = "postgresql+asyncpg://orvyn:orvyn_secret@localhost:5432/orvyn"
    database_echo: bool = False
    redis_url: str = "redis://localhost:6379/0"

    # LLM Provider
    default_llm_provider: Literal["gemini", "openai", "anthropic", "mock"] = "mock"
    default_llm_model: str = "gemini-2.5-flash"
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # Telephony
    telephony_provider: Literal["mock", "twilio", "vapi"] = "mock"
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_from_phone_number: str | None = None
    vapi_api_key: str | None = None
    vapi_phone_number_id: str | None = None

    # User Defaults for Notifications & Interventions
    default_user_phone: str = "+10000000000"
    default_user_name: str = "Engineer"


settings = Settings()
