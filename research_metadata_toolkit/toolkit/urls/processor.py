"""URL-based scholarly metadata and affiliation extraction."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
import html
import json
import re

import pandas as pd
import requests

from research_metadata_toolkit.toolkit.affiliations import is_caribbean_country, is_caribbean_institution
from research_metadata_toolkit.toolkit.api import fetch_crossref_by_doi, fetch_openalex_by_doi
from research_metadata_toolkit.toolkit.config import DEFAULT_SETTINGS, ToolkitSettings
from research_metadata_toolkit.toolkit.utils.doi import extract_doi_from_text, extract_doi_from_url
from research_metadata_toolkit.toolkit.utils.excel import drop_generated_columns, load_excel, save_excel, strip_column_names
from research_metadata_toolkit.toolkit.utils.http import create_session, request_text
from research_metadata_toolkit.toolkit.utils.logging import get_logger
from research_metadata_toolkit.toolkit.utils.progress import progress
from research_metadata_toolkit.toolkit.utils.text import unique_pipe_join

LOGGER = get_logger(__name__)


def parse_meta_tags(html_content: str | None) -> dict[str, list[str]]:
    """Parse HTML meta tags into a mapping of meta key to content values."""

    meta_map: dict[str, list[str]] = {}
    meta_pattern = re.compile(r"<meta\s+[^>]*>", re.I)
    attr_pattern = re.compile(r"([\w:-]+)\s*=\s*([\"'])(.*?)\2", re.I | re.S)

    for tag in meta_pattern.findall(html_content or ""):
        attrs: dict[str, str] = {}
        for key, _, value in attr_pattern.findall(tag):
            attrs[key.lower()] = html.unescape(value).strip()

        key = attrs.get("name") or attrs.get("property") or attrs.get("itemprop")
        content = attrs.get("content", "").strip()
        if key and content:
            meta_map.setdefault(key.lower(), []).append(content)
    return meta_map


def extract_title(html_content: str | None, meta_map: dict[str, list[str]]) -> str | None:
    """Extract a page title from scholarly meta tags or the HTML title element."""

    for key in ["citation_title", "dc.title", "og:title", "twitter:title", "title"]:
        values = meta_map.get(key, [])
        if values:
            return values[0].strip()

    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_content or "", re.I | re.S)
    if title_match:
        return re.sub(r"\s+", " ", html.unescape(title_match.group(1))).strip()
    return None


def extract_jsonld_blocks(html_content: str | None) -> list[Any]:
    """Extract JSON-LD script blocks from HTML."""

    blocks: list[Any] = []
    pattern = re.compile(r"<script[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>", re.I | re.S)
    for raw_block in pattern.findall(html_content or ""):
        block = raw_block.strip()
        if not block:
            continue
        try:
            blocks.append(json.loads(block))
        except json.JSONDecodeError:
            LOGGER.warning("Skipping malformed JSON-LD block")
    return blocks


def collect_jsonld_fields(node: Any, dois: list[str], affiliations: list[str]) -> None:
    """Collect DOI and affiliation values recursively from parsed JSON-LD."""

    if isinstance(node, dict):
        for key, value in node.items():
            key_l = str(key).lower()
            if key_l in {"doi", "identifier"} and isinstance(value, str):
                candidate_doi = extract_doi_from_text(value)
                if candidate_doi:
                    dois.append(candidate_doi)

            if key_l == "affiliation":
                if isinstance(value, str):
                    affiliations.append(value)
                elif isinstance(value, dict):
                    name = value.get("name")
                    if isinstance(name, str) and name.strip():
                        affiliations.append(name.strip())
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str) and item.strip():
                            affiliations.append(item.strip())
                        elif isinstance(item, dict):
                            name = item.get("name")
                            if isinstance(name, str) and name.strip():
                                affiliations.append(name.strip())
            collect_jsonld_fields(value, dois, affiliations)
    elif isinstance(node, list):
        for item in node:
            collect_jsonld_fields(item, dois, affiliations)


def fetch_webpage_metadata(
    url: str,
    *,
    session: requests.Session | None = None,
    settings: ToolkitSettings = DEFAULT_SETTINGS,
) -> dict[str, Any] | None:
    """Fetch and parse DOI, title, and affiliation metadata from a webpage."""

    html_content = request_text(url, session=session, settings=settings)
    if not html_content:
        return None

    meta_map = parse_meta_tags(html_content)
    title = extract_title(html_content, meta_map)
    doi_candidates: list[str] = []
    affiliation_candidates: list[str] = []

    for key in ["citation_doi", "dc.identifier", "dc.identifier.doi", "prism.doi", "doi"]:
        for value in meta_map.get(key, []):
            candidate_doi = extract_doi_from_text(value)
            if candidate_doi:
                doi_candidates.append(candidate_doi)

    for key, values in meta_map.items():
        if any(token in key for token in ["affiliation", "institution", "university", "school"]):
            affiliation_candidates.extend([value for value in values if value])

    for block in extract_jsonld_blocks(html_content):
        collect_jsonld_fields(block, doi_candidates, affiliation_candidates)

    if not doi_candidates:
        body_doi = extract_doi_from_text(html_content)
        if body_doi:
            doi_candidates.append(body_doi)

    affiliations = sorted({aff.strip() for aff in affiliation_candidates if aff and aff.strip()})
    return {"title": title, "doi": doi_candidates[0] if doi_candidates else None, "affiliations": affiliations}


def extract_webpage_affiliation_info(metadata: dict[str, Any] | None) -> tuple[str | None, bool]:
    """Extract matching Caribbean institutions from parsed webpage metadata."""

    if not metadata:
        return None, False

    matched_unis: list[str] = []
    affiliated_flag = False
    for inst_name in metadata.get("affiliations", []):
        if is_caribbean_institution(inst_name):
            matched_unis.append(inst_name)
            affiliated_flag = True
        if is_caribbean_country(inst_name):
            affiliated_flag = True
    return unique_pipe_join(matched_unis) if matched_unis else None, affiliated_flag


def check_url_access(
    url: str,
    *,
    session: requests.Session | None = None,
    settings: ToolkitSettings = DEFAULT_SETTINGS,
) -> tuple[int | None, str, str]:
    """Check whether a URL is reachable."""

    if not url:
        return None, "NO", "NO URL"

    active_session = session or create_session(settings)
    try:
        response = active_session.get(url, timeout=settings.request_timeout, allow_redirects=True)
        is_success = 200 <= response.status_code < 300
        return response.status_code, "YES" if is_success else "NO", f"HTTP {response.status_code}"
    except requests.RequestException as exc:
        return None, "NO", f"EXCEPTION: {exc}"


def extract_affiliation_info(work: dict[str, Any] | None) -> tuple[str | None, bool]:
    """Extract Caribbean affiliation information from OpenAlex work metadata."""

    if not work:
        return None, False

    matched_unis: list[str] = []
    affiliated_flag = False

    for authorship in work.get("authorships", []):
        for inst in authorship.get("institutions", []):
            inst_name = inst.get("display_name", "")
            country_code = inst.get("country_code", "")
            country_name = inst.get("country", "")
            geo = inst.get("geo", {})
            geo_country = geo.get("country", "") if isinstance(geo, dict) else ""

            if is_caribbean_institution(inst_name):
                matched_unis.append(inst_name)
                affiliated_flag = True

            if (
                is_caribbean_country(country_code)
                or is_caribbean_country(country_name)
                or is_caribbean_country(geo_country)
                or is_caribbean_country(inst_name)
            ):
                affiliated_flag = True

    return unique_pipe_join(matched_unis) if matched_unis else None, affiliated_flag


def extract_crossref_affiliation_info(work: dict[str, Any] | None) -> tuple[str | None, bool]:
    """Extract Caribbean affiliation information from Crossref work metadata."""

    if not work:
        return None, False
    matched_unis: list[str] = []
    affiliated_flag = False

    for author in work.get("author", []):
        for aff in author.get("affiliation", []):
            inst_name = aff.get("name", "")
            if inst_name and is_caribbean_institution(inst_name):
                matched_unis.append(inst_name)
                affiliated_flag = True
            if is_caribbean_country(inst_name):
                affiliated_flag = True
    return unique_pipe_join(matched_unis) if matched_unis else None, affiliated_flag


def process_row(
    row: pd.Series,
    settings: ToolkitSettings = DEFAULT_SETTINGS,
    session: requests.Session | None = None,
) -> dict[str, object]:
    """Process one spreadsheet row and return URL affiliation result columns."""

    article_url_raw = row.get("ArticleURL", "")
    article_url = "" if pd.isna(article_url_raw) else str(article_url_raw).strip()
    url_status_code, url_accessible, url_check_detail = None, "NOT CHECKED", "NOT CHECKED"

    if settings.check_url_access:
        url_status_code, url_accessible, url_check_detail = check_url_access(article_url, session=session, settings=settings)

    doi = extract_doi_from_url(article_url)
    work = None
    webpage_metadata = None

    if doi:
        work = fetch_openalex_by_doi(doi, session=session, settings=settings)
        if not work:
            work = fetch_crossref_by_doi(doi, session=session, settings=settings)

    if not work and article_url:
        webpage_metadata = fetch_webpage_metadata(article_url, session=session, settings=settings)
        metadata_doi = webpage_metadata.get("doi") if webpage_metadata else None
        if metadata_doi and metadata_doi != doi:
            doi = metadata_doi
            work = fetch_openalex_by_doi(doi, session=session, settings=settings)
            if not work:
                work = fetch_crossref_by_doi(doi, session=session, settings=settings)

    if work and "authorships" in work:
        matched_unis, affiliated = extract_affiliation_info(work)
    elif work:
        matched_unis, affiliated = extract_crossref_affiliation_info(work)
    else:
        matched_unis, affiliated = extract_webpage_affiliation_info(webpage_metadata)

    is_caribbean_affiliated = "TRUE" if affiliated else "FALSE"
    has_metadata = bool(
        webpage_metadata
        and (webpage_metadata.get("title") or webpage_metadata.get("doi") or webpage_metadata.get("affiliations"))
    )
    manual_review = "YES" if ((not work and not has_metadata) or (is_caribbean_affiliated == "FALSE" and not matched_unis)) else "NO"

    return {
        "URL_Status_Code": url_status_code,
        "URL_Accessible": url_accessible,
        "URL_Check_Detail": url_check_detail,
        "Matched_Universities": matched_unis,
        "Is_Caribbean_Affiliated": is_caribbean_affiliated,
        "Manual_Review": manual_review,
    }


def process_url_file(
    input_file: str | Path,
    output_file: str | Path,
    max_workers: int | None = None,
    settings: ToolkitSettings = DEFAULT_SETTINGS,
) -> str:
    """Process an Excel workbook of ArticleURL values and write URL affiliation results."""

    df = drop_generated_columns(strip_column_names(load_excel(input_file)))
    results: list[dict[str, object] | None] = [None] * len(df)
    workers = max_workers if max_workers is not None else settings.url_max_workers

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_row, row, settings): i for i, (_, row) in enumerate(df.iterrows())}
        for future in progress(as_completed(futures), total=len(futures), desc="Processing URL rows", unit="row"):
            i = futures[future]
            try:
                results[i] = future.result()
            except Exception as exc:
                LOGGER.error("URL row processing failed: %s", exc)
                results[i] = {
                    "URL_Status_Code": None,
                    "URL_Accessible": "NO",
                    "URL_Check_Detail": f"ERROR: {exc}",
                    "Matched_Universities": None,
                    "Is_Caribbean_Affiliated": "FALSE",
                    "Manual_Review": f"ERROR: {exc}",
                }

    final_df = pd.concat([df.reset_index(drop=True), pd.DataFrame(results)], axis=1)
    save_excel(final_df, output_file)
    LOGGER.info("URL check + affiliation check complete.")
    LOGGER.info("Saved URL results to: %s", output_file)
    return str(output_file)
