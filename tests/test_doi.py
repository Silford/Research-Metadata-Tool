import pandas as pd

from research_metadata_toolkit.toolkit.doi.processor import extract_crossref, extract_openalex, resolve_doi_column
from research_metadata_toolkit.toolkit.utils.doi import clean_doi, extract_doi_from_text


def test_clean_doi_removes_trailing_punctuation() -> None:
    assert clean_doi("10.1234/example.") == "10.1234/example"


def test_extract_doi_from_text() -> None:
    assert extract_doi_from_text("https://doi.org/10.1000/xyz123") == "10.1000/xyz123"


def test_resolve_doi_column_finds_document_doi() -> None:
    df = pd.DataFrame({"Document DOI": ["10.1000/test"]})
    assert resolve_doi_column(df) == "Document DOI"


def test_extract_openalex_flags_caribbean_affiliation() -> None:
    work = {
        "authorships": [
            {
                "author": {"display_name": "Ada Researcher"},
                "institutions": [{"display_name": "University of the West Indies", "country": "Jamaica"}],
            }
        ]
    }
    assert extract_openalex(work) == ("Ada Researcher", "University of the West Indies", "TRUE")


def test_extract_crossref_flags_caribbean_affiliation() -> None:
    work = {"author": [{"given": "Ada", "family": "Researcher", "affiliation": [{"name": "University of Guyana"}]}]}
    assert extract_crossref(work) == ("Ada Researcher", "University of Guyana", "TRUE")
