"""DOI-based scholarly metadata enrichment."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd

from research_metadata_toolkit.toolkit.affiliations import is_caribbean_country, is_caribbean_institution
from research_metadata_toolkit.toolkit.api import fetch_crossref_by_doi, fetch_openalex_by_doi
from research_metadata_toolkit.toolkit.config import DEFAULT_SETTINGS, ToolkitSettings
from research_metadata_toolkit.toolkit.utils.doi import clean_doi
from research_metadata_toolkit.toolkit.utils.excel import (
    drop_generated_columns,
    load_excel,
    resolve_optional_column,
    resolve_required_column,
    save_excel_sheets,
    strip_column_names,
)
from research_metadata_toolkit.toolkit.utils.logging import get_logger
from research_metadata_toolkit.toolkit.utils.progress import progress
from research_metadata_toolkit.toolkit.utils.text import unique_pipe_join

LOGGER = get_logger(__name__)


def get_crossref_author_name(author: dict[str, Any]) -> str:
    """Return a displayable author name from a Crossref author object."""

    full_name = str(author.get("name", "")).strip()
    if full_name:
        return full_name
    given = str(author.get("given", "")).strip()
    family = str(author.get("family", "")).strip()
    return " ".join(part for part in [given, family] if part).strip()


def resolve_doi_column(df: pd.DataFrame) -> str:
    """Resolve the DOI column in a spreadsheet."""

    return resolve_required_column(df, ["doi", "doi id", "doi_id", "document doi"], "doi")


def extract_openalex(work: dict[str, Any], doi: str = "") -> tuple[str, str, str]:
    """Extract authors, institutions, and Caribbean affiliation from OpenAlex metadata."""

    authors_list: list[str] = []
    universities_list: list[str] = []
    affiliated_flag = False

    for author in work.get("authorships", [])[:10]:
        author_name = author.get("author", {}).get("display_name", "")
        if author_name:
            authors_list.append(author_name)

        for inst in author.get("institutions", []):
            inst_name = inst.get("display_name", "")
            country_code = inst.get("country_code", "")
            country_name = inst.get("country", "")
            geo = inst.get("geo", {})
            country_geo = geo.get("country", "") if isinstance(geo, dict) else ""

            if inst_name:
                universities_list.append(inst_name)

            if (
                is_caribbean_institution(inst_name)
                or is_caribbean_country(country_name, exact_words=False)
                or is_caribbean_country(country_geo, exact_words=False)
                or is_caribbean_country(country_code, exact_words=False)
                or is_caribbean_country(inst_name, exact_words=False)
            ):
                affiliated_flag = True

    return (
        unique_pipe_join(authors_list),
        unique_pipe_join(universities_list),
        "TRUE" if affiliated_flag else "FALSE",
    )


def extract_crossref(work: dict[str, Any], doi: str = "") -> tuple[str, str, str]:
    """Extract authors, affiliations, and Caribbean affiliation from Crossref metadata."""

    authors_list: list[str] = []
    universities_list: list[str] = []
    affiliated_flag = False

    for author in work.get("author", [])[:10]:
        author_name = get_crossref_author_name(author)
        if author_name:
            authors_list.append(author_name)

        if is_caribbean_country(author.get("country", ""), exact_words=False):
            affiliated_flag = True

        for aff in author.get("affiliation", []):
            inst_name = aff.get("name", "")
            if inst_name:
                universities_list.append(inst_name)
            if is_caribbean_institution(inst_name) or is_caribbean_country(inst_name, exact_words=False):
                affiliated_flag = True

    return (
        unique_pipe_join(authors_list),
        unique_pipe_join(universities_list),
        "TRUE" if affiliated_flag else "FALSE",
    )


def process_row(doi: object, settings: ToolkitSettings = DEFAULT_SETTINGS) -> tuple[str, str, str]:
    """Process one DOI value and return extracted author, institution, and affiliation fields."""

    normalized_doi = clean_doi(doi)
    if not normalized_doi:
        return "", "", "Needs Manual Verification"

    work = fetch_openalex_by_doi(normalized_doi, settings=settings)
    if work:
        return extract_openalex(work, normalized_doi)

    work = fetch_crossref_by_doi(normalized_doi, settings=settings)
    if work:
        return extract_crossref(work, normalized_doi)

    return "", "", "Needs Manual Verification"


def process_doi_file(
    input_file: str | Path,
    output_file: str | Path | None = None,
    max_workers: int | None = None,
    settings: ToolkitSettings = DEFAULT_SETTINGS,
) -> str:
    """Enrich an Excel workbook using DOI metadata and write results plus manual review sheets."""

    df = strip_column_names(load_excel(input_file)).dropna(how="all")
    df = drop_generated_columns(df)
    doi_column = resolve_doi_column(df)
    df = df[df[doi_column].astype(str).str.strip() != ""].reset_index(drop=True)

    source_universities_col = resolve_optional_column(
        df,
        ["universities", "university", "affiliation", "affiliations", "institution", "institutions"],
    )
    row_count = len(df)
    authors_col = [""] * row_count
    universities_col = [""] * row_count
    caribbean_col = ["Needs Manual Verification"] * row_count
    manual_review_indices: list[int] = []

    workers = max_workers if max_workers is not None else settings.doi_max_workers
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_row, df.iloc[i].get(doi_column, ""), settings): i for i in range(row_count)}
        for future in progress(as_completed(futures), total=row_count, desc="Processing DOI rows", unit="row"):
            i = futures[future]
            authors, universities, caribbean = future.result()
            universities_value = universities

            if caribbean == "FALSE" and not str(universities_value).strip() and source_universities_col is not None:
                universities_value = str(df.iloc[i].get(source_universities_col, "")).strip()

            if caribbean == "FALSE" and not str(universities_value).strip():
                caribbean = "Manual Review"

            authors_col[i] = authors
            universities_col[i] = universities_value
            caribbean_col[i] = caribbean

            if caribbean in {"Needs Manual Verification", "Manual Review"}:
                manual_review_indices.append(i)

    df["Authors_Extracted"] = authors_col
    df["Universities"] = universities_col
    df["Is_Caribbean_Affiliated"] = caribbean_col
    manual_df = df.iloc[manual_review_indices].copy()

    resolved_output = Path(output_file) if output_file is not None else Path(input_file).with_name(f"{Path(input_file).stem}_results.xlsx")
    save_excel_sheets({"Results": df, "Manual Review": manual_df}, resolved_output)
    LOGGER.info("Saved DOI results to: %s", resolved_output)
    return str(resolved_output)
