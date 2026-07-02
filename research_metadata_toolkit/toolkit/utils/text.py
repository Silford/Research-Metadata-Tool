"""Text normalization and collection helpers."""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable

import pandas as pd


def normalize_text(value: object) -> str:
    """Return lowercase ASCII-normalized text with collapsed whitespace."""

    if value is None or pd.isna(value):
        return ""

    text = unicodedata.normalize("NFKD", str(value))
    text = text.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", text).strip().lower()


def unique_pipe_join(values: Iterable[object]) -> str:
    """Join unique non-empty values with a pipe separator."""

    cleaned = sorted({str(value).strip() for value in values if str(value).strip()})
    return " | ".join(cleaned)
