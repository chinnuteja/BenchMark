"""Deterministic procedural oracle for TENDER-TIMELINE.

Computes operative deadlines, dependent validity cascades, and verdicts directly from
rule parameters + demo calendars, so gold answers are derived rather than hand-authored.
Pure and offline: no API calls, no randomness.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from typing import Any

from tender_timeline.normalize import parse_datetime
from tender_timeline.utils import repo_root

CALENDARS_DIR = "data/public_dev/calendars"


class CalculatorError(ValueError):
    """Raised when a compute_spec cannot be evaluated."""


@dataclass
class ComputedAnswer:
    operative_deadline: str | None = None
    controlling_basis: str | None = None
    bid_validity_end: str | None = None
    required_bid_security_validity_through: str | None = None
    verdict: str | None = None
    failure_reason_code: str | None = None
    governing_clause_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_calendar(calendar_id: str) -> dict[str, Any]:
    path = repo_root() / CALENDARS_DIR / f"{calendar_id}.json"
    if not path.is_file():
        raise CalculatorError(f"calendar not found: {calendar_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def _date_of(value: str | None) -> date:
    if value is None:
        raise CalculatorError("expected a date value, got None")
    dt = parse_datetime(value)
    if dt is not None:
        return dt.date()
    return date.fromisoformat(str(value).strip()[:10])


def _end_of_day(d: date, tz_offset: str | None, time_str: str = "23:59:00") -> str:
    if not tz_offset:
        raise CalculatorError("deadline_tz_offset is required for window-based deadlines")
    return f"{d.isoformat()}T{time_str}{tz_offset}"


def _later(a: str | None, b: str | None) -> bool:
    """True if datetime a is strictly after datetime b (timezone-aware)."""
    da, db = parse_datetime(a), parse_datetime(b)
    if da is None or db is None:
        return False
    return da > db


def compute_bid_security_cascade(spec: dict[str, Any], action_log: dict[str, Any]) -> ComputedAnswer:
    base = spec.get("base_deadline")
    addendum = spec.get("addendum_deadline")
    operative = addendum or base
    ca = ComputedAnswer(
        operative_deadline=operative,
        controlling_basis="addendum" if addendum else "base",
        governing_clause_id=spec.get("governing_clause_id"),
    )

    submission = action_log.get("submission_datetime")
    if submission is not None and _later(submission, operative):
        ca.verdict = "INVALID"
        ca.failure_reason_code = "LATE_SUBMISSION"
        return ca

    submitted = action_log.get("bid_security_valid_through")
    validity_days = spec.get("bid_validity_days")
    extra_days = spec.get("bid_security_extra_days")
    if submitted is not None and validity_days is not None and extra_days is not None:
        validity_end = _date_of(operative) + timedelta(days=int(validity_days))
        required = validity_end + timedelta(days=int(extra_days))
        ca.bid_validity_end = validity_end.isoformat()
        ca.required_bid_security_validity_through = required.isoformat()
        if _date_of(submitted) < required:
            ca.verdict = "INVALID"
            ca.failure_reason_code = "INSUFFICIENT_BID_SECURITY_VALIDITY"
            return ca

    ca.verdict = "VALID"
    ca.failure_reason_code = "VALID"
    return ca


def compute_protest_window(spec: dict[str, Any], action_log: dict[str, Any]) -> ComputedAnswer:
    subtype = spec.get("protest_subtype")
    ca = ComputedAnswer(governing_clause_id=spec.get("governing_clause_id"))

    if subtype == "apparent_solicitation_impropriety":
        ca.operative_deadline = spec.get("proposal_deadline")
        ca.controlling_basis = "proposal_deadline"
    elif subtype == "known_basis":
        days = int(spec.get("known_basis_window_days", 10))
        op_date = _date_of(action_log.get("basis_known_date")) + timedelta(days=days)
        ca.operative_deadline = _end_of_day(
            op_date, spec.get("deadline_tz_offset"), spec.get("deadline_end_of_day_time", "23:59:00")
        )
        ca.controlling_basis = "known_basis_plus_window"
    else:
        raise CalculatorError(f"unknown protest_subtype: {subtype!r}")

    if _later(action_log.get("protest_filed"), ca.operative_deadline):
        ca.verdict = "INVALID"
        ca.failure_reason_code = "MISSED_PROTEST_WINDOW"
    else:
        ca.verdict = "VALID"
        ca.failure_reason_code = "VALID"
    return ca


def compute_admin_review_window(spec: dict[str, Any], action_log: dict[str, Any]) -> ComputedAnswer:
    days = int(spec.get("window_days", 10))
    op_date = _date_of(action_log.get("decision_received")) + timedelta(days=days)
    operative = _end_of_day(
        op_date, spec.get("deadline_tz_offset"), spec.get("deadline_end_of_day_time", "23:59:00")
    )
    ca = ComputedAnswer(
        operative_deadline=operative,
        controlling_basis="receipt_plus_window",
        governing_clause_id=spec.get("governing_clause_id"),
    )
    if _later(action_log.get("review_filed"), operative):
        ca.verdict = "INVALID"
        ca.failure_reason_code = "MISSED_PROTEST_WINDOW"
    else:
        ca.verdict = "VALID"
        ca.failure_reason_code = "VALID"
    return ca


_DISPATCH = {
    "bid_security_cascade": compute_bid_security_cascade,
    "protest_window": compute_protest_window,
    "admin_review_window": compute_admin_review_window,
}


def compute_from_spec(spec: dict[str, Any], action_log: dict[str, Any]) -> ComputedAnswer:
    """Compute the oracle answer from a plain compute_spec dict + action_log dict."""
    rule = spec.get("rule_type")
    fn = _DISPATCH.get(rule)
    if fn is None:
        raise CalculatorError(f"unknown rule_type: {rule!r}")
    return fn(spec, action_log)


def compute_expected(item: Any) -> ComputedAnswer:
    """Compute the oracle answer for a TenderTimelineItem (must have a compute_spec)."""
    if getattr(item, "compute_spec", None) is None:
        raise CalculatorError(f"item {item.item_id} has no compute_spec")
    spec = item.compute_spec.model_dump()
    action_log = (item.task or {}).get("action_log", {})
    return compute_from_spec(spec, action_log)
