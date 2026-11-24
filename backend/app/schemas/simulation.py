"""Pydantic schemas for interactive What-If simulation."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.analytics import SHAPEntry


class SimulateRequest(BaseModel):
    student_id: int = Field(..., ge=1)
    attendance_pct: float = Field(..., ge=0.0, le=100.0)
    assignment_score: float = Field(..., ge=0.0, le=100.0)
    internal_score: float = Field(..., ge=0.0, le=100.0)
    weeks_remaining: int | None = Field(default=None, ge=1, le=14)
    subject_id: int | None = Field(default=None, ge=1)


class SimulateResponse(BaseModel):
    student_id: int
    baseline_tier: str
    baseline_risk_score: float
    baseline_projected_score: float
    simulated_tier: str
    simulated_risk_score: float
    simulated_projected_score: float
    score_delta: float
    at_risk_probability: float
    historical_cusum_triggered: bool = False
    projected_cusum_active: bool = False
    class_probabilities: dict[str, float]
    shap_values: list[SHAPEntry]
    grouped_shap: list[SHAPEntry] = Field(default_factory=list)
