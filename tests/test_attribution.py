"""Tests for tender_timeline.attribution (failure localization)."""

from __future__ import annotations

import json


from tender_timeline.attribution import (
    CASCADE_ARITHMETIC_ERROR,
    CLAUSE_GROUNDING_FAILURE,
    DEADLINE_PRECISION_MISMATCH,
    PARSE_ERROR,
    WRONG_CONTROLLING_DEADLINE,
    WRONG_FAILURE_CODE,
    WRONG_OPERATIVE_DEADLINE,
    WRONG_RULE_SELECTION,
    WRONG_VERDICT,
    attribute_failure,
)
from tender_timeline.grader import grade_prediction
from tender_timeline.schema import TenderTimelineItem
from tender_timeline.utils import repo_root

ITEMS_DIR = repo_root() / "data" / "public_dev" / "items"


def _load_item(item_id: str) -> TenderTimelineItem:
    path = ITEMS_DIR / f"{item_id}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return TenderTimelineItem.model_validate(raw)


# ── parse error ─────────────────────────────────────────────────────────────


def test_parse_error_attribution() -> None:
    item = _load_item("tt_item_006_uganda_admin_review_late")
    result = attribute_failure(item, None)
    assert len(result) == 1
    assert result[0]["category"] == PARSE_ERROR


# ── clean pass → empty attribution ─────────────────────────────────────────


def test_clean_pass_yields_empty_attribution() -> None:
    item = _load_item("tt_item_003_valid_control")
    perfect = item.expected_answer.model_dump()
    result = attribute_failure(item, perfect)
    assert result == [], f"Expected empty attribution but got: {result}"


# ── CASCADE_ARITHMETIC_ERROR: the hero failure ──────────────────────────────


def test_hero_002_cascade_arithmetic_error() -> None:
    """Real Azure event_graph prediction: right deadline, wrong cascade calc."""
    item = _load_item("tt_item_002_bid_security_short")
    # Matches the actual Azure gpt-5.4-nano event_graph output (verified from JSONL)
    prediction = {
        "governing_clause_id": "ITB 19.3",
        "operative_deadline": "2026-06-14T10:00:00+03:00",
        "action_datetime": "2026-06-14T09:58:00+03:00",
        "required_bid_security_validity_through": "2026-11-06",  # wrong: should be 2026-11-09
        "submitted_bid_security_validity_through": "2026-11-06",
        "precondition_status": "satisfied",
        "verdict": "VALID",
        "failure_reason_code": "VALID",
        "citation": {
            "base_rule": [{"id": "ITB 18.1", "quote": "120 calendar days"}],
            "amendment_addendum": [{"id": "Addendum 2 §1", "quote": "extended to 14 June"}],
            "dependent_validity_period": [{"id": "ITB 19.3", "quote": "28 calendar days beyond"}],
        },
    }
    categories = [a["category"] for a in attribute_failure(item, prediction)]
    assert CASCADE_ARITHMETIC_ERROR in categories
    assert WRONG_VERDICT in categories
    assert WRONG_FAILURE_CODE in categories
    # Clause grounding passes (all keywords are in citation)
    assert CLAUSE_GROUNDING_FAILURE not in categories


def test_hero_002_via_grader_result() -> None:
    """grade_prediction result carries failure_attribution with CASCADE_ARITHMETIC_ERROR."""
    item = _load_item("tt_item_002_bid_security_short")
    prediction = {
        "governing_clause_id": "ITB 19.3",
        "operative_deadline": "2026-06-14T10:00:00+03:00",
        "required_bid_security_validity_through": "2026-11-06",
        "submitted_bid_security_validity_through": "2026-11-06",
        "precondition_status": "satisfied",
        "verdict": "VALID",
        "failure_reason_code": "VALID",
        "citation": {
            "base_rule": [{"id": "ITB 18.1"}],
            "amendment_addendum": [{"id": "Addendum 2 §1"}],
            "dependent_validity_period": [{"id": "ITB 19.3"}],
        },
    }
    result = grade_prediction(item, prediction=prediction)
    assert CASCADE_ARITHMETIC_ERROR in result["failure_attribution"]
    assert "failure_attribution" in result
    assert "attribution_detail" in result


# ── WRONG_CONTROLLING_DEADLINE (the trap) ───────────────────────────────────


def test_wrong_controlling_deadline_base_trap() -> None:
    item = _load_item("tt_item_002_bid_security_short")
    prediction = {
        "governing_clause_id": "Tender Data Sheet deadline",
        "operative_deadline": "2026-06-10T10:00:00+03:00",
        "required_bid_security_validity_through": "2026-11-05",
        "submitted_bid_security_validity_through": "2026-11-06",
        "precondition_status": "satisfied",
        "verdict": "VALID",
        "failure_reason_code": "VALID",
        "citation": {"rule": "Tender Data Sheet"},
    }
    categories = [a["category"] for a in attribute_failure(item, prediction)]
    assert WRONG_CONTROLLING_DEADLINE in categories
    assert CLAUSE_GROUNDING_FAILURE in categories  # missing ITB 19.3, ITB 18.1, Addendum 2


# ── WRONG_RULE_SELECTION (GAO (a)(1) vs (a)(2)) ─────────────────────────────


def test_wrong_rule_selection_gao_item_004() -> None:
    """Model uses (a)(2) when (a)(1) is required for apparent solicitation impropriety."""
    item = _load_item("tt_item_004_gao_solicitation_impropriety_late")
    prediction = {
        "governing_clause_id": "4 CFR §21.2(a)(2)",
        "operative_deadline": "2026-08-15T23:59:00-04:00",
        "action_datetime": "2026-07-21T09:00:00-04:00",
        "precondition_status": "unsatisfied",
        "verdict": "INVALID",
        "failure_reason_code": "MISSED_PROTEST_WINDOW",
        "citation": {"rule": "4 CFR §21.2(a)(2)"},
    }
    categories = [a["category"] for a in attribute_failure(item, prediction)]
    assert WRONG_RULE_SELECTION in categories


def test_no_wrong_rule_selection_when_correct() -> None:
    """Correct (a)(1) prediction does not trigger WRONG_RULE_SELECTION."""
    item = _load_item("tt_item_004_gao_solicitation_impropriety_late")
    perfect = item.expected_answer.model_dump()
    categories = [a["category"] for a in attribute_failure(item, perfect)]
    assert WRONG_RULE_SELECTION not in categories


# ── grader result backward compatibility ────────────────────────────────────


def test_item_005_end_of_day_artifact_is_clean_pass() -> None:
    """gpt-5.5 answered 23:59:59 where gold is 23:59:00 — now tolerated, no attribution."""
    item = _load_item("tt_item_005_gao_known_basis_timely")
    prediction = {
        "governing_clause_id": "4 CFR §21.2(a)(2)",
        "operative_deadline": "2026-08-15T23:59:59-04:00",  # gold is 23:59:00
        "action_datetime": "2026-08-14T15:30:00-04:00",
        "precondition_status": "satisfied",
        "verdict": "VALID",
        "failure_reason_code": "VALID",
        "citation": {"rule": "4 CFR §21.2(a)(2)"},
    }
    result = attribute_failure(item, prediction)
    assert result == [], f"Expected clean pass but got: {result}"


def test_wrong_operative_deadline_on_wrong_day() -> None:
    """Operative deadline on a genuinely wrong day → WRONG_OPERATIVE_DEADLINE."""
    item = _load_item("tt_item_005_gao_known_basis_timely")
    prediction = {
        "governing_clause_id": "4 CFR §21.2(a)(2)",
        "operative_deadline": "2026-08-20T23:59:00-04:00",  # gold 2026-08-15
        "verdict": "VALID",
        "failure_reason_code": "VALID",
        "citation": {"rule": "4 CFR §21.2(a)(2)"},
    }
    categories = [a["category"] for a in attribute_failure(item, prediction)]
    assert WRONG_OPERATIVE_DEADLINE in categories
    assert DEADLINE_PRECISION_MISMATCH not in categories


def test_deadline_precision_mismatch_same_day_non_eod() -> None:
    """Same day, different non-end-of-day time → DEADLINE_PRECISION_MISMATCH."""
    item = _load_item("tt_item_004_gao_solicitation_impropriety_late")
    prediction = {
        "governing_clause_id": "4 CFR §21.2(a)(1)",
        "operative_deadline": "2026-07-20T18:30:00-04:00",  # gold 17:00:00 same day
        "verdict": "INVALID",
        "failure_reason_code": "MISSED_PROTEST_WINDOW",
        "citation": {"rule": "4 CFR §21.2(a)(1)"},
    }
    categories = [a["category"] for a in attribute_failure(item, prediction)]
    assert DEADLINE_PRECISION_MISMATCH in categories
    assert WRONG_OPERATIVE_DEADLINE not in categories


def test_base_trap_is_controlling_not_operative_deadline() -> None:
    """The base-deadline trap stays WRONG_CONTROLLING_DEADLINE, not WRONG_OPERATIVE_DEADLINE."""
    item = _load_item("tt_item_002_bid_security_short")
    prediction = {
        "governing_clause_id": "ITB 19.3 read with ITB 18.1 and Addendum 2 §1",
        "operative_deadline": "2026-06-10T10:00:00+03:00",  # base, not addendum
        "verdict": "VALID",
        "failure_reason_code": "VALID",
        "citation": {"controlling_deadline": "ITB 19.3; ITB 18.1; Addendum 2"},
    }
    categories = [a["category"] for a in attribute_failure(item, prediction)]
    assert WRONG_CONTROLLING_DEADLINE in categories
    assert WRONG_OPERATIVE_DEADLINE not in categories  # not double-counted


def test_grader_parse_error_result_has_attribution() -> None:
    item = _load_item("tt_item_006_uganda_admin_review_late")
    result = grade_prediction(item, prediction=None, raw_output="The filing was late.")
    assert result["strict_score"] == 0
    assert "parse_error" in result["errors"]
    assert "failure_attribution" in result
    assert PARSE_ERROR in result["failure_attribution"]
    # diagnosis unchanged
    assert "Model output could not be parsed as JSON." in result["diagnosis"]
