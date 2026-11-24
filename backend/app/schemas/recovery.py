"""Pydantic schemas for counterfactual recovery plans."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RecoveryStep(BaseModel):
    feature: str
    label: str
    action: str
    subject: str = "ALL"
    current_value: float = Field(..., ge=0.0, le=1.0)
    target_value: float = Field(..., ge=0.0, le=1.0)
    current_pct: float = Field(..., ge=0.0, le=100.0)
    target_pct: float = Field(..., ge=0.0, le=100.0)
    delta_pct: float = Field(..., ge=0.0, le=100.0)
    unit: str = "ratio"


class RecoveryPlanResponse(BaseModel):
    student_id: int | None = None
    feasible: bool
    current_tier: str
    target_tier: str
    projected_score_before: float
    projected_score_after: float
    waiver_required: bool
    requires_waiver: bool = False
    recovery_steps: list[RecoveryStep]
    summary: str
