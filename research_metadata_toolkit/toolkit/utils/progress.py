"""Progress-bar utilities."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import TypeVar

from tqdm import tqdm

T = TypeVar("T")


def progress(iterable: Iterable[T], **kwargs: object) -> Iterator[T]:
    """Wrap an iterable with tqdm using project defaults."""

    defaults = {"dynamic_ncols": True, "colour": "cyan"}
    defaults.update(kwargs)
    yield from tqdm(iterable, **defaults)
