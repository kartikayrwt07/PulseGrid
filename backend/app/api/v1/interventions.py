"""Intervention logging and before/after risk lift tracking endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import TokenPayload
from app.core.database import get_db
from app.core.dependencies import assert_student_scope, get_current_user, require_faculty
from app.repositories.intervention_repo import create_intervention, list_interventions
from app.schemas.intervention import (
    InterventionCreate,
    InterventionListResponse,
    InterventionResponse,
)

router = APIRouter(prefix="/interventions", tags=["interventions"])


@router.get("", response_model=InterventionListResponse)
def get_interventions(
    student_id: int | None = Query(default=None, ge=1),
    user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InterventionListResponse:
    """List logged faculty interventions (students scoped strictly to own records)."""
    effective_student_id = student_id
    if user.role == "student":
        target = student_id if student_id is not None else (user.student_id or -1)
        assert_student_scope(user, target)
        effective_student_id = user.student_id
    return list_interventions(db, student_id=effective_student_id)


@router.post("", response_model=InterventionResponse, status_code=status.HTTP_201_CREATED)
def log_intervention(
    payload: InterventionCreate,
    faculty: TokenPayload = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> InterventionResponse:
    """Create a faculty intervention record capturing baseline pre_risk_tier."""
    faculty_id = faculty.sub.split(":")[-1] if ":" in faculty.sub else faculty.sub
    created = create_intervention(db, payload, faculty_id=faculty_id)
    if created is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {payload.student_id} not found.",
        )
    return created
