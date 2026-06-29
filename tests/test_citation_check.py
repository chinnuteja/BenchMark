"""Tests for tender_timeline.citation_check."""

from tender_timeline.citation_check import has_required_clause_keywords


def test_keywords_found_in_governing_clause_id() -> None:
    prediction = {
        "governing_clause_id": "ITB 19.3 read with Addendum 2 §1",
        "citation": {},
    }
    passed, missing = has_required_clause_keywords(
        prediction,
        ["ITB 19.3", "Addendum 2"],
    )
    assert passed
    assert missing == []


def test_keywords_found_in_citation_dict() -> None:
    prediction = {
        "governing_clause_id": "Submission deadline rule",
        "citation": {"rule": "ITB 19.3", "deadline": "Addendum 2"},
    }
    passed, missing = has_required_clause_keywords(
        prediction,
        ["ITB 19.3", "Addendum 2"],
    )
    assert passed
    assert missing == []


def test_missing_keyword_fails() -> None:
    prediction = {
        "governing_clause_id": "ITB 19.3",
        "citation": {"rule": "ITB 19.3"},
    }
    passed, missing = has_required_clause_keywords(
        prediction,
        ["ITB 19.3", "Addendum 2"],
    )
    assert not passed
    assert missing == ["Addendum 2"]


def test_case_insensitive_matching() -> None:
    prediction = {
        "governing_clause_id": "itb 19.3 read with addendum 2",
        "citation": {},
    }
    passed, missing = has_required_clause_keywords(
        prediction,
        ["ITB 19.3", "Addendum 2"],
    )
    assert passed
    assert missing == []


def test_section_symbol_spacing_normalizes() -> None:
    prediction = {
        "governing_clause_id": "4 CFR § 21.2(a)(1)",
        "citation": {},
    }
    passed, missing = has_required_clause_keywords(
        prediction,
        ["4 CFR §21.2(a)(1)"],
    )
    assert passed
    assert missing == []


def test_multiple_spaces_normalize() -> None:
    prediction = {
        "governing_clause_id": "ITB  19.3   read   with   Addendum   2",
        "citation": {},
    }
    passed, missing = has_required_clause_keywords(
        prediction,
        ["ITB 19.3", "Addendum 2"],
    )
    assert passed
    assert missing == []


def test_genuinely_missing_clause_still_fails() -> None:
    prediction = {
        "governing_clause_id": "4 CFR § 21.2(a)(2)",
        "citation": {"rule": "4 CFR § 21.2(a)(2)"},
    }
    passed, missing = has_required_clause_keywords(
        prediction,
        ["4 CFR §21.2(a)(1)"],
    )
    assert not passed
    assert missing == ["4 CFR §21.2(a)(1)"]
