"""Tests for tender_timeline.aggregate (leaderboard builder)."""

from __future__ import annotations

import json

import pytest

from tender_timeline.aggregate import build_leaderboard, parse_label, render_markdown


# ── parse_label ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("label", "expected_model", "expected_prompt"),
    [
        ("azure_gpt54nano_event_graph", "azure_gpt54nano", "event_graph"),
        ("azure_gpt54nano_event_graph_first", "azure_gpt54nano", "event_graph_first"),
        ("azure_gpt54nano_clause_first", "azure_gpt54nano", "clause_first"),
        ("azure_gpt54nano_naive", "azure_gpt54nano", "naive"),
        ("fake_clause_first", "fake", "clause_first"),
        ("openai_gpt55_naive", "openai_gpt55", "naive"),
        ("anthropic_sonnet46_event_graph_first", "anthropic_sonnet46", "event_graph_first"),
        # Longest suffix wins: event_graph_first over event_graph
        ("mymodel_event_graph_first", "mymodel", "event_graph_first"),
    ],
)
def test_parse_label(label: str, expected_model: str, expected_prompt: str) -> None:
    model, prompt = parse_label(label)
    assert model == expected_model
    assert prompt == expected_prompt


def test_parse_label_unknown_prompt() -> None:
    model, prompt = parse_label("somemodel_unknownprompt")
    assert prompt == "unknown"


def test_parse_label_bare_prompt_name() -> None:
    model, prompt = parse_label("naive")
    assert model == "unknown"
    assert prompt == "naive"


# ── build_leaderboard + render_markdown ──────────────────────────────────────


def test_build_leaderboard_two_files(tmp_path) -> None:
    data1 = {
        "summary": {
            "strict_accuracy": 0.5,
            "verdict_accuracy": 1.0,
            "clause_grounding_accuracy": 0.8333,
            "paired_consistency": 1.0,
            "right_reason_accuracy": 0.3333,
            "parse_error_rate": 0.0,
        }
    }
    data2 = {
        "summary": {
            "strict_accuracy": 0.8333,
            "verdict_accuracy": 1.0,
            "clause_grounding_accuracy": 1.0,
            "paired_consistency": 1.0,
            "right_reason_accuracy": 0.8333,
            "parse_error_rate": 0.0,
        }
    }
    (tmp_path / "fake_naive_grade_results.json").write_text(json.dumps(data1), encoding="utf-8")
    (tmp_path / "fake_event_graph_first_grade_results.json").write_text(json.dumps(data2), encoding="utf-8")

    lb = build_leaderboard(tmp_path)
    assert len(lb["rows"]) == 2
    models = {r["model"] for r in lb["rows"]}
    prompts = {r["prompt"] for r in lb["rows"]}
    assert models == {"fake"}
    assert prompts == {"naive", "event_graph_first"}


def test_render_markdown_has_header_and_rows(tmp_path) -> None:
    data = {
        "summary": {
            "strict_accuracy": 0.5,
            "verdict_accuracy": 1.0,
            "clause_grounding_accuracy": 1.0,
            "paired_consistency": 0.5,
            "right_reason_accuracy": 0.3333,
            "parse_error_rate": 0.0,
        }
    }
    (tmp_path / "azure_gpt54nano_naive_grade_results.json").write_text(json.dumps(data), encoding="utf-8")
    lb = build_leaderboard(tmp_path)
    md = render_markdown(lb)
    assert "# TENDER-TIMELINE Leaderboard" in md
    assert "| Model | Prompt |" in md
    assert "azure_gpt54nano" in md
    assert "naive" in md
    assert "0.5000" in md


def test_render_markdown_none_values_show_na(tmp_path) -> None:
    """Grade results without paired_consistency should render as n/a."""
    data = {"summary": {"strict_accuracy": 0.5, "verdict_accuracy": 1.0, "clause_grounding_accuracy": 1.0, "parse_error_rate": 0.0}}
    (tmp_path / "model_naive_grade_results.json").write_text(json.dumps(data), encoding="utf-8")
    lb = build_leaderboard(tmp_path)
    md = render_markdown(lb)
    assert "n/a" in md


def test_build_leaderboard_empty_dir(tmp_path) -> None:
    lb = build_leaderboard(tmp_path)
    assert lb["rows"] == []
