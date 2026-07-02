"""Centralized runtime settings for toolkit workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class ToolkitSettings:
    """Runtime settings shared by all toolkit modules."""

    doi_max_workers: int = 10
    url_max_workers: int = 30
    request_timeout: int = 8
    request_retries: int = 2
    retry_backoff_seconds: float = 0.5
    check_url_access: bool = False
    http_pool_size: int = 50
    http_headers: Mapping[str, str] = field(
        default_factory=lambda: {
            "User-Agent": "Mozilla/5.0 (compatible; URLMetadataBot/1.0; +https://example.org/bot)"
        }
    )


DEFAULT_SETTINGS = ToolkitSettings()
