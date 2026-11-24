from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WeeklyTimelineCache(Base):
    """Precomputed Week 4..active_week comparison snapshots for instant Time Machine scrubbing."""

    __tablename__ = "weekly_timeline_cache"

    week: Mapped[int] = mapped_column(Integer, primary_key=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
