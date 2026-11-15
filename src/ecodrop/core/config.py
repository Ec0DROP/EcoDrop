"""Application settings loaded from environment variables and validated on startup."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

ENVIRONMENTS = ("development", "test", "production")
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
MIN_PORT, MAX_PORT = 1, 65535


class ConfigError(ValueError):
    """Raised when the application configuration is invalid."""


@dataclass(frozen=True)
class Settings:
    env: str = "development"
    log_level: str = "INFO"
    host: str = "127.0.0.1"
    port: int = 8000

    def __post_init__(self) -> None:
        if self.env not in ENVIRONMENTS:
            raise ConfigError(
                f"Invalid env {self.env!r}; expected one of: {', '.join(ENVIRONMENTS)}"
            )
        if self.log_level not in LOG_LEVELS:
            raise ConfigError(
                f"Invalid log level {self.log_level!r}; expected one of: {', '.join(LOG_LEVELS)}"
            )
        if not self.host:
            raise ConfigError("Host must not be empty")
        if not MIN_PORT <= self.port <= MAX_PORT:
            raise ConfigError(f"Invalid port {self.port}; expected {MIN_PORT}-{MAX_PORT}")

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Settings:
        """Build settings from ``ECODROP_*`` environment variables."""
        environ = os.environ if environ is None else environ
        raw_port = environ.get("ECODROP_PORT", str(cls.port)).strip()
        try:
            port = int(raw_port)
        except ValueError:
            raise ConfigError(f"Invalid port {raw_port!r}; expected a number") from None
        return cls(
            env=environ.get("ECODROP_ENV", cls.env).strip().lower(),
            log_level=environ.get("ECODROP_LOG_LEVEL", cls.log_level).strip().upper(),
            host=environ.get("ECODROP_HOST", cls.host).strip(),
            port=port,
        )
