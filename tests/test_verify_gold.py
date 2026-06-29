"""Tests for the verify_gold gate in validate_items."""

from __future__ import annotations

import copy
import json

import pytest

from tender_timeline.schema import TenderTimelineItem
from tender_timeline.utils import repo_root
from tender_timeline.validate_items import verify_gold

ITEMS_DIR = repo_root() / "data" / "public_dev" / "items"

ALL_ITEM_IDS = [
    "tt_item_001_late_submission",
    "tt_item_002_bid_security_short",
    "tt_item_003_valid_control",
    "tt_item_004_gao_solicitation_impropriety_late",
    "tt_item_005_gao_known_basis_timely",
    "tt_item_006_uganda_admin_review_late",
]


def _load_item(item_id: str) -> TenderTimelineItem:
    path = ITEMS_DIR / f"{item_id}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return TenderTimelineItem.model_validate(raw)


@pytest.mark.parametrize("item_id", ALL_ITEM_IDS)
def test_all_items_gold_matches_oracle(item_id: str) -> None:
    """Oracle-computed answer must equal the authored expected_answer for every item."""
    item = _load_item(item_id)
    ok, messages = verify_gold(item)
    assert ok, f"Gold mismatch for {item_id}: {messages}"


def test_verify_gold_skips_items_without_compute_spec() -> None:
    """Items without compute_spec must return (True, ['no compute_spec (skipped)'])."""
    item = _load_item("tt_item_001_late_submission")
    item_dict = item.model_dump()
    item_dict["compute_spec"] = None
    item_no_spec = TenderTimelineItem.model_validate(item_dict)
    ok, messages = verify_gold(item_no_spec)
    assert ok
    assert messages == ["no compute_spec (skipped)"]


def test_verify_gold_fails_on_corrupted_required_through() -> None:
    """Deliberately wrong required_bid_security_validity_through triggers mismatch."""
    raw = json.loads((ITEMS_DIR / "tt_item_002_bid_security_short.json").read_text(encoding="utf-8"))
    bad = copy.deepcopy(raw)
    bad["expected_answer"]["required_bid_security_validity_through"] = "2026-11-08"
    item_bad = TenderTimelineItem.model_validate(bad)
    ok, messages = verify_gold(item_bad)
    assert not ok
    assert any("required_bid_security_validity_through" in m for m in messages)
    assert any("2026-11-08" in m for m in messages)
    assert any("2026-11-09" in m for m in messages)


def test_verify_gold_fails_on_wrong_verdict() -> None:
    """Wrong verdict in authored expected_answer is caught."""
    raw = json.loads((ITEMS_DIR / "tt_item_001_late_submission.json").read_text(encoding="utf-8"))
    bad = copy.deepcopy(raw)
    bad["expected_answer"]["verdict"] = "VALID"
    bad["expected_answer"]["failure_reason_code"] = "VALID"
    item_bad = TenderTimelineItem.model_validate(bad)
    ok, messages = verify_gold(item_bad)
    assert not ok
    assert any("verdict" in m for m in messages)
