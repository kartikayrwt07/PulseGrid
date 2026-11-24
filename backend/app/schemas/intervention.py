"""Pydantic schemas for faculty intervention logging and lift tracking."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class InterventionCreate(BaseModel):
    student_id: int = Field(..., ge=1)
    week: int = Field(..., ge=1, le=20)
    intervention_type: str = Field(..., min_length=2, max_length=80)
    notes: str = Field(..., min_length=3, max_length=1000)
    outcome: str | None = Field(default=None, max_length=120)


class InterventionResponse(BaseModel):
    id: int
    student_id: int
    student_roll_no: str
    student_name: str
    faculty_id: str
    week: int
    intervention_type: str
    notes: str
    outcome: str | None = None
    pre_risk_tier: str | None = None
    current_risk_tier: str
    risk_improved: bool
    created_at: datetime


class InterventionListResponse(BaseModel):
    total: int
    items: list[InterventionResponse]
