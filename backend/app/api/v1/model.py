"""ML holdout model audit endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.analytics.ml_inference import get_model_audit
from app.core.auth import TokenPayload
from app.core.dependencies import get_current_user
from app.schemas.model_audit import ModelAuditResponse

router = APIRouter(prefix="/model", tags=["model"])


@router.get("/audit", response_model=ModelAuditResponse)
def model_audit(
    _user: TokenPayload = Depends(get_current_user),
) -> ModelAuditResponse:
    """Return real holdout evaluation metrics, model comparison, and feature importances."""
    try:
        audit = get_model_audit()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model audit artifacts not yet available. Run training pipeline first.",
        ) from exc
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model audit metadata is empty.",
        )
    return ModelAuditResponse(**audit)
