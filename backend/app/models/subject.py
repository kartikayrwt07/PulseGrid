from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(16), nullable=False, default="THEORY")
    sessions_per_week: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    credits: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    weekly_records = relationship(
        "WeeklyRecord", back_populates="subject", cascade="all, delete-orphan"
    )
