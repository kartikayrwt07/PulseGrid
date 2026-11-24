"""Student directory and full per-student analytics endpoints."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.auth import TokenPayload
from app.core.database import get_db
from app.core.dependencies import assert_student_scope, get_current_user, require_faculty
from app.repositories.student_repo import (
    get_student_analytics_detail,
    list_students_with_snapshots,
)
from app.schemas.analytics import StudentAnalyticsResponse
from app.schemas.student import StudentListResponse

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=StudentListResponse)
def list_students(
    risk_tier: Literal["SAFE", "WATCH", "AT_RISK", "CRITICAL"] | None = Query(default=None),
    archetype: str | None = Query(default=None, max_length=60),
    search: str | None = Query(default=None, max_length=80),
    sort_by: Literal["urgency", "ponr", "name", "roll_no"] = Query(default="urgency"),
    limit: int = Query(default=50, ge=1, le=300),
    offset: int = Query(default=0, ge=0),
    _faculty: TokenPayload = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> StudentListResponse:
    """List students with precomputed risk, PONR, and archetype metrics (faculty-only)."""
    return list_students_with_snapshots(
        db=db,
        risk_tier=risk_tier,
        archetype=archetype,
        search=search,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )


@router.get("/{student_id}/analytics", response_model=StudentAnalyticsResponse)
def get_student_analytics(
    student_id: int = Path(..., ge=1),
    user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudentAnalyticsResponse:
    """Fetch complete trajectory, Z-score, CUSUM, PONR, SHAP, and recovery analytics."""
    assert_student_scope(user, student_id)
    detail = get_student_analytics_detail(db, student_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} or analytics snapshot not found.",
        )
    return detail
