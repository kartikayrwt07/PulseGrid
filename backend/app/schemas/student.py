"""Pydantic schemas for student directory and summary views."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class StudentSummary(BaseModel):
    id: int
    roll_no: str
    name: str
    program: str
    year: int
    is_hero_persona: bool
    risk_tier: str
    risk_score: float
    projected_final_score: float
    projected_score_after: float
    ponr_days_left: int
    archetype: str
    primary_archetype: str
    secondary_flags: list[str] = Field(default_factory=list)
    divergence_index: float
    cusum_triggered: bool
    cusum_week: int | None = None


class StudentListResponse(BaseModel):
    total: int = Field(..., ge=0)
    limit: int = Field(..., ge=1)
    offset: int = Field(..., ge=0)
    items: list[StudentSummary]


class StudentDetailResponse(StudentSummary):
    persona_tag: str | None = None
    computed_at: datetime | None = None
    intervention_count: int = 0
