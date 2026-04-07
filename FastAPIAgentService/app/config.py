"""
Runtime configuration facade.

The codebase primarily reads configuration from environment variables and YAML files
under `app/config/`. Some modules (and tests) expect a python module `app.config`
exposing a `settings` object with common attributes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List


@dataclass(slots=True)
class Settings:
    # These defaults are intentionally lightweight; production should override via env.
    DATABASE_URL: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./app.db"))
    REDIS_URL: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    DJANGO_API_URL: str = field(default_factory=lambda: os.getenv("DJANGO_API_URL", "http://localhost:8000/api/v1"))
    DJANGO_API_TOKEN: str = field(default_factory=lambda: os.getenv("DJANGO_API_TOKEN", ""))

    QWEN_API_KEY: str = field(default_factory=lambda: os.getenv("QWEN_API_KEY", ""))
    QWEN_MODEL: str = field(default_factory=lambda: os.getenv("QWEN_MODEL", "qwen-plus"))

    SECRET_KEY: str = field(default_factory=lambda: os.getenv("SECRET_KEY", "change-me"))
    CORS_ORIGINS: List[str] = field(default_factory=lambda: os.getenv("CORS_ORIGINS", "*").split(","))


settings = Settings()

