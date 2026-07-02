"""Country and university matching for Caribbean affiliation detection."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from importlib import resources

from research_metadata_toolkit.toolkit.utils.text import normalize_text

DATA_PACKAGE = "research_metadata_toolkit.data"


def _load_json_list(filename: str) -> list[str]:
    with resources.files(DATA_PACKAGE).joinpath(filename).open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return [str(item) for item in payload]


@lru_cache(maxsize=1)
def get_countries() -> tuple[str, ...]:
    """Return configured Caribbean country names and aliases."""

    return tuple(_load_json_list("countries.json"))


@lru_cache(maxsize=1)
def get_universities() -> tuple[str, ...]:
    """Return configured Caribbean university names and aliases."""

    return tuple(_load_json_list("universities.json"))


def is_caribbean_country(value: object, *, exact_words: bool = True) -> bool:
    """Return True when a value contains a configured Caribbean country name."""

    if not value:
        return False

    value_l = normalize_text(value)
    if not value_l:
        return False

    for country in get_countries():
        country_l = normalize_text(country)
        if not country_l:
            continue
        if exact_words:
            if re.search(rf"(?<!\w){re.escape(country_l)}(?!\w)", value_l):
                return True
        elif value_l == country_l or country_l in value_l:
            return True
    return False


def is_caribbean_institution(value: object) -> bool:
    """Return True when a value contains a configured Caribbean university name."""

    if not value:
        return False
    value_l = normalize_text(value)
    return bool(value_l) and any(normalize_text(university) in value_l for university in get_universities())
