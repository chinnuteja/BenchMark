"""Tests for tender_timeline.run_model and providers."""

import json
from pathlib import Path

from tender_timeline.providers import call_model
from tender_timeline.run_model import run_items
from tender_timeline.utils import repo_root


def test_fake_provider_returns_outputs() -> None:
    result = call_model(
        provider="fake",
        model="fake-v1",
        prompt="ignored",
        item_id="tt_item_001_late_submission",
        prompt_name="naive",
    )
    assert "raw_output" in result
    assert result["latency_ms"] == 0
    assert result["usage"]["provider_label"] == "fake/sample"


def test_run_model_writes_jsonl(tmp_path: Path) -> None:
    root = repo_root()
    output_path = tmp_path / "fake_naive_outputs.jsonl"
    run_items(
        provider="fake",
        model="fake-v1",
        prompt_path=root / "baselines" / "prompts" / "naive.md",
        items_dir=root / "data" / "public_dev" / "items",
        output_path=output_path,
        limit=2,
    )

    lines = output_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2

    for line in lines:
        record = json.loads(line)
        assert record["item_id"]
        assert record["provider"] == "fake"
        assert record["model"] == "fake-v1"
        assert record["prompt_name"] == "naive"
        assert "raw_output" in record
        assert record.get("is_fake_sample_output") is True
        assert ("parsed_prediction" in record and record["parsed_prediction"] is not None) or record.get(
            "parse_error"
        )
