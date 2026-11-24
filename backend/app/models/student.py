from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    roll_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    program: Mapped[str] = mapped_column(String(60), nullable=False, default="B.Tech CSE")
    year: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    is_hero_persona: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    persona_tag: Mapped[str | None] = mapped_column(String(60), nullable=True)

    weekly_records = relationship(
        "WeeklyRecord", back_populates="student", cascade="all, delete-orphan"
    )
    interventions = relationship(
        "Intervention", back_populates="student", cascade="all, delete-orphan"
    )
    snapshot = relationship(
        "PredictionSnapshot", back_populates="student", uselist=False, cascade="all, delete-orphan"
    )
