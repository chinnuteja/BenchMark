"""Normalization utilities for grading model predictions."""

from __future__ import annotations

import re
from datetime import datetime


def normalize_string(value: object | None) -> str:
    """Convert a value to a lowercase comparison string."""
    if value is None:
        return ""
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def normalize_enum(value: object | None) -> str:
    """Normalize enum-like values to uppercase underscore form."""
    if value is None:
        return ""
    text = str(value).strip().upper()
    text = text.replace("-", "_")
    text = re.sub(r"\s+", "_", text)
    return text


def parse_datetime(value: object | None) -> datetime | None:
    """Parse an ISO datetime string; return None on failure."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


_DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _is_date_only(value: str) -> bool:
    return bool(_DATE_ONLY_RE.fullmatch(value.strip()))


def _is_end_of_day(dt: datetime) -> bool:
    """True for the final minute of a local day (23:59:00–23:59:59)."""
    return dt.hour == 23 and dt.minute == 59


def date_or_datetime_equal(expected: object | None, predicted: object | None) -> bool:
    """Compare date-only strings or ISO datetimes.

    Datetimes must match exactly, with one principled tolerance: an "expires at 23:59"
    end-of-day deadline treats 23:59:00 through 23:59:59 on the same local date and offset
    as equivalent (e.g. gold 23:59:00 == model 23:59:59). This avoids penalizing a
    defensible end-of-day reading as if it were a reasoning error.
    """
    if expected is None and predicted is None:
        return True
    if expected is None or predicted is None:
        return False

    expected_text = str(expected).strip()
    predicted_text = str(predicted).strip()

    if _is_date_only(expected_text) and _is_date_only(predicted_text):
        return expected_text == predicted_text

    expected_dt = parse_datetime(expected_text)
    predicted_dt = parse_datetime(predicted_text)
    if expected_dt is None or predicted_dt is None:
        return False
    if expected_dt == predicted_dt:
        return True

    return (
        _is_end_of_day(expected_dt)
        and _is_end_of_day(predicted_dt)
        and expected_dt.date() == predicted_dt.date()
        and expected_dt.utcoffset() == predicted_dt.utcoffset()
    )
