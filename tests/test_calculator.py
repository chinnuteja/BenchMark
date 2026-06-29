"""Tests for tender_timeline.calculator (procedural oracle)."""

from __future__ import annotations

import pytest

from tender_timeline.calculator import (
    CalculatorError,
    compute_admin_review_window,
    compute_bid_security_cascade,
    compute_from_spec,
    compute_protest_window,
)
from tender_timeline.normalize import date_or_datetime_equal

# ── bid_security_cascade ────────────────────────────────────────────────────


KENYA_SPEC = {
    "rule_type": "bid_security_cascade",
    "governing_clause_id": "ITB 19.3 read with ITB 18.1 and Addendum 2 §1",
    "calendar_id": "kenya_2026_demo",
    "base_deadline": "2026-06-10T10:00:00+03:00",
    "addendum_deadline": "2026-06-14T10:00:00+03:00",
    "bid_validity_days": 120,
    "bid_security_extra_days": 28,
}


def test_cascade_invalid_bid_security(item_002_action_log: dict) -> None:
    """Item 002: timely submission but security expires Nov 6 < required Nov 9."""
    r = compute_bid_security_cascade(KENYA_SPEC, item_002_action_log)
    assert r.operative_deadline == "2026-06-14T10:00:00+03:00"
    assert r.controlling_basis == "addendum"
    assert r.required_bid_security_validity_through == "2026-11-09"
    assert r.verdict == "INVALID"
    assert r.failure_reason_code == "INSUFFICIENT_BID_SECURITY_VALIDITY"


def test_cascade_valid_control(item_003_action_log: dict) -> None:
    """Item 003: timely submission and security through Nov 10 >= required Nov 9."""
    r = compute_bid_security_cascade(KENYA_SPEC, item_003_action_log)
    assert r.required_bid_security_validity_through == "2026-11-09"
    assert r.verdict == "VALID"
    assert r.failure_reason_code == "VALID"


def test_cascade_late_submission(item_001_action_log: dict) -> None:
    """Item 001: submission 10:03 after 10:00 deadline."""
    r = compute_bid_security_cascade(KENYA_SPEC, item_001_action_log)
    assert r.verdict == "INVALID"
    assert r.failure_reason_code == "LATE_SUBMISSION"


def test_cascade_base_trap() -> None:
    """If a model uses base Jun 10, required-through becomes Nov 5 (the trap).

    Use a submission that is timely w.r.t. the base Jun 10 deadline so the
    cascade arithmetic runs. With Nov 6 submitted and only Nov 5 required the
    result is VALID — that is the trap a model falls into.
    """
    base_spec = {
        "rule_type": "bid_security_cascade",
        "base_deadline": "2026-06-10T10:00:00+03:00",
        "addendum_deadline": None,
        "bid_validity_days": 120,
        "bid_security_extra_days": 28,
    }
    r = compute_bid_security_cascade(
        base_spec,
        # Use Jun 9 submission so it is before the base Jun 10 deadline
        {"submission_datetime": "2026-06-09T09:58:00+03:00", "bid_security_valid_through": "2026-11-06"},
    )
    assert r.required_bid_security_validity_through == "2026-11-05"
    # Nov 6 submitted >= Nov 5 required → VALID from base POV (the trap)
    assert r.verdict == "VALID"


def test_cascade_addendum_overrides_base() -> None:
    """Addendum deadline takes precedence over base when both are present."""
    r = compute_bid_security_cascade(
        KENYA_SPEC,
        {"submission_datetime": "2026-06-14T09:58:00+03:00", "bid_security_valid_through": "2026-11-06"},
    )
    assert r.controlling_basis == "addendum"
    assert date_or_datetime_equal(r.operative_deadline, "2026-06-14T10:00:00+03:00")


# ── protest_window ──────────────────────────────────────────────────────────


def test_protest_apparent_impropriety_late() -> None:
    """Item 004: protest filed 2026-07-21 after proposal deadline 2026-07-20."""
    spec = {
        "rule_type": "protest_window",
        "protest_subtype": "apparent_solicitation_impropriety",
        "governing_clause_id": "4 CFR §21.2(a)(1)",
        "proposal_deadline": "2026-07-20T17:00:00-04:00",
    }
    r = compute_protest_window(spec, {"protest_filed": "2026-07-21T09:00:00-04:00"})
    assert r.operative_deadline == "2026-07-20T17:00:00-04:00"
    assert r.verdict == "INVALID"
    assert r.failure_reason_code == "MISSED_PROTEST_WINDOW"


def test_protest_known_basis_timely() -> None:
    """Item 005: basis known Aug 5 + 10 days = Aug 15 23:59; filed Aug 14 → VALID."""
    spec = {
        "rule_type": "protest_window",
        "protest_subtype": "known_basis",
        "governing_clause_id": "4 CFR §21.2(a)(2)",
        "known_basis_window_days": 10,
        "deadline_tz_offset": "-04:00",
        "deadline_end_of_day_time": "23:59:00",
    }
    r = compute_protest_window(spec, {"basis_known_date": "2026-08-05", "protest_filed": "2026-08-14T15:30:00-04:00"})
    assert r.operative_deadline == "2026-08-15T23:59:00-04:00"
    assert r.verdict == "VALID"
    assert r.failure_reason_code == "VALID"


def test_protest_unknown_subtype_raises() -> None:
    with pytest.raises(CalculatorError, match="unknown protest_subtype"):
        compute_protest_window({"protest_subtype": "unknown"}, {})


# ── admin_review_window ─────────────────────────────────────────────────────


def test_admin_review_late() -> None:
    """Item 006: received Sep 1 + 10 days = Sep 11 23:59; filed Sep 12 → INVALID."""
    spec = {
        "rule_type": "admin_review_window",
        "governing_clause_id": "Demo Rule 10.1",
        "window_days": 10,
        "deadline_tz_offset": "+03:00",
        "deadline_end_of_day_time": "23:59:00",
    }
    r = compute_admin_review_window(spec, {"decision_received": "2026-09-01", "review_filed": "2026-09-12T10:00:00+03:00"})
    assert r.operative_deadline == "2026-09-11T23:59:00+03:00"
    assert r.verdict == "INVALID"
    assert r.failure_reason_code == "MISSED_PROTEST_WINDOW"


# ── compute_from_spec dispatch ──────────────────────────────────────────────


def test_compute_from_spec_dispatches_correctly() -> None:
    r = compute_from_spec(
        {**KENYA_SPEC},
        {"submission_datetime": "2026-06-14T09:58:00+03:00", "bid_security_valid_through": "2026-11-06"},
    )
    assert r.verdict == "INVALID"


def test_compute_from_spec_unknown_rule_raises() -> None:
    with pytest.raises(CalculatorError, match="unknown rule_type"):
        compute_from_spec({"rule_type": "not_real"}, {})


# ── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def item_001_action_log() -> dict:
    return {"submission_datetime": "2026-06-14T10:03:00+03:00"}


@pytest.fixture
def item_002_action_log() -> dict:
    return {
        "submission_datetime": "2026-06-14T09:58:00+03:00",
        "bid_security_valid_through": "2026-11-06",
    }


@pytest.fixture
def item_003_action_log() -> dict:
    return {
        "submission_datetime": "2026-06-14T09:58:00+03:00",
        "bid_security_valid_through": "2026-11-10",
    }
