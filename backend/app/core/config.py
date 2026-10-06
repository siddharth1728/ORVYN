"""Core application settings using Pydantic Settings."""

import os
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

# Disable SQLAlchemy Cython C-extensions on Windows environments where local unsigned DLLs may be restricted
os.environ.setdefault("DISABLE_SQLALCHEMY_CEXT", "1")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General
    app_name: str = "ORVYN"
    app_env: Literal["development", "production", "test"] = "development"
    debug: bool = True
    secret_key: str = "change-this-in-production-to-a-secure-random-32-byte-hex"
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./orvyn.db"
    database_echo: bool = False

    # Message Broker
    redis_url: str = "redis://localhost:6379/0"

    # LLM Providers
    llm_provider: str = "mock"  # "mock", "gemini", "openai", "huggingface"
    llm_model: str = "default"
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    huggingface_api_key: str | None = None

    # Telephony Providers
    voice_provider: str = "mock"  # "mock", "twilio", "vapi"
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_phone_number: str | None = None

    # Search Providers
    search_provider: str = "mock"  # "mock", "tavily", "duckduckgo"
    tavily_api_key: str | None = None


settings = Settings()
