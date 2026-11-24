"""Pydantic schemas for Week 4-9 Time Machine scrubber & Naive vs Cohort comparison."""

from __future__ import annotations

from pydantic import BaseModel


class TimeMachinePoint(BaseModel):
    student_id: int
    roll_no: str
    name: str
    risk_score: float
    naive_risk_score: float
    projected_score: float
    risk_tier: str
    naive_tier: str
    archetype: str
    cusum_triggered: bool
    naive_flagged: bool
    is_hero_aarav: bool = False


class EngineWeekMetrics(BaseModel):
    safe_count: int
    watch_count: int
    at_risk_count: int
    critical_count: int
    flagged_count: int
    false_alarms_on_track: int
    silent_slipper_detected: int
    silent_slipper_total: int
    aarav_detected: bool


class ShockBanner(BaseModel):
    subject_code: str
    subject_name: str
    week: int
    drop_pts: float
    message: str


class TimeMachineResponse(BaseModel):
    week: int
    active_week: int
    available_weeks: list[int]
    shock_banner: ShockBanner | None = None
    pulsegrid: EngineWeekMetrics
    naive_static: EngineWeekMetrics
    false_alarms_prevented: int
    delta_callout: str
    points: list[TimeMachinePoint]
