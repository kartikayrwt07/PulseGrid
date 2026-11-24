"""Pydantic schemas for Faculty Dashboard summary and triage."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.student import StudentSummary


class DistributionBucket(BaseModel):
    label: str
    count: int


class TriagePoint(BaseModel):
    id: int
    roll_no: str
    name: str
    risk_tier: str
    archetype: str
    risk_score: float
    ponr_days_left: int
    projected_final_score: float
    projected_score_after: float
    rescue_gain: float


class DashboardSummaryResponse(BaseModel):
    total_students: int
    safe_count: int
    watch_count: int
    at_risk_count: int
    critical_count: int
    cusum_alerts_count: int
    detention_cliff_count: int
    passive_copier_count: int
    avg_projected_score: float
    current_week: int
    active_week: int = 9
    total_weeks: int
    risk_distribution: list[DistributionBucket]
    archetype_distribution: list[DistributionBucket]
    urgent_queue: list[StudentSummary]
    triage_points: list[TriagePoint]
