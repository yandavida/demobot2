# config.py
from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    saas_api_base_url: str = os.getenv("SAAS_API_BASE_URL", "http://localhost:8000")
    saas_api_key: str = os.getenv("SAAS_API_KEY", "DEMOBOT_API_KEY")

    # לעתיד:
    db_url: str | None = os.getenv("SAAS_DB_URL")
    pricing_engine: str = os.getenv("PRICING_ENGINE", "black_scholes")


settings = Settings()
