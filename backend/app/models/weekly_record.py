from sqlalchemy import Float, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class WeeklyRecord(Base):
    __tablename__ = "weekly_records"
    __table_args__ = (
        Index("ix_weekly_student_week", "student_id", "week"),
        Index("ix_weekly_student_subject", "student_id", "subject_id"),
        UniqueConstraint("student_id", "subject_id", "week", name="uq_weekly_student_subject_week"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    week: Mapped[int] = mapped_column(Integer, nullable=False)
    attended_sessions: Mapped[int] = mapped_column(Integer, nullable=False)
    total_sessions: Mapped[int] = mapped_column(Integer, nullable=False)
    attendance_pct: Mapped[float] = mapped_column(Float, nullable=False)
    assignment_score: Mapped[float] = mapped_column(Float, nullable=False)
    internal_score: Mapped[float] = mapped_column(Float, nullable=False)

    student = relationship("Student", back_populates="weekly_records")
    subject = relationship("Subject", back_populates="weekly_records")
