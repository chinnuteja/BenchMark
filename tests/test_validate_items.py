"""Tests for benchmark item validation."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tender_timeline.schema import TenderTimelineItem
from tender_timeline.utils import repo_root

ITEMS_DIR = repo_root() / "data" / "public_dev" / "items"


def _load_item_files() -> list[Path]:
    return sorted(ITEMS_DIR.glob("*.json"))


def test_at_least_six_items_exist() -> None:
    item_files = _load_item_files()
    assert len(item_files) >= 6


@pytest.mark.parametrize("item_path", _load_item_files(), ids=lambda p: p.name)
def test_item_json_validates(item_path: Path) -> None:
    raw = json.loads(item_path.read_text(encoding="utf-8"))
    item = TenderTimelineItem.model_validate(raw)
    assert item.data_version == "public_dev_v0.1"
    assert item.grading.strict_fields == [
        "verdict",
        "failure_reason_code",
        "operative_deadline",
        "governing_clause_id",
    ]
    assert len(item.grading.required_clause_keywords) > 0


@pytest.mark.parametrize("item_path", _load_item_files(), ids=lambda p: p.name)
def test_referenced_documents_exist(item_path: Path) -> None:
    root = repo_root()
    raw = json.loads(item_path.read_text(encoding="utf-8"))
    item = TenderTimelineItem.model_validate(raw)
    for doc in item.documents:
        doc_path = root / doc.path
        assert doc_path.is_file(), f"Missing document: {doc.path}"


def test_invalid_item_json_fails_validation() -> None:
    with pytest.raises(ValidationError):
        TenderTimelineItem.model_validate(
            {
                "item_id": "bad_item",
                "family_id": "family_test",
                "jurisdiction": "test",
                "source_backbone": {},
                "documents": [],
                "task": {},
                "expected_answer": {
                    "governing_clause_id": "X",
                    "precondition_status": "unknown",
                    "verdict": "INVALID",
                    "failure_reason_code": "BOGUS_CODE",
                },
                "grading": {"strict_fields": ["verdict"]},
                "failure_modes": [],
                "trap": "test",
                "perturbation_certificate": {},
            }
        )
