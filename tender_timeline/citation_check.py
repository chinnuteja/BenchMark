"""Clause-grounding checks for model predictions."""

from __future__ import annotations

import re
from typing import Any


def normalize_clause_text(text: str) -> str:
    """Normalize clause/citation text for robust substring matching."""
    normalized = text.lower()
    normalized = re.sub(r"\s+", " ", normalized).strip()
    normalized = re.sub(r"§\s+", "§", normalized)
    normalized = re.sub(r"\s+", "", normalized)
    return normalized


def _collect_text(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        parts: list[str] = []
        for nested in value.values():
            parts.extend(_collect_text(nested))
        return parts
    if isinstance(value, list):
        parts = []
        for nested in value:
            parts.extend(_collect_text(nested))
        return parts
    return []


def has_required_clause_keywords(
    prediction: dict[str, Any],
    required_keywords: list[str],
) -> tuple[bool, list[str]]:
    """Check whether all required clause keywords appear in prediction text."""
    parts: list[str] = []
    parts.extend(_collect_text(prediction.get("governing_clause_id", "")))
    parts.extend(_collect_text(prediction.get("citation", {})))
    haystack = normalize_clause_text(" ".join(parts))

    missing: list[str] = []
    for keyword in required_keywords:
        if normalize_clause_text(keyword) not in haystack:
            missing.append(keyword)

    return len(missing) == 0, missing
