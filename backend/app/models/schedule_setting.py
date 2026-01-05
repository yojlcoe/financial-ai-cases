"""Schedule settings database model."""
from sqlalchemy import Column, Integer, String, Date, DateTime, func
from app.core.database import Base


class ScheduleSetting(Base):
    """Schedule configuration for periodic job execution."""

    __tablename__ = "schedule_settings"

    id = Column(Integer, primary_key=True, index=True)
    search_start_date = Column(Date, nullable=False)
    search_end_date = Column(Date, nullable=False)
    schedule_type = Column(String(50), default="weekly")  # daily, weekly
    schedule_day = Column(Integer, default=1)  # 曜日 (0=月, 6=日) or 日付
    schedule_hour = Column(Integer, default=9)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())