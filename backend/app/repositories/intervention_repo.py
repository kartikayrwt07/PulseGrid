"""Repository queries for faculty interventions and risk-tier lift tracking."""

from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.intervention import Intervention
from app.models.snapshot import PredictionSnapshot
from app.models.student import Student
from app.schemas.intervention import (
    InterventionCreate,
    InterventionListResponse,
    InterventionResponse,
)

TIER_SEVERITY = {"SAFE": 0, "WATCH": 1, "AT_RISK": 2, "CRITICAL": 3}


def _to_response(
    iv: Intervention, stu: Student, snap: PredictionSnapshot | None
) -> InterventionResponse:
    cur_tier = snap.risk_tier if snap else "SAFE"
    improved = bool(
        iv.pre_risk_tier
        and TIER_SEVERITY.get(cur_tier, 0) < TIER_SEVERITY.get(iv.pre_risk_tier, 0)
    )
    return InterventionResponse(
        id=iv.id,
        student_id=iv.student_id,
        student_roll_no=stu.roll_no,
        student_name=stu.name,
        faculty_id=iv.faculty_id,
        week=iv.week,
        intervention_type=iv.intervention_type,
        notes=iv.notes,
        outcome=iv.outcome,
        pre_risk_tier=iv.pre_risk_tier,
        current_risk_tier=cur_tier,
        risk_improved=improved,
        created_at=iv.created_at,
    )


def list_interventions(
    db: Session, student_id: int | None = None
) -> InterventionListResponse:
    stmt = (
        select(Intervention, Student, PredictionSnapshot)
        .join(Student, Student.id == Intervention.student_id)
        .outerjoin(PredictionSnapshot, PredictionSnapshot.student_id == Student.id)
        .order_by(desc(Intervention.created_at), desc(Intervention.id))
    )
    if student_id is not None:
        stmt = stmt.where(Intervention.student_id == student_id)
    rows = db.execute(stmt).all()
    items = [_to_response(iv, stu, snap) for iv, stu, snap in rows]
    return InterventionListResponse(total=len(items), items=items)


def create_intervention(
    db: Session, payload: InterventionCreate, faculty_id: str
) -> InterventionResponse | None:
    row = db.execute(
        select(Student, PredictionSnapshot)
        .outerjoin(PredictionSnapshot, PredictionSnapshot.student_id == Student.id)
        .where(Student.id == payload.student_id)
    ).first()
    if row is None:
        return None
    student, snap = row
    pre_tier = snap.risk_tier if snap else "WATCH"
    iv = Intervention(
        student_id=payload.student_id,
        faculty_id=faculty_id,
        week=payload.week,
        intervention_type=payload.intervention_type.strip(),
        notes=payload.notes.strip(),
        outcome=payload.outcome.strip() if payload.outcome else None,
        pre_risk_tier=pre_tier,
    )
    db.add(iv)
    db.commit()
    db.refresh(iv)
    return _to_response(iv, student, snap)
