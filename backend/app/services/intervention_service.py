"""Intervention service helpers calculating before/after risk lift metrics."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.intervention_repo import create_intervention, list_interventions
from app.schemas.intervention import (
    InterventionCreate,
    InterventionListResponse,
    InterventionResponse,
)


def log_faculty_intervention(
    db: Session, payload: InterventionCreate, faculty_id: str
) -> InterventionResponse | None:
    """Create a faculty intervention and immediately return before/after lift state."""
    return create_intervention(db, payload=payload, faculty_id=faculty_id)


def get_intervention_feed_with_summary(
    db: Session, student_id: int | None = None
) -> tuple[InterventionListResponse, dict[str, int]]:
    """Return role-scoped intervention list alongside improved vs active counts."""
    listing = list_interventions(db, student_id=student_id)
    improved_count = sum(1 for item in listing.items if item.risk_improved)
    return listing, {
        "total": listing.total,
        "improved_count": improved_count,
        "monitoring_count": listing.total - improved_count,
    }
