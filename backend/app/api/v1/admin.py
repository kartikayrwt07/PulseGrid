"""Demo-mode cohort restoration endpoint for repeatable live hackathon demos."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import TokenPayload
from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import require_faculty
from app.repositories.snapshot_repo import get_active_week
from app.schemas.upload import DemoResetResponse
from app.services.snapshot_service import recompute_all_snapshots
from ml.generate_data import seed_database

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/reset-demo", response_model=DemoResetResponse)
def reset_demo_cohort(
    _faculty: TokenPayload = Depends(require_faculty),
    db: Session = Depends(get_db),
) -> DemoResetResponse:
    """Restore the deterministic 240-student cohort and 4 pinned hero personas."""
    settings = get_settings()
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo cohort reset is only available when DEMO_MODE=true.",
        )
    students_seeded = seed_database(db_session=db)
    snapshots_recomputed = recompute_all_snapshots(
        db=db, current_week=get_active_week(db), commit=True
    )
    return DemoResetResponse(
        status="ok",
        students_seeded=students_seeded,
        snapshots_recomputed=snapshots_recomputed,
    )
