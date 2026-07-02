"""Excel text encoding cleanup."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import logging

import ftfy
import pandas as pd

from research_metadata_toolkit.toolkit.utils.excel import load_excel, save_excel, strip_column_names
from research_metadata_toolkit.toolkit.utils.logging import get_logger
from research_metadata_toolkit.toolkit.utils.progress import progress

LOGGER = get_logger(__name__)


def fix_encoding(
    input_file: str | Path,
    output_file: str | Path,
    columns_to_fix: Iterable[str] = ("Title", "Authors"),
) -> str:
    """Fix mojibake and text encoding issues in selected Excel columns.

    Args:
        input_file: Source Excel workbook path.
        output_file: Destination Excel workbook path.
        columns_to_fix: Column names to clean when present.

    Returns:
        The output workbook path as a string.
    """

    df = strip_column_names(load_excel(input_file))
    columns = list(columns_to_fix)
    available_columns = [col for col in columns if col in df.columns]

    for col in columns:
        if col not in df.columns:
            LOGGER.warning("Column not found: %s", col)
            continue
        df[col] = [
            ftfy.fix_text(str(value)) if pd.notna(value) else value
            for value in progress(
                df[col],
                desc=f"Fixing {col}",
                unit="cell",
                leave=len(available_columns) == 1,
            )
        ]

    if not available_columns:
        LOGGER.warning("No supported text columns found to clean.")
    else:
        LOGGER.info("Encoding fixed for: %s", ", ".join(available_columns))

    save_excel(df, output_file)
    LOGGER.info("Saved cleaned workbook to: %s", output_file)
    return str(output_file)
