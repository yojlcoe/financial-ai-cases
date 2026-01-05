from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.models import SourceUrl
from app.schemas import SourceUrlCreate, SourceUrlUpdate


async def get_source_urls_by_company(
    db: AsyncSession,
    company_id: int
) -> List[SourceUrl]:
    query = select(SourceUrl).where(SourceUrl.company_id == company_id)
    result = await db.execute(query)
    return result.scalars().all()


async def create_source_url(
    db: AsyncSession,
    company_id: int,
    source_url: SourceUrlCreate
) -> SourceUrl:
    db_url = SourceUrl(
        company_id=company_id,
        url=source_url.url,
        url_type=source_url.url_type,
        is_active=source_url.is_active,
    )
    db.add(db_url)
    await db.commit()
    await db.refresh(db_url)
    return db_url


async def update_source_url(
    db: AsyncSession,
    url_id: int,
    source_url: SourceUrlUpdate
) -> Optional[SourceUrl]:
    query = select(SourceUrl).where(SourceUrl.id == url_id)
    result = await db.execute(query)
    db_url = result.scalar_one_or_none()

    if not db_url:
        return None

    update_data = source_url.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_url, field, value)

    await db.commit()
    await db.refresh(db_url)
    return db_url


async def delete_source_url(db: AsyncSession, url_id: int) -> bool:
    query = select(SourceUrl).where(SourceUrl.id == url_id)
    result = await db.execute(query)
    db_url = result.scalar_one_or_none()

    if not db_url:
        return False

    await db.delete(db_url)
    await db.commit()
    return True
