from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Intervention(Base):
    __tablename__ = "interventions"
    __table_args__ = (Index("ix_intervention_student_week", "student_id", "week"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    faculty_id: Mapped[str] = mapped_column(String(40), nullable=False, default="FAC-001")
    week: Mapped[int] = mapped_column(Integer, nullable=False)
    intervention_type: Mapped[str] = mapped_column(String(80), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str | None] = mapped_column(String(120), nullable=True)
    pre_risk_tier: Mapped[str | None] = mapped_column(String(24), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    student = relationship("Student", back_populates="interventions")
