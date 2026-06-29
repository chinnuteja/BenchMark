"""Failure attribution: localize which procedural reasoning step a prediction got wrong."""

from __future__ import annotations

from typing import Any

from tender_timeline.calculator import CalculatorError, compute_expected
from tender_timeline.citation_check import has_required_clause_keywords
from tender_timeline.normalize import date_or_datetime_equal, normalize_enum, parse_datetime

# Attribution category codes (stable identifiers used in metrics/reports).
WRONG_CONTROLLING_DEADLINE = "WRONG_CONTROLLING_DEADLINE"
CASCADE_ARITHMETIC_ERROR = "CASCADE_ARITHMETIC_ERROR"
WRONG_RULE_SELECTION = "WRONG_RULE_SELECTION"
WRONG_OPERATIVE_DEADLINE = "WRONG_OPERATIVE_DEADLINE"
DEADLINE_PRECISION_MISMATCH = "DEADLINE_PRECISION_MISMATCH"
CLAUSE_GROUNDING_FAILURE = "CLAUSE_GROUNDING_FAILURE"
WRONG_VERDICT = "WRONG_VERDICT"
WRONG_FAILURE_CODE = "WRONG_FAILURE_CODE"
PARSE_ERROR = "PARSE_ERROR"


def _same_local_date(a: str | None, b: str | None) -> bool:
    da, db = parse_datetime(a), parse_datetime(b)
    if da is None or db is None:
        return False
    return da.date() == db.date()


def attribute_failure(item: Any, prediction: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return a list of {category, message, evidence} entries describing the failure(s).

    An empty list means no detectable failure. Safe for items without a compute_spec
    (it simply skips oracle-based categories).
    """
    if prediction is None:
        return [
            {
                "category": PARSE_ERROR,
                "message": "Model output could not be parsed as JSON.",
                "evidence": {},
            }
        ]

    out: list[dict[str, Any]] = []
    exp = item.expected_answer
    spec = item.compute_spec.model_dump() if item.compute_spec is not None else None
    computed = None
    if item.compute_spec is not None:
        try:
            computed = compute_expected(item)
        except CalculatorError:
            computed = None

    pred_op = prediction.get("operative_deadline")

    # WRONG_CONTROLLING_DEADLINE — used base instead of addendum (cascade rule only)
    if spec and spec.get("rule_type") == "bid_security_cascade":
        base = spec.get("base_deadline")
        add = spec.get("addendum_deadline")
        if (
            add
            and pred_op
            and date_or_datetime_equal(pred_op, base)
            and not date_or_datetime_equal(pred_op, add)
        ):
            out.append(
                {
                    "category": WRONG_CONTROLLING_DEADLINE,
                    "message": "Used base deadline instead of the controlling addendum deadline.",
                    "evidence": {"predicted": pred_op, "addendum": add, "base": base},
                }
            )

    # CASCADE_ARITHMETIC_ERROR — operative deadline correct but required-through wrong
    if (
        computed
        and computed.required_bid_security_validity_through
        and pred_op
        and date_or_datetime_equal(pred_op, exp.operative_deadline)
    ):
        pred_req = prediction.get("required_bid_security_validity_through")
        if pred_req and not date_or_datetime_equal(
            pred_req, computed.required_bid_security_validity_through
        ):
            out.append(
                {
                    "category": CASCADE_ARITHMETIC_ERROR,
                    "message": "Correct controlling deadline but miscalculated the bid-security cascade.",
                    "evidence": {
                        "predicted_required": pred_req,
                        "computed_required": computed.required_bid_security_validity_through,
                    },
                }
            )

    # WRONG_RULE_SELECTION — GAO (a)(1) vs (a)(2) mismatch
    if spec and spec.get("rule_type") == "protest_window":
        exp_clause = exp.governing_clause_id or ""
        pred_clause = str(prediction.get("governing_clause_id") or "")
        if ("(a)(1)" in exp_clause and "(a)(2)" in pred_clause) or (
            "(a)(2)" in exp_clause and "(a)(1)" in pred_clause
        ):
            out.append(
                {
                    "category": WRONG_RULE_SELECTION,
                    "message": "Applied the wrong protest-timeliness subsection.",
                    "evidence": {
                        "expected_clause": exp_clause,
                        "predicted_clause": pred_clause,
                    },
                }
            )

    # Operative-deadline mismatch not already explained as a controlling-deadline error.
    # (date_or_datetime_equal tolerates end-of-day 23:59:00 vs 23:59:59.)
    exp_op = exp.operative_deadline
    has_controlling = any(e["category"] == WRONG_CONTROLLING_DEADLINE for e in out)
    if exp_op and pred_op and not has_controlling and not date_or_datetime_equal(exp_op, pred_op):
        if _same_local_date(exp_op, pred_op):
            out.append(
                {
                    "category": DEADLINE_PRECISION_MISMATCH,
                    "message": "Operative deadline has the right date but a different time-of-day.",
                    "evidence": {"expected": exp_op, "predicted": pred_op},
                }
            )
        else:
            out.append(
                {
                    "category": WRONG_OPERATIVE_DEADLINE,
                    "message": "Operative deadline does not match the controlling deadline.",
                    "evidence": {"expected": exp_op, "predicted": pred_op},
                }
            )

    # CLAUSE_GROUNDING_FAILURE
    ok, missing = has_required_clause_keywords(prediction, item.grading.required_clause_keywords)
    if not ok:
        out.append(
            {
                "category": CLAUSE_GROUNDING_FAILURE,
                "message": "Answer not grounded in required controlling clause keywords.",
                "evidence": {"missing_keywords": missing},
            }
        )

    # WRONG_VERDICT / WRONG_FAILURE_CODE (fallbacks, always last)
    if normalize_enum(prediction.get("verdict")) != normalize_enum(exp.verdict):
        out.append(
            {
                "category": WRONG_VERDICT,
                "message": "Verdict does not match expected procedural outcome.",
                "evidence": {
                    "expected": exp.verdict,
                    "predicted": prediction.get("verdict"),
                },
            }
        )
    if normalize_enum(prediction.get("failure_reason_code")) != normalize_enum(exp.failure_reason_code):
        out.append(
            {
                "category": WRONG_FAILURE_CODE,
                "message": "Failure reason code does not match expected classification.",
                "evidence": {
                    "expected": exp.failure_reason_code,
                    "predicted": prediction.get("failure_reason_code"),
                },
            }
        )
    return out
