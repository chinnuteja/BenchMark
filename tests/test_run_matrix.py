"""Tests for tender_timeline.run_matrix (matrix runner)."""

from __future__ import annotations

import json

import pytest

from tender_timeline.run_matrix import PROMPTS, model_slug


# ── model_slug ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("model", "expected_slug"),
    [
        ("gpt-5.5", "gpt55"),
        ("fake-v1", "fakev1"),
        ("claude-sonnet-4-6", "claudesonnet46"),
        ("gemini-3.5-flash", "gemini35flash"),
        ("UPPER-CASE-MODEL", "uppercasemodel"),
    ],
)
def test_model_slug(model: str, expected_slug: str) -> None:
    assert model_slug(model) == expected_slug


def test_model_slug_empty_falls_back() -> None:
    assert model_slug("---") == "model"


# ── PROMPTS constant ─────────────────────────────────────────────────────────


def test_prompts_list_contains_all_three() -> None:
    assert set(PROMPTS) == {"naive", "clause_first", "event_graph_first"}
    assert len(PROMPTS) == 3


# ── end-to-end matrix run with fake provider ─────────────────────────────────


def test_matrix_run_fake_provider_writes_three_jsonl_files(tmp_path) -> None:
    """Matrix runner writes one JSONL per prompt, each with 6 records (6 items)."""
    from tender_timeline.utils import repo_root
    from typer.testing import CliRunner
    from tender_timeline.run_matrix import app

    items_dir = repo_root() / "data" / "public_dev" / "items"
    prompts_dir = repo_root() / "baselines" / "prompts"

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "--provider", "fake",
            "--model", "fake-v1",
            "--items", str(items_dir),
            "--prompts-dir", str(prompts_dir),
            "--out-dir", str(tmp_path),
        ],
    )
    assert result.exit_code == 0, f"Matrix runner failed: {result.output}"

    for prompt in PROMPTS:
        out_file = tmp_path / f"fake_fakev1_{prompt}_outputs.jsonl"
        assert out_file.exists(), f"Missing: {out_file.name}"
        lines = [json.loads(ln) for ln in out_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 6, f"{prompt}: expected 6 records, got {len(lines)}"
        for record in lines:
            assert record["provider"] == "fake"
            assert record["prompt_name"] == prompt


def test_matrix_run_output_filenames_contain_model_slug(tmp_path) -> None:
    """Output filenames follow {provider}_{model_slug}_{prompt}_outputs.jsonl convention."""
    from typer.testing import CliRunner
    from tender_timeline.run_matrix import app
    from tender_timeline.utils import repo_root

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "--provider", "fake",
            "--model", "gpt-5.5",
            "--items", str(repo_root() / "data" / "public_dev" / "items"),
            "--prompts-dir", str(repo_root() / "baselines" / "prompts"),
            "--out-dir", str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    files = list(tmp_path.glob("*.jsonl"))
    assert any("gpt55" in f.name for f in files), f"No gpt55 slug in: {[f.name for f in files]}"
