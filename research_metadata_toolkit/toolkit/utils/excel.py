"""Excel loading, cleaning, and saving helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd

from research_metadata_toolkit.toolkit.exceptions import ExcelFileError, MissingColumnError


def load_excel(path: str | Path) -> pd.DataFrame:
    """Load an Excel workbook into a DataFrame with a clear error on failure."""

    try:
        return pd.read_excel(path)
    except FileNotFoundError as exc:
        raise ExcelFileError(f"Excel file not found: {path}") from exc
    except Exception as exc:
        raise ExcelFileError(f"Could not read Excel file {path}: {exc}") from exc


def save_excel(df: pd.DataFrame, path: str | Path) -> None:
    """Save a DataFrame to an Excel workbook."""

    try:
        df.to_excel(path, index=False)
    except Exception as exc:
        raise ExcelFileError(f"Could not save Excel file {path}: {exc}") from exc


def save_excel_sheets(sheets: Mapping[str, pd.DataFrame], path: str | Path) -> None:
    """Save multiple DataFrames as worksheets in one Excel workbook."""

    try:
        with pd.ExcelWriter(path) as writer:
            for sheet_name, frame in sheets.items():
                frame.to_excel(writer, sheet_name=sheet_name, index=False)
    except Exception as exc:
        raise ExcelFileError(f"Could not save Excel file {path}: {exc}") from exc


def strip_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of a DataFrame with surrounding column whitespace removed."""

    cleaned = df.copy()
    cleaned.columns = [str(col).strip() for col in cleaned.columns]
    return cleaned


def drop_generated_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove unnamed and previously extracted columns from a DataFrame."""

    return df.loc[
        :,
        [
            not str(col).lower().startswith("unnamed")
            and not str(col).lower().endswith("_extracted")
            for col in df.columns
        ],
    ]


def resolve_required_column(df: pd.DataFrame, candidates: Iterable[str], label: str) -> str:
    """Resolve a required column by exact normalized name or contained label."""

    cleaned_to_original = {str(col).strip().lower(): str(col) for col in df.columns}

    for candidate in candidates:
        key = str(candidate).strip().lower()
        if key in cleaned_to_original:
            return cleaned_to_original[key]

    label_l = label.strip().lower()
    for cleaned_name, original_name in cleaned_to_original.items():
        if label_l in cleaned_name:
            return original_name

    raise MissingColumnError(
        f"No {label}-like column found. Available columns: " + ", ".join(map(str, df.columns))
    )


def resolve_optional_column(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    """Resolve an optional column by exact normalized name."""

    cleaned_to_original = {str(col).strip().lower(): str(col) for col in df.columns}

    for candidate in candidates:
        key = str(candidate).strip().lower()
        if key in cleaned_to_original:
            return cleaned_to_original[key]
    return None
