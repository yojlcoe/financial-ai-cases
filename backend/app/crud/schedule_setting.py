"""CRUD operations for schedule settings."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.models.schedule_setting import ScheduleSetting
from app.schemas.schedule_setting import ScheduleSettingCreate, ScheduleSettingUpdate


async def get_schedule_setting(db: AsyncSession) -> Optional[ScheduleSetting]:
    """Get the schedule setting (singleton)."""
    query = select(ScheduleSetting).limit(1)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_or_update_schedule_setting(
    db: AsyncSession,
    setting: ScheduleSettingCreate
) -> ScheduleSetting:
    """Create or update schedule setting."""
    existing = await get_schedule_setting(db)

    if existing:
        for field, value in setting.model_dump().items():
            setattr(existing, field, value)
        await db.commit()
        await db.refresh(existing)
        return existing

    db_setting = ScheduleSetting(**setting.model_dump())
    db.add(db_setting)
    await db.commit()
    await db.refresh(db_setting)
    return db_setting
