"""Configuration for the Finance Division service."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FIN_", env_file=".env", extra="ignore")

    # LLM — OpenAI-compatible (swap base_url for Ollama / PGX Nemotron)
    openai_api_key: str = "your-api-key"
    openai_base_url: str = "https://api.openai.com/v1"
    default_model: str = "gpt-4o"
    fast_model: str = "gpt-4o-mini"    # Cheap model for classification / quick tasks

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 3              # DB 3 — separate from simulation (DB 2) and ai (DB 0)

    # COMPLIANCE hard limits
    compliance_timeout_seconds: int = 30
    max_single_position_eur: float = 5_000.0
    max_daily_loss_eur: float = 500.0
    max_sector_concentration_pct: float = 40.0
    max_kelly_fraction: float = 0.33
    ruleset_version: str = "2026-03-20"

    # Blackout window (Friday CET, no trading)
    blackout_day_of_week: int = 4          # 0=Mon, 4=Fri
    blackout_start_hour: int = 13
    blackout_start_minute: int = 45
    blackout_end_hour: int = 16
    blackout_end_minute: int = 0

    # Drawdown thresholds (%)
    drawdown_warning_pct: float = 10.0
    drawdown_halt_24h_pct: float = 20.0
    drawdown_halt_72h_pct: float = 30.0

    # ORACLE monitoring
    monitored_symbols: list[str] = [
        "DAX", "SPX", "NKY", "BTC-USD", "ETH-USD",
        "EURUSD", "XAUUSD", "CL1",
    ]
    p0_move_threshold_pct: float = 2.0      # Index move % that triggers P0 alert

    # German tax
    sparerpauschbetrag_eur: float = 1_000.0  # Annual exemption per individual
    abgeltungssteuer_rate: float = 0.25      # 25% flat rate
    crypto_haltefrist_days: int = 365        # 1-year holding period for crypto tax exemption

    # OpenClaw Gateway integration
    # Set to ws://127.0.0.1:18789 when OpenClaw is running locally (same machine)
    # Set to ws://<tailscale-hostname>:18789 when running on a remote plutos node
    openclaw_gateway_url: str = ""          # Empty = push disabled (non-fatal)
    openclaw_default_session: str = "main"  # OpenClaw session to push notifications to

    # Service
    host: str = "0.0.0.0"
    port: int = 8008


settings = Settings()
