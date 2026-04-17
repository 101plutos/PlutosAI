"""Configuration for the simulation service."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SIM_", env_file=".env", extra="ignore")

    # LLM endpoint (OpenAI-compatible — swap base_url to point at local Ollama or PGX)
    openai_api_key: str = "your-api-key"
    openai_base_url: str = "https://api.openai.com/v1"
    default_model: str = "gpt-4o"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 2  # separate DB from ai-service
    simulation_cache_ttl_seconds: int = 3600 * 24  # 24h

    # Simulation limits
    max_rounds: int = 10
    max_seed_length: int = 20_000
    agent_timeout_seconds: int = 30

    # Service
    host: str = "0.0.0.0"
    port: int = 8007


settings = Settings()
