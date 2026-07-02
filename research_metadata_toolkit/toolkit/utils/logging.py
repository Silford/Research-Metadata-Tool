"""Logging setup helpers."""

from __future__ import annotations

import logging
import sys


def configure_logging(level: int | str = logging.INFO) -> None:
    """Configure process-wide logging for command-line usage."""

    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
        stream=sys.stdout,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a module logger."""

    return logging.getLogger(name)
