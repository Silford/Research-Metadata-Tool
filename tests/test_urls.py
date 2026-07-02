import pandas as pd

from research_metadata_toolkit.toolkit.urls.processor import (
    extract_doi_from_url,
    extract_webpage_affiliation_info,
    parse_meta_tags,
    process_row,
)


def test_extract_doi_from_url() -> None:
    assert extract_doi_from_url("https://example.org/article/10.5555/abc.123") == "10.5555/abc.123"


def test_parse_meta_tags_extracts_citation_doi() -> None:
    html = '<meta name="citation_doi" content="10.1000/test">'
    assert parse_meta_tags(html)["citation_doi"] == ["10.1000/test"]


def test_extract_webpage_affiliation_info_flags_institution() -> None:
    metadata = {"affiliations": ["University of Belize"]}
    assert extract_webpage_affiliation_info(metadata) == ("University of Belize", True)


def test_process_row_without_url_needs_manual_review() -> None:
    result = process_row(pd.Series({"ArticleURL": ""}))
    assert result["URL_Accessible"] == "NOT CHECKED"
    assert result["Is_Caribbean_Affiliated"] == "FALSE"
    assert result["Manual_Review"] == "YES"
