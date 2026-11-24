from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PredictionSnapshot(Base):
    __tablename__ = "prediction_snapshots"
    __table_args__ = (Index("ix_snapshot_tier_ponr", "risk_tier", "ponr_days_left"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
    risk_tier: Mapped[str] = mapped_column(String(24), nullable=False, default="SAFE")
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    projected_final_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ponr_days_left: Mapped[int] = mapped_column(Integer, nullable=False, default=99)
    archetype: Mapped[str] = mapped_column(String(48), nullable=False, default="ON_TRACK")
    secondary_flags_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    divergence_index: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cusum_triggered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cusum_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    z_scores_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    cusum_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    ponr_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    shap_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    recovery_path_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    student = relationship("Student", back_populates="snapshot")
