"""HTTP session and retry helpers."""

from __future__ import annotations

import time
from typing import Any

import requests

from research_metadata_toolkit.toolkit.config import DEFAULT_SETTINGS, ToolkitSettings
from research_metadata_toolkit.toolkit.utils.logging import get_logger

LOGGER = get_logger(__name__)


def create_session(settings: ToolkitSettings = DEFAULT_SETTINGS) -> requests.Session:
    """Create a configured requests session."""

    session = requests.Session()
    session.headers.update(settings.http_headers)
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=settings.http_pool_size,
        pool_maxsize=settings.http_pool_size,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def request_json(
    url: str,
    *,
    session: requests.Session | None = None,
    settings: ToolkitSettings = DEFAULT_SETTINGS,
    expected_json_key: str | None = None,
) -> dict[str, Any] | None:
    """Request JSON with retries, returning None when no usable payload is available."""

    active_session = session or create_session(settings)
    for attempt in range(settings.request_retries):
        try:
            response = active_session.get(url, timeout=settings.request_timeout, allow_redirects=True)
            if response.status_code == 200:
                payload = response.json()
                if expected_json_key is None or expected_json_key in payload:
                    return payload
                return payload
            LOGGER.warning("HTTP %s for JSON request: %s", response.status_code, url)
        except requests.RequestException as exc:
            LOGGER.warning("JSON request failed for %s: %s", url, exc)

        if attempt < settings.request_retries - 1:
            time.sleep(settings.retry_backoff_seconds * (2**attempt))
    return None


def request_text(
    url: str,
    *,
    session: requests.Session | None = None,
    settings: ToolkitSettings = DEFAULT_SETTINGS,
) -> str | None:
    """Request text content with retries, returning None when unavailable."""

    active_session = session or create_session(settings)
    for attempt in range(settings.request_retries):
        try:
            response = active_session.get(url, timeout=settings.request_timeout, allow_redirects=True)
            if response.status_code == 200:
                return response.text
            LOGGER.warning("HTTP %s for text request: %s", response.status_code, url)
        except requests.RequestException as exc:
            LOGGER.warning("Text request failed for %s: %s", url, exc)

        if attempt < settings.request_retries - 1:
            time.sleep(settings.retry_backoff_seconds * (2**attempt))
    return None
