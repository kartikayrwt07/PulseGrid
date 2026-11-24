"""Snapshot JSON parsing and lookup helpers."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.snapshot import PredictionSnapshot
from app.models.weekly_record import WeeklyRecord


def get_active_week(db: Session) -> int:
    """Infer current academic week from weekly_records, falling back to CURRENT_WEEK."""
    settings = get_settings()
    active = db.scalar(
        select(func.coalesce(func.max(WeeklyRecord.week), settings.CURRENT_WEEK))
    )
    return int(active) if active is not None else int(settings.CURRENT_WEEK)


def get_snapshot_by_student_id(db: Session, student_id: int) -> PredictionSnapshot | None:
    stmt = select(PredictionSnapshot).where(PredictionSnapshot.student_id == student_id)
    return db.scalar(stmt)


def safe_json_loads(raw: str | None, fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def extract_projected_score_after(snap: PredictionSnapshot | None) -> float:
    if snap is None:
        return 0.0
    recovery = safe_json_loads(snap.recovery_path_json, {})
    return float(recovery.get("projected_score_after", snap.projected_final_score))
