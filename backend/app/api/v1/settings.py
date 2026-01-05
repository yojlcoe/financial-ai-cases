"""API endpoints for schedule settings management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.crud import schedule_setting as crud_schedule
from app.schemas import (
    ScheduleSettingCreate,
    ScheduleSettingResponse,
)

router = APIRouter()


@router.get("", response_model=ScheduleSettingResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    """Get schedule settings."""
    setting = await crud_schedule.get_schedule_setting(db)
    if not setting:
        raise HTTPException(status_code=404, detail="Settings not found")
    return setting


@router.post("", response_model=ScheduleSettingResponse)
async def update_settings(
    setting: ScheduleSettingCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create or update schedule settings."""
    return await crud_schedule.create_or_update_schedule_setting(db, setting)
