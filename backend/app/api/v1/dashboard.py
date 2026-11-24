"""Faculty cohort summary dashboard endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import TokenPayload
from app.core.database import get_db
from app.core.dependencies import require_faculty
from app.repositories.dashboard_repo import get_dashboard_summary
from app.schemas.dashboard import DashboardSummaryResponse
from app.schemas.time_machine import TimeMachineResponse
from app.services.time_machine_service import get_time_machine_week

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(
    _faculty: TokenPayload = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    """Return cohort KPIs, tier/archetype distributions, urgent queue, and triage data."""
    return get_dashboard_summary(db)


@router.get("/time-machine", response_model=TimeMachineResponse)
def dashboard_time_machine(
    week: int | None = Query(default=None, ge=4, le=20),
    _faculty: TokenPayload = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> TimeMachineResponse:
    """Return precomputed Week 4..active_week comparison of PulseGrid vs Naive Static."""
    return get_time_machine_week(db, week=week)
