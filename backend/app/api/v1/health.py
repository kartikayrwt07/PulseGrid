from pathlib import Path

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import BACKEND_DIR, get_settings
from app.core.database import get_db
from app.models.student import Student
from app.repositories.snapshot_repo import get_active_week
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(request: Request, db: Session = Depends(get_db)) -> HealthResponse:
    """Health endpoint returning database, model artifact, and dataset status."""
    settings = get_settings()
    db_ok = False
    dataset_count = 0
    active_week = int(settings.CURRENT_WEEK)
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
        dataset_count = int(db.scalar(select(func.count()).select_from(Student)) or 0)
        active_week = get_active_week(db)
    except SQLAlchemyError:
        db_ok = False

    artifacts_dir = Path(BACKEND_DIR) / "ml" / "artifacts"
    model_loaded = bool(
        getattr(request.app.state, "model_loaded", False)
        or (artifacts_dir / "classifier.joblib").exists()
    )

    return HealthResponse(
        status="ok" if db_ok else "degraded",
        db_ok=db_ok,
        model_loaded=model_loaded,
        dataset_count=dataset_count,
        active_week=active_week,
        total_weeks=int(settings.TOTAL_WEEKS),
    )


@router.head("/health", include_in_schema=False)
def health_head() -> Response:
    """HEAD health endpoint for uptime monitors (prevents OpenAPI duplicate operationId)."""
    return Response(status_code=200)
