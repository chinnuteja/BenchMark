"""Tests for tender_timeline.grader and JSON extraction."""

import json

import pytest

from tender_timeline.grader import grade_prediction
from tender_timeline.schema import TenderTimelineItem
from tender_timeline.utils import extract_json_from_text, repo_root

ITEMS_DIR = repo_root() / "data" / "public_dev" / "items"


def _load_item(item_id: str) -> TenderTimelineItem:
    path = ITEMS_DIR / f"{item_id}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return TenderTimelineItem.model_validate(raw)


def _expected_dict(item: TenderTimelineItem) -> dict:
    return item.expected_answer.model_dump()


def test_exact_expected_answer_passes_strict_score() -> None:
    item = _load_item("tt_item_001_late_submission")
    result = grade_prediction(item, prediction=_expected_dict(item))
    assert result["strict_score"] == 1
    assert result["passed"] is True
    assert result["clause_grounding_score"] == 1


def test_wrong_verdict_fails() -> None:
    item = _load_item("tt_item_001_late_submission")
    prediction = _expected_dict(item)
    prediction["verdict"] = "VALID"
    prediction["failure_reason_code"] = "VALID"
    result = grade_prediction(item, prediction=prediction)
    assert result["strict_score"] == 0
    assert result["verdict_score"] == 0
    assert "wrong_verdict" in result["errors"]


def test_correct_verdict_wrong_clause_fails_strict_score() -> None:
    item = _load_item("tt_item_003_valid_control")
    prediction = _expected_dict(item)
    prediction["governing_clause_id"] = "Tender Data Sheet deadline"
    prediction["citation"] = {"rule": "Tender Data Sheet"}
    result = grade_prediction(item, prediction=prediction)
    assert result["verdict_score"] == 1
    assert result["clause_grounding_score"] == 0
    assert result["strict_score"] == 0
    assert "wrong_clause_grounding" in result["errors"]


def test_item_002_june_10_base_deadline_answer_fails() -> None:
    item = _load_item("tt_item_002_bid_security_short")
    prediction = {
        "governing_clause_id": "Tender Data Sheet deadline",
        "operative_deadline": "2026-06-10T10:00:00+03:00",
        "action_datetime": "2026-06-14T09:58:00+03:00",
        "required_bid_security_validity_through": "2026-11-05",
        "submitted_bid_security_validity_through": "2026-11-06",
        "precondition_status": "satisfied",
        "verdict": "VALID",
        "failure_reason_code": "VALID",
        "citation": {"rule": "Tender Data Sheet"},
    }
    result = grade_prediction(item, prediction=prediction)
    assert result["strict_score"] == 0
    assert result["verdict_score"] == 0
    assert result["clause_grounding_score"] == 0
    assert any(
        "Addendum 2 extended deadline" in message for message in result["diagnosis"]
    )


def test_parse_error_returns_zero_scores_and_parse_diagnosis() -> None:
    item = _load_item("tt_item_006_uganda_admin_review_late")
    result = grade_prediction(
        item,
        prediction=None,
        raw_output="The filing was late.",
    )
    assert result["strict_score"] == 0
    assert result["verdict_score"] == 0
    assert "parse_error" in result["errors"]
    assert "Model output could not be parsed as JSON." in result["diagnosis"]


@pytest.mark.parametrize(
    ("text", "expected_verdict"),
    [
        ('{"verdict":"VALID"}', "VALID"),
        (
            'Here is the answer:\n```json\n{"verdict":"INVALID"}\n```',
            "INVALID",
        ),
    ],
)
def test_extract_json_from_text_success_cases(text: str, expected_verdict: str) -> None:
    parsed, error = extract_json_from_text(text)
    assert error is None
    assert parsed is not None
    assert parsed["verdict"] == expected_verdict


def test_extract_json_from_text_prose_fails() -> None:
    parsed, error = extract_json_from_text("The answer is invalid because it is late.")
    assert parsed is None
    assert error is not None
    assert error.startswith("parse_error:")
