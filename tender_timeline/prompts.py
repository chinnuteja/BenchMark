"""Prompt construction for TENDER-TIMELINE model runs."""

from __future__ import annotations

import json

from tender_timeline.schema import TenderTimelineItem
from tender_timeline.utils import repo_root

OUTPUT_SCHEMA_REMINDER = """{
  "governing_clause_id": "...",
  "operative_deadline": "ISO-8601 datetime or null",
  "action_datetime": "ISO-8601 datetime or null",
  "required_bid_security_validity_through": "YYYY-MM-DD or null",
  "submitted_bid_security_validity_through": "YYYY-MM-DD or null",
  "precondition_status": "satisfied | unsatisfied | not_evaluated | unknown",
  "verdict": "VALID | INVALID",
  "failure_reason_code": "LATE_SUBMISSION | MISSED_PROTEST_WINDOW | ... | VALID",
  "citation": {}
}"""


def _load_document_text(path: str) -> str:
    doc_path = repo_root() / path
    return doc_path.read_text(encoding="utf-8")


def build_prompt(item: TenderTimelineItem, prompt_template: str) -> str:
    """Build a full model prompt for one benchmark item."""
    seen_paths: set[str] = set()
    document_blocks: list[str] = []
    for doc in item.documents:
        if doc.path in seen_paths:
            continue
        seen_paths.add(doc.path)
        document_blocks.append(
            f"### Document: {doc.title} ({doc.doc_id})\n"
            f"Path: {doc.path}\n\n"
            f"{_load_document_text(doc.path)}"
        )

    task_json = json.dumps(item.task, indent=2, ensure_ascii=False)

    return (
        f"{prompt_template.strip()}\n\n"
        f"## Benchmark Item\n"
        f"- item_id: {item.item_id}\n"
        f"- family_id: {item.family_id}\n"
        f"- jurisdiction: {item.jurisdiction}\n"
        f"- data_version: {item.data_version}\n\n"
        f"## Task\n"
        f"```json\n{task_json}\n```\n\n"
        f"## Referenced Documents\n\n"
        f"{chr(10).join(document_blocks)}\n\n"
        f"## Required Output Schema\n"
        f"Return JSON only matching this schema:\n"
        f"```json\n{OUTPUT_SCHEMA_REMINDER}\n```\n\n"
        f"Do not include prose outside JSON."
    )
