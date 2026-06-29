"""Shared utilities for tender_timeline."""

from __future__ import annotations

import json
import re
from pathlib import Path


def repo_root() -> Path:
    """Return the repository root (parent of the tender_timeline package)."""
    return Path(__file__).resolve().parent.parent


def extract_json_from_text(text: str) -> tuple[dict | None, str | None]:
    """Extract a JSON object from raw model text without raising."""
    stripped = text.strip()
    if not stripped:
        return None, "parse_error: empty input"

    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed, None
    except json.JSONDecodeError:
        pass

    fence_match = re.search(
        r"```(?:json)?\s*\n?(.*?)\n?```",
        stripped,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if fence_match:
        candidate = fence_match.group(1).strip()
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed, None
        except json.JSONDecodeError as exc:
            return None, f"parse_error: {exc}"

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = stripped[start : end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed, None
        except json.JSONDecodeError as exc:
            return None, f"parse_error: {exc}"

    return None, "parse_error: no valid JSON object found"
