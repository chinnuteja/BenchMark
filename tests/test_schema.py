"""Tests for tender_timeline.schema."""

import pytest
from pydantic import ValidationError

from tender_timeline.schema import FAILURE_REASON_CODES, TenderTimelineAnswer


def test_valid_answer_parses() -> None:
    answer = TenderTimelineAnswer(
        governing_clause_id="Addendum 2 §1 read with ITB 22.1",
        operative_deadline="2026-06-14T10:00:00+03:00",
        action_datetime="2026-06-14T10:03:00+03:00",
        precondition_status="not_evaluated",
        verdict="INVALID",
        failure_reason_code="LATE_SUBMISSION",
        citation={"deadline": "Addendum 2 §1; ITB 22.1"},
    )
    assert answer.verdict == "INVALID"
    assert answer.failure_reason_code == "LATE_SUBMISSION"


def test_lowercase_verdict_and_failure_code_normalize() -> None:
    answer = TenderTimelineAnswer(
        governing_clause_id="Addendum 2 §1",
        precondition_status="not_evaluated",
        verdict="invalid",
        failure_reason_code="late_submission",
        citation={},
    )
    assert answer.verdict == "INVALID"
    assert answer.failure_reason_code == "LATE_SUBMISSION"


def test_invalid_failure_code_fails() -> None:
    with pytest.raises(ValidationError):
        TenderTimelineAnswer(
            governing_clause_id="ITB 22.1",
            precondition_status="not_evaluated",
            verdict="INVALID",
            failure_reason_code="NOT_A_REAL_CODE",
            citation={},
        )


def test_missing_required_fields_fail() -> None:
    with pytest.raises(ValidationError):
        TenderTimelineAnswer(
            governing_clause_id="ITB 22.1",
            verdict="INVALID",
            failure_reason_code="LATE_SUBMISSION",
            citation={},
        )

    with pytest.raises(ValidationError):
        TenderTimelineAnswer(
            precondition_status="not_evaluated",
            verdict="INVALID",
            failure_reason_code="LATE_SUBMISSION",
            citation={},
        )


def test_failure_reason_codes_list_is_complete() -> None:
    assert "VALID" in FAILURE_REASON_CODES
    assert len(FAILURE_REASON_CODES) == 9
