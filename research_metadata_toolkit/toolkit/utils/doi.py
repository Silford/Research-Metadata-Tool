"""DOI parsing helpers."""

from __future__ import annotations

import re

import pandas as pd


DOI_PATTERN = r"(10\.\d{4,9}/[-._;()/:A-Z0-9]+)"


def clean_doi(value: object) -> str | None:
    """Normalize a DOI-like value or return None when it is empty."""

    if value is None or pd.isna(value):
        return None
    doi = str(value).strip().rstrip(".,);")
    return doi or None


def extract_doi_from_text(text: object) -> str | None:
    """Extract the first DOI from arbitrary text."""

    if not text:
        return None
    match = re.search(DOI_PATTERN, str(text), re.I)
    if not match:
        return None
    return match.group(1).strip().rstrip(".,);\"]'")


def extract_doi_from_url(url: object) -> str | None:
    """Extract the first DOI embedded in a URL."""

    if url is None or pd.isna(url):
        return None
    return extract_doi_from_text(str(url).strip())
