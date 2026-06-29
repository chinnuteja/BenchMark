"""Deterministic grader for TENDER-TIMELINE predictions."""

from __future__ import annotations

from typing import Any

from tender_timeline.attribution import attribute_failure
from tender_timeline.citation_check import has_required_clause_keywords
from tender_timeline.normalize import date_or_datetime_equal, normalize_enum, normalize_string
from tender_timeline.schema import TenderTimelineItem
from tender_timeline.utils import extract_json_from_text


def _prediction_value(prediction: dict[str, Any] | None, field: str) -> Any:
    if prediction is None:
        return None
    return prediction.get(field)


def _compare_strict_field(
    field: str,
    expected: Any,
    predicted: Any,
    prediction: dict[str, Any],
    required_keywords: list[str],
) -> tuple[bool, dict[str, Any]]:
    if field == "verdict":
        passed = normalize_enum(expected) == normalize_enum(predicted)
        return passed, {
            "expected": normalize_enum(expected),
            "predicted": normalize_enum(predicted),
            "passed": passed,
        }

    if field == "failure_reason_code":
        passed = normalize_enum(expected) == normalize_enum(predicted)
        return passed, {
            "expected": normalize_enum(expected),
            "predicted": normalize_enum(predicted),
            "passed": passed,
        }

    if field == "operative_deadline":
        passed = date_or_datetime_equal(expected, predicted)
        return passed, {
            "expected": expected,
            "predicted": predicted,
            "passed": passed,
        }

    if field == "governing_clause_id":
        passed, missing = has_required_clause_keywords(prediction, required_keywords)
        return passed, {
            "expected": expected,
            "predicted": predicted,
            "expected_contains": required_keywords,
            "missing_keywords": missing,
            "passed": passed,
        }

    passed = normalize_string(expected) == normalize_string(predicted)
    return passed, {
        "expected": expected,
        "predicted": predicted,
        "passed": passed,
    }


def _build_diagnosis(
    item: TenderTimelineItem,
    prediction: dict[str, Any] | None,
    parse_error: str | None,
    clause_grounding_passed: bool,
    field_results: dict[str, dict[str, Any]],
) -> list[str]:
    diagnoses: list[str] = []

    if parse_error:
        diagnoses.append("Model output could not be parsed as JSON.")
        return diagnoses

    if prediction is None:
        diagnoses.append("Model output could not be parsed as JSON.")
        return diagnoses

    expected_deadline = item.expected_answer.operative_deadline or ""
    predicted_deadline = str(prediction.get("operative_deadline") or "")
    if "2026-06-14" in expected_deadline and "2026-06-10" in predicted_deadline:
        diagnoses.append(
            "Used base Tender Data Sheet deadline instead of Addendum 2 extended deadline."
        )

    expected_clause = item.expected_answer.governing_clause_id or ""
    predicted_clause = str(prediction.get("governing_clause_id") or "")
    if "4 CFR §21.2(a)(1)" in expected_clause and "(a)(2)" in predicted_clause:
        diagnoses.append(
            "Used 10-day known-basis rule instead of apparent solicitation impropriety deadline rule."
        )

    if not clause_grounding_passed:
        diagnoses.append(
            "Prediction did not ground answer in required controlling clause keywords."
        )

    verdict_result = field_results.get("verdict")
    if verdict_result and not verdict_result.get("passed", True):
        diagnoses.append("Verdict does not match expected procedural outcome.")

    failure_result = field_results.get("failure_reason_code")
    if failure_result and not failure_result.get("passed", True):
        diagnoses.append("Failure reason code does not match expected classification.")

    deadline_result = field_results.get("operative_deadline")
    if deadline_result and not deadline_result.get("passed", True):
        diagnoses.append("Operative deadline does not match expected controlling deadline.")

    return diagnoses


def grade_prediction(
    item: TenderTimelineItem,
    prediction: dict[str, Any] | None,
    raw_output: str | None = None,
) -> dict[str, Any]:
    """Grade a single model prediction against an item's expected answer."""
    parse_error: str | None = None
    if prediction is None and raw_output:
        prediction, parse_error = extract_json_from_text(raw_output)

    required_keywords = item.grading.required_clause_keywords
    expected = item.expected_answer

    if prediction is None:
        attr = attribute_failure(item, None)
        return {
            "item_id": item.item_id,
            "family_id": item.family_id,
            "passed": False,
            "strict_score": 0,
            "verdict_score": 0,
            "failure_code_score": 0,
            "clause_grounding_score": 0,
            "date_score": 0,
            "field_results": {},
            "errors": ["parse_error"],
            "diagnosis": ["Model output could not be parsed as JSON."],
            "parse_error": parse_error,
            "failure_attribution": [a["category"] for a in attr],
            "attribution_detail": attr,
        }

    field_results: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    strict_fields_passed = True

    for field in item.grading.strict_fields:
        expected_value = getattr(expected, field, None)
        predicted_value = _prediction_value(prediction, field)
        passed, result = _compare_strict_field(
            field,
            expected_value,
            predicted_value,
            prediction,
            required_keywords,
        )
        field_results[field] = result
        if not passed:
            strict_fields_passed = False
            if field == "governing_clause_id":
                errors.append("wrong_governing_clause_id")
            else:
                errors.append(f"wrong_{field}")

    verdict_score = (
        1
        if normalize_enum(expected.verdict) == normalize_enum(prediction.get("verdict"))
        else 0
    )
    if verdict_score == 0:
        if "wrong_verdict" not in errors:
            errors.append("wrong_verdict")

    failure_code_score = (
        1
        if normalize_enum(expected.failure_reason_code)
        == normalize_enum(prediction.get("failure_reason_code"))
        else 0
    )
    if failure_code_score == 0:
        if "wrong_failure_reason_code" not in errors:
            errors.append("wrong_failure_reason_code")

    clause_grounding_passed, missing_keywords = has_required_clause_keywords(
        prediction,
        required_keywords,
    )
    clause_grounding_score = 1 if clause_grounding_passed else 0
    if not clause_grounding_passed:
        errors.append("wrong_clause_grounding")
        for keyword in missing_keywords:
            errors.append(f"missing_required_clause:{keyword}")

    date_fields = item.grading.date_fields
    if date_fields:
        date_passes = 0
        for field in date_fields:
            expected_value = getattr(expected, field, None)
            predicted_value = _prediction_value(prediction, field)
            if date_or_datetime_equal(expected_value, predicted_value):
                date_passes += 1
        date_score = date_passes / len(date_fields)
    else:
        date_score = 1.0

    strict_score = 1 if strict_fields_passed and clause_grounding_passed else 0
    if item.grading.clause_grounding_required and not clause_grounding_passed:
        strict_score = 0

    diagnosis = _build_diagnosis(
        item,
        prediction,
        parse_error,
        clause_grounding_passed,
        field_results,
    )

    attribution = attribute_failure(item, prediction)

    return {
        "item_id": item.item_id,
        "family_id": item.family_id,
        "passed": strict_score == 1,
        "strict_score": strict_score,
        "verdict_score": verdict_score,
        "failure_code_score": failure_code_score,
        "clause_grounding_score": clause_grounding_score,
        "date_score": date_score,
        "field_results": field_results,
        "errors": errors,
        "diagnosis": diagnosis,
        "failure_attribution": [a["category"] for a in attribution],
        "attribution_detail": attribution,
    }
