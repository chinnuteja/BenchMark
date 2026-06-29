"""Tests for tender_timeline.consistency metrics."""

from __future__ import annotations

from tender_timeline.consistency import (
    RIGHT_REASON_BLOCKERS,
    paired_consistency,
    right_reason_rate,
)


def _result(
    item_id: str,
    verdict_score: int,
    strict_score: int = 1,
    contrast_group: str | None = None,
    failure_attribution: list[str] | None = None,
) -> dict:
    return {
        "item_id": item_id,
        "verdict_score": verdict_score,
        "strict_score": strict_score,
        "contrast_group": contrast_group,
        "failure_attribution": failure_attribution or [],
    }


# ── paired_consistency ───────────────────────────────────────────────────────


def test_paired_consistency_both_correct() -> None:
    results = [
        _result("item_a_invalid", verdict_score=1, contrast_group="group_1"),
        _result("item_a_valid", verdict_score=1, contrast_group="group_1"),
    ]
    assert paired_consistency(results) == 1.0


def test_paired_consistency_one_wrong() -> None:
    results = [
        _result("item_a_invalid", verdict_score=1, contrast_group="group_1"),
        _result("item_a_valid", verdict_score=0, contrast_group="group_1"),
    ]
    assert paired_consistency(results) == 0.0


def test_paired_consistency_two_groups_half_pass() -> None:
    results = [
        _result("g1_a", verdict_score=1, contrast_group="group_1"),
        _result("g1_b", verdict_score=1, contrast_group="group_1"),
        _result("g2_a", verdict_score=1, contrast_group="group_2"),
        _result("g2_b", verdict_score=0, contrast_group="group_2"),
    ]
    assert paired_consistency(results) == 0.5


def test_paired_consistency_no_groups_returns_none() -> None:
    results = [
        _result("item_x", verdict_score=1),
        _result("item_y", verdict_score=0),
    ]
    assert paired_consistency(results) is None


def test_paired_consistency_always_invalid_pattern() -> None:
    """A model that always predicts INVALID will fail the VALID control member."""
    results = [
        _result("invalid_item", verdict_score=1, contrast_group="grp"),
        _result("valid_control", verdict_score=0, contrast_group="grp"),  # wrong: predicted INVALID
    ]
    assert paired_consistency(results) == 0.0


def test_paired_consistency_mixed_groups_and_ungrouped() -> None:
    """Ungrouped items are ignored; grouped items are scored."""
    results = [
        _result("ungrouped", verdict_score=1),
        _result("g1_a", verdict_score=1, contrast_group="g1"),
        _result("g1_b", verdict_score=1, contrast_group="g1"),
    ]
    assert paired_consistency(results) == 1.0


# ── right_reason_rate ────────────────────────────────────────────────────────


def test_right_reason_rate_clean_pass() -> None:
    results = [_result("i1", verdict_score=1, strict_score=1, failure_attribution=[])]
    assert right_reason_rate(results) == 1.0


def test_right_reason_rate_cascade_error_blocks() -> None:
    """strict=1 but CASCADE_ARITHMETIC_ERROR → does not count as right-reason."""
    results = [
        _result("i1", verdict_score=1, strict_score=1, failure_attribution=["CASCADE_ARITHMETIC_ERROR"]),
    ]
    assert right_reason_rate(results) == 0.0


def test_right_reason_rate_wrong_verdict_blocks() -> None:
    results = [_result("i1", verdict_score=0, strict_score=0, failure_attribution=[])]
    assert right_reason_rate(results) == 0.0


def test_right_reason_rate_mixed() -> None:
    results = [
        _result("clean", verdict_score=1, strict_score=1, failure_attribution=[]),
        _result("cascade_err", verdict_score=1, strict_score=1, failure_attribution=["CASCADE_ARITHMETIC_ERROR"]),
        _result("wrong_rule", verdict_score=0, strict_score=0, failure_attribution=["WRONG_RULE_SELECTION"]),
    ]
    # Only "clean" qualifies
    assert right_reason_rate(results) == round(1 / 3, 4)


def test_right_reason_rate_empty_list() -> None:
    assert right_reason_rate([]) == 0.0


def test_right_reason_blockers_set_contents() -> None:
    expected = {
        "CASCADE_ARITHMETIC_ERROR",
        "WRONG_RULE_SELECTION",
        "WRONG_CONTROLLING_DEADLINE",
        "WRONG_OPERATIVE_DEADLINE",
        "CLAUSE_GROUNDING_FAILURE",
    }
    assert RIGHT_REASON_BLOCKERS == expected
