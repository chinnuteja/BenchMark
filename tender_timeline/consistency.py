"""Shortcut / consistency metrics for TENDER-TIMELINE grade results.

paired_consistency: across matched contrast groups (an INVALID item and its VALID
control), a group only "passes" if the model gets the verdict right on BOTH members.
This penalizes models that pattern-match a family to one verdict (e.g. always INVALID).

right_reason_rate: fraction of items that pass strict scoring AND show no
construct-relevant failure attribution (cascade error, wrong rule, wrong controlling
deadline, clause-grounding failure) — i.e. "right answer for the right reason".
"""

from __future__ import annotations

from typing import Any

RIGHT_REASON_BLOCKERS = {
    "CASCADE_ARITHMETIC_ERROR",
    "WRONG_RULE_SELECTION",
    "WRONG_CONTROLLING_DEADLINE",
    "WRONG_OPERATIVE_DEADLINE",
    "CLAUSE_GROUNDING_FAILURE",
}


def paired_consistency(item_results: list[dict[str, Any]]) -> float | None:
    """Fraction of contrast groups where every member has verdict_score == 1.

    Returns None when there are no contrast groups in the results.
    """
    groups: dict[str, list[dict[str, Any]]] = {}
    for r in item_results:
        g = r.get("contrast_group")
        if g:
            groups.setdefault(g, []).append(r)
    if not groups:
        return None
    passed = sum(
        1
        for members in groups.values()
        if all(m.get("verdict_score", 0) == 1 for m in members)
    )
    return round(passed / len(groups), 4)


def right_reason_rate(item_results: list[dict[str, Any]]) -> float:
    """Fraction of items that pass strict AND have no construct-relevant failure attribution."""
    if not item_results:
        return 0.0
    good = 0
    for r in item_results:
        attrib = set(r.get("failure_attribution", []))
        if r.get("strict_score") == 1 and not (attrib & RIGHT_REASON_BLOCKERS):
            good += 1
    return round(good / len(item_results), 4)
