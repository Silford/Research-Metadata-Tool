"""Crossref metadata access."""

from __future__ import annotations

from typing import Any
import requests

from research_metadata_toolkit.toolkit.config import DEFAULT_SETTINGS, ToolkitSettings
from research_metadata_toolkit.toolkit.utils.http import request_json


def fetch_crossref_by_doi(
    doi: str,
    *,
    session: requests.Session | None = None,
    settings: ToolkitSettings = DEFAULT_SETTINGS,
) -> dict[str, Any] | None:
    """Fetch a Crossref work message by DOI, returning None when unavailable."""

    url = f"https://api.crossref.org/works/{doi}"
    payload = request_json(url, session=session, settings=settings)
    if not payload:
        return None
    message = payload.get("message")
    return message if isinstance(message, dict) else None
