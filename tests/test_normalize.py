"""Tests for tender_timeline.normalize."""

from datetime import datetime

from tender_timeline.normalize import (
    date_or_datetime_equal,
    normalize_enum,
    normalize_string,
    parse_datetime,
)


def test_normalize_enum_examples() -> None:
    assert normalize_enum("valid") == "VALID"
    assert normalize_enum("late submission") == "LATE_SUBMISSION"
    assert normalize_enum("insufficient-bid-security-validity") == "INSUFFICIENT_BID_SECURITY_VALIDITY"


def test_normalize_string_collapses_whitespace_and_lowercases() -> None:
    assert normalize_string("  Addendum   2 ") == "addendum 2"
    assert normalize_string(None) == ""


def test_parse_datetime_with_timezone_offsets() -> None:
    dt = parse_datetime("2026-06-14T10:00:00+03:00")
    assert dt == datetime.fromisoformat("2026-06-14T10:00:00+03:00")
    assert parse_datetime("2026-07-20T17:00:00-04:00") is not None


def test_date_only_comparison() -> None:
    assert date_or_datetime_equal("2026-11-09", "2026-11-09")
    assert not date_or_datetime_equal("2026-11-09", "2026-11-10")


def test_datetime_comparison() -> None:
    assert date_or_datetime_equal(
        "2026-06-14T10:00:00+03:00",
        "2026-06-14T10:00:00+03:00",
    )
    assert not date_or_datetime_equal(
        "2026-06-14T10:00:00+03:00",
        "2026-06-10T10:00:00+03:00",
    )


def test_invalid_datetime_returns_none_and_comparison_fails_safely() -> None:
    assert parse_datetime("not-a-date") is None
    assert not date_or_datetime_equal("2026-06-14T10:00:00+03:00", "bad-value")


def test_end_of_day_tolerance_equates_2359_00_and_2359_59() -> None:
    # "expires at 23:59" — 23:59:00 and 23:59:59 are the same end-of-day deadline
    assert date_or_datetime_equal(
        "2026-08-15T23:59:00-04:00",
        "2026-08-15T23:59:59-04:00",
    )
    assert date_or_datetime_equal(
        "2026-09-11T23:59:59+03:00",
        "2026-09-11T23:59:00+03:00",
    )


def test_end_of_day_tolerance_does_not_cross_days_or_offsets() -> None:
    # Different date → not equal even if both are end-of-day
    assert not date_or_datetime_equal(
        "2026-08-15T23:59:00-04:00",
        "2026-08-16T23:59:59-04:00",
    )
    # Different offset → different instant, not equal
    assert not date_or_datetime_equal(
        "2026-08-15T23:59:00-04:00",
        "2026-08-15T23:59:59+00:00",
    )


def test_end_of_day_tolerance_does_not_loosen_normal_deadlines() -> None:
    # Non-end-of-day times still require exact match
    assert not date_or_datetime_equal(
        "2026-07-20T17:00:00-04:00",
        "2026-07-20T17:00:30-04:00",
    )
