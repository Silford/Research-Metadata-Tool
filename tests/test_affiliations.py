from research_metadata_toolkit.toolkit.affiliations import is_caribbean_country, is_caribbean_institution


def test_country_detection_matches_country_names() -> None:
    assert is_caribbean_country("Department of Biology, Jamaica") is True
    assert is_caribbean_country("Department of Biology, Canada") is False


def test_university_detection_matches_configured_universities() -> None:
    assert is_caribbean_institution("The University of the West Indies, Mona") is True
    assert is_caribbean_institution("University of Toronto") is False
