"""Interactive What-If counterfactual simulation endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.analytics.ml_inference import get_grouped_and_raw_shap, predict_risk
from app.analytics.whatif import project_whatif_state
from app.core.auth import TokenPayload
from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import assert_student_scope, get_current_user
from app.repositories.snapshot_repo import (
    get_active_week,
    get_snapshot_by_student_id,
    safe_json_loads,
)
from app.schemas.analytics import SHAPEntry
from app.schemas.simulation import SimulateRequest, SimulateResponse

router = APIRouter(prefix="/simulate", tags=["simulation"])


@router.post("", response_model=SimulateResponse)
def simulate_what_if(
    payload: SimulateRequest,
    user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SimulateResponse:
    """Evaluate What-If slider adjustments without mutating persisted database state."""
    assert_student_scope(user, payload.student_id)
    snap = get_snapshot_by_student_id(db, payload.student_id)
    if snap is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction snapshot not found for student {payload.student_id}.",
        )

    z_data = safe_json_loads(snap.z_scores_json, {})
    cusum_data = safe_json_loads(snap.cusum_json, {})
    base_features = {str(k): float(v) for k, v in z_data.get("features", {}).items()}
    if not base_features:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Baseline feature vector missing from snapshot.",
        )

    settings = get_settings()
    active_week = get_active_week(db)
    weeks_left = (
        payload.weeks_remaining
        if payload.weeks_remaining is not None
        else max(1, settings.TOTAL_WEEKS - active_week)
    )
    baseline_pred = predict_risk(base_features)
    projected_features, cusum_state = project_whatif_state(
        base_features=base_features,
        future_att_pct=payload.attendance_pct,
        future_assign_pct=payload.assignment_score,
        future_internal_pct=payload.internal_score,
        weeks_remaining=weeks_left,
        total_weeks=settings.TOTAL_WEEKS,
        cohort_stats=z_data.get("cohort_stats"),
        z_composites_history=cusum_data.get("z_composites"),
    )
    sim_pred = predict_risk(projected_features)
    shap_bundle = get_grouped_and_raw_shap(projected_features)

    return SimulateResponse(
        student_id=payload.student_id,
        baseline_tier=baseline_pred["risk_tier"],
        baseline_risk_score=baseline_pred["risk_score"],
        baseline_projected_score=baseline_pred["projected_final_score"],
        simulated_tier=sim_pred["risk_tier"],
        simulated_risk_score=sim_pred["risk_score"],
        simulated_projected_score=sim_pred["projected_final_score"],
        score_delta=round(
            sim_pred["projected_final_score"] - baseline_pred["projected_final_score"], 2
        ),
        at_risk_probability=sim_pred["at_risk_probability"],
        historical_cusum_triggered=cusum_state["historical_cusum_triggered"],
        projected_cusum_active=cusum_state["projected_cusum_active"],
        class_probabilities=sim_pred["class_probabilities"],
        shap_values=[SHAPEntry(**s) for s in shap_bundle["raw_shap"]],
        grouped_shap=[SHAPEntry(**s) for s in shap_bundle["grouped_shap"]],
    )
