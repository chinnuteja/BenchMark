"""Pydantic schemas for TENDER-TIMELINE benchmark items and answers."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator

FAILURE_REASON_CODES = [
    "LATE_SUBMISSION",
    "MISSED_PROTEST_WINDOW",
    "ADDENDUM_OVERRIDE_IGNORED",
    "INSUFFICIENT_BID_SECURITY_VALIDITY",
    "UNCURED_DEFECT",
    "MISSING_PRECONDITION",
    "WRONG_CALENDAR_RULE",
    "WRONG_TIMEZONE_NORMALIZATION",
    "VALID",
]

FailureReasonCode = Literal[
    "LATE_SUBMISSION",
    "MISSED_PROTEST_WINDOW",
    "ADDENDUM_OVERRIDE_IGNORED",
    "INSUFFICIENT_BID_SECURITY_VALIDITY",
    "UNCURED_DEFECT",
    "MISSING_PRECONDITION",
    "WRONG_CALENDAR_RULE",
    "WRONG_TIMEZONE_NORMALIZATION",
    "VALID",
]

Verdict = Literal["VALID", "INVALID"]


class TenderTimelineAnswer(BaseModel):
    governing_clause_id: str
    operative_deadline: str | None = None
    action_datetime: str | None = None
    required_bid_security_validity_through: str | None = None
    submitted_bid_security_validity_through: str | None = None
    precondition_status: str
    verdict: Verdict
    failure_reason_code: FailureReasonCode
    citation: dict[str, Any] = Field(default_factory=dict)

    @field_validator("verdict", mode="before")
    @classmethod
    def normalize_verdict(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("verdict must be a string")
        normalized = value.strip().upper()
        if normalized not in ("VALID", "INVALID"):
            raise ValueError(f"invalid verdict: {value!r}")
        return normalized

    @field_validator("failure_reason_code", mode="before")
    @classmethod
    def normalize_failure_reason_code(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("failure_reason_code must be a string")
        normalized = value.strip().upper()
        if normalized not in FAILURE_REASON_CODES:
            raise ValueError(f"invalid failure_reason_code: {value!r}")
        return normalized


class DocumentRef(BaseModel):
    doc_id: str
    title: str
    path: str


class GradingSpec(BaseModel):
    strict_fields: list[str]
    date_fields: list[str] = []
    required_clause_keywords: list[str] = []
    clause_grounding_required: bool = True


class ComputeSpec(BaseModel):
    rule_type: Literal["bid_security_cascade", "protest_window", "admin_review_window"]
    governing_clause_id: Optional[str] = None
    calendar_id: Optional[str] = None
    # bid_security_cascade
    base_deadline: Optional[str] = None
    addendum_deadline: Optional[str] = None
    bid_validity_days: Optional[int] = None
    bid_security_extra_days: Optional[int] = None
    # protest_window
    protest_subtype: Optional[str] = None
    proposal_deadline: Optional[str] = None
    known_basis_window_days: Optional[int] = None
    # admin_review_window
    window_days: Optional[int] = None
    # shared window helpers
    deadline_tz_offset: Optional[str] = None
    deadline_end_of_day_time: Optional[str] = None


class TenderTimelineItem(BaseModel):
    item_id: str
    family_id: str
    data_version: str = "public_dev_v0.1"
    jurisdiction: str
    source_backbone: dict[str, Any]
    documents: list[DocumentRef]
    task: dict[str, Any]
    expected_answer: TenderTimelineAnswer
    grading: GradingSpec
    compute_spec: Optional[ComputeSpec] = None
    contrast_group: Optional[str] = None
    failure_modes: list[str]
    trap: str
    perturbation_certificate: dict[str, Any]
