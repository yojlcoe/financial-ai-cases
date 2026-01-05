"""Schedule setting schemas for request/response validation."""
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class ScheduleSettingBase(BaseModel):
    """Base schedule setting schema."""

    search_start_date: date
    search_end_date: date
    schedule_type: str = "weekly"
    schedule_day: int = 1
    schedule_hour: int = 9


class ScheduleSettingCreate(ScheduleSettingBase):
    """Schema for creating schedule settings."""

    pass


class ScheduleSettingUpdate(BaseModel):
    """Schema for updating schedule settings."""

    search_start_date: Optional[date] = None
    search_end_date: Optional[date] = None
    schedule_type: Optional[str] = None
    schedule_day: Optional[int] = None
    schedule_hour: Optional[int] = None


class ScheduleSettingResponse(ScheduleSettingBase):
    """Schema for schedule setting responses."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True