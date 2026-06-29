"""Tests for tender_timeline.report."""

import json
from pathlib import Path

from tender_timeline.report import (
    _attribution_breakdown,
    _strongest_substantive_failure,
    generate_report,
)
from tender_timeline.utils import repo_root


def _write_grade_results(path: Path, label: str, strict_accuracy: float) -> None:
    payload = {
        "summary": {
            "num_items": 2,
            "strict_accuracy": strict_accuracy,
            "verdict_accuracy": 0.5,
            "failure_code_accuracy": 0.5,
            "clause_grounding_accuracy": 0.5,
            "parse_error_rate": 0.0,
        },
        "items": [
            {
                "item_id": f"{label}_item_a",
                "passed": strict_accuracy == 1.0,
                "errors": [] if strict_accuracy == 1.0 else ["wrong_clause_grounding"],
                "diagnosis": []
                if strict_accuracy == 1.0
                else ["Prediction did not ground answer in required controlling clause keywords."],
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_report_generator_writes_markdown(tmp_path: Path) -> None:
    grade_a = tmp_path / "fake_naive_grade_results.json"
    grade_b = tmp_path / "fake_clause_first_grade_results.json"
    _write_grade_results(grade_a, "naive", 0.3333)
    _write_grade_results(grade_b, "clause_first", 0.6667)

    output_path = tmp_path / "mini_eval_report.md"
    report_text = generate_report(
        grade_result_paths=[grade_a, grade_b],
        output_path=output_path,
        items_dir=repo_root() / "data" / "public_dev" / "items",
    )

    assert output_path.is_file()
    assert "| Baseline | Strict Accuracy |" in report_text
    assert "fake_naive" in report_text
    assert "Failure" in report_text
    assert "Prediction did not ground answer" in report_text
    # New metric columns and attribution section are present
    assert "Paired Consistency" in report_text
    assert "Right-Reason" in report_text
    assert "Failure-Attribution Breakdown" in report_text


def _grade_results_with_attribution(path: Path) -> None:
    """A real-model-style grade-results payload carrying oracle attribution."""
    payload = {
        "summary": {
            "num_items": 2,
            "strict_accuracy": 0.5,
            "verdict_accuracy": 0.5,
            "failure_code_accuracy": 0.5,
            "clause_grounding_accuracy": 1.0,
            "parse_error_rate": 0.0,
            "paired_consistency": 0.5,
            "right_reason_accuracy": 0.5,
        },
        "items": [
            {
                "item_id": "tt_item_002_bid_security_short",
                "passed": False,
                "errors": ["wrong_verdict"],
                "diagnosis": ["Verdict does not match expected procedural outcome."],
                "failure_attribution": ["CASCADE_ARITHMETIC_ERROR", "WRONG_VERDICT"],
                "attribution_detail": [
                    {
                        "category": "CASCADE_ARITHMETIC_ERROR",
                        "message": "Correct controlling deadline but miscalculated the bid-security cascade.",
                        "evidence": {
                            "predicted_required": "2026-11-06",
                            "computed_required": "2026-11-09",
                        },
                    },
                    {
                        "category": "WRONG_VERDICT",
                        "message": "Verdict does not match expected procedural outcome.",
                        "evidence": {"expected": "INVALID", "predicted": "VALID"},
                    },
                ],
            },
            {
                "item_id": "tt_item_003_valid_control",
                "passed": True,
                "errors": [],
                "diagnosis": [],
                "failure_attribution": [],
                "attribution_detail": [],
            },
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_real_model_report_surfaces_oracle_hero_failure(tmp_path: Path) -> None:
    grade = tmp_path / "azure_gpt54nano_event_graph_grade_results.json"
    _grade_results_with_attribution(grade)

    output_path = tmp_path / "real_model_eval_report.md"
    report_text = generate_report(
        grade_result_paths=[grade],
        output_path=output_path,
        items_dir=repo_root() / "data" / "public_dev" / "items",
        real_model=True,
    )

    # Hero failure is data-driven from attribution_detail, not hard-coded
    assert "Strongest Substantive Failure" in report_text
    assert "CASCADE_ARITHMETIC_ERROR" in report_text
    assert "2026-11-09" in report_text  # computed_required evidence
    assert "tt_item_002_bid_security_short" in report_text
    # Attribution breakdown counts the category
    assert "Failure-Attribution Breakdown" in report_text


def test_attribution_breakdown_counts_categories() -> None:
    items = [
        {"failure_attribution": ["CASCADE_ARITHMETIC_ERROR", "WRONG_VERDICT"]},
        {"failure_attribution": ["CASCADE_ARITHMETIC_ERROR"]},
        {"failure_attribution": []},
    ]
    breakdown = _attribution_breakdown(items)
    assert breakdown["CASCADE_ARITHMETIC_ERROR"] == 2
    assert breakdown["WRONG_VERDICT"] == 1


def test_strongest_substantive_failure_priority_order() -> None:
    """CASCADE_ARITHMETIC_ERROR outranks WRONG_RULE_SELECTION."""
    baselines = [
        {
            "label": "m_a",
            "payload": {
                "items": [
                    {
                        "item_id": "i_rule",
                        "attribution_detail": [
                            {"category": "WRONG_RULE_SELECTION", "message": "rule", "evidence": {}}
                        ],
                    },
                    {
                        "item_id": "i_cascade",
                        "attribution_detail": [
                            {
                                "category": "CASCADE_ARITHMETIC_ERROR",
                                "message": "cascade",
                                "evidence": {"computed_required": "2026-11-09"},
                            }
                        ],
                    },
                ]
            },
        }
    ]
    result = _strongest_substantive_failure(baselines)
    assert result is not None
    assert "CASCADE_ARITHMETIC_ERROR" in result
    assert "i_cascade" in result


def test_strongest_substantive_failure_none_when_clean() -> None:
    baselines = [{"label": "m", "payload": {"items": [{"item_id": "i", "attribution_detail": []}]}}]
    assert _strongest_substantive_failure(baselines) is None
