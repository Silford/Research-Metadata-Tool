"""OpenAlex metadata access."""

from __future__ import annotations

from typing import Any

import requests

from research_metadata_toolkit.toolkit.config import DEFAULT_SETTINGS, ToolkitSettings
from research_metadata_toolkit.toolkit.utils.http import request_json


def fetch_openalex_by_doi(
    doi: str,
    *,
    session: requests.Session | None = None,
    settings: ToolkitSettings = DEFAULT_SETTINGS,
) -> dict[str, Any] | None:
    """Fetch an OpenAlex work by DOI, returning None when unavailable."""

    url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    return request_json(url, session=session, settings=settings)
