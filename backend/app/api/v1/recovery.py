"""Per-student counterfactual recovery plan endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.auth import TokenPayload
from app.core.database import get_db
from app.core.dependencies import assert_student_scope, get_current_user
from app.repositories.snapshot_repo import get_snapshot_by_student_id, safe_json_loads
from app.schemas.recovery import RecoveryPlanResponse

router = APIRouter(prefix="/students", tags=["recovery"])


@router.get("/{student_id}/recovery-plan", response_model=RecoveryPlanResponse)
def get_recovery_plan(
    student_id: int = Path(..., ge=1),
    user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecoveryPlanResponse:
    """Return the minimum-effort constrained recovery plan for a single student."""
    assert_student_scope(user, student_id)
    snap = get_snapshot_by_student_id(db, student_id)
    if snap is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery plan not found for student {student_id}.",
        )
    rec = safe_json_loads(snap.recovery_path_json, {})
    return RecoveryPlanResponse(
        student_id=student_id,
        feasible=bool(rec.get("feasible", False)),
        current_tier=str(rec.get("current_tier", snap.risk_tier)),
        target_tier=str(rec.get("target_tier", snap.risk_tier)),
        projected_score_before=float(rec.get("projected_score_before", snap.projected_final_score)),
        projected_score_after=float(rec.get("projected_score_after", snap.projected_final_score)),
        waiver_required=bool(rec.get("waiver_required", False)),
        requires_waiver=bool(rec.get("requires_waiver", rec.get("waiver_required", False))),
        recovery_steps=list(rec.get("recovery_steps", [])),
        summary=str(rec.get("summary", "")),
    )
