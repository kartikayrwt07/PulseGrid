"""Pydantic schemas for academic analytics payloads."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.recovery import RecoveryPlanResponse


class WeeklyTrajectoryPoint(BaseModel):
    week: int = Field(..., ge=1, le=20)
    attendance_pct: float
    assignment_score: float
    internal_score: float
    composite: float
    z_composite: float
    z_att: float
    z_assign: float
    z_internal: float


class SubjectZSummary(BaseModel):
    subject_id: int
    subject_code: str
    z_att_mean: float
    z_assign_mean: float
    z_internal_mean: float


class EWMAResult(BaseModel):
    ewma_series: list[float]
    flagged_weeks: list[int]


class CUSUMResult(BaseModel):
    change_point_detected: bool
    change_point_week: int | None = None
    shift_magnitude: float | None = None
    cusum_series: list[float]
    baseline_mean: float
    baseline_std: float
    ewma: EWMAResult | None = None
    z_composites: list[float] = Field(default_factory=list)


class InternalStanding(BaseModel):
    average_pct: float
    min_needed_ia_pct: float
    passing: bool


class PONRSubjectStatus(BaseModel):
    subject_id: int
    subject_code: str
    subject_name: str
    subject_type: str
    sessions_per_week: int
    attended_so_far: int
    current_pct: float
    bunk_budget: int
    bunk_budget_sessions: int = 0
    ponr_sessions_left: int
    min_future_needed: int
    remaining_sessions: int
    min_total_needed: int
    eligibility_status: str
    internal_standing: InternalStanding


class SHAPEntry(BaseModel):
    feature: str
    label: str
    shap_value: float
    feature_value: float


class StudentAnalyticsResponse(BaseModel):
    student_id: int
    roll_no: str
    name: str
    program: str
    year: int
    risk_tier: str
    risk_score: float
    projected_final_score: float
    ponr_days_left: int
    active_week: int = 9
    total_weeks: int = 14
    archetype: str
    primary_archetype: str
    secondary_flags: list[str] = Field(default_factory=list)
    divergence_index: float
    cusum_triggered: bool
    cusum_week: int | None = None
    z_att_avg: float
    z_assign_avg: float
    z_internal_avg: float
    baseline_features: dict[str, float]
    weekly_trajectory: list[WeeklyTrajectoryPoint]
    subject_z_summary: list[SubjectZSummary]
    cusum: CUSUMResult
    ponr: list[PONRSubjectStatus]
    shap_values: list[SHAPEntry]
    grouped_shap: list[SHAPEntry] = Field(default_factory=list)
    recovery_plan: RecoveryPlanResponse
