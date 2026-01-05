from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.models import Company, SourceUrl
from app.schemas import CompanyCreate, CompanyUpdate


async def get_companies(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None
) -> tuple[List[Company], int]:
    query = select(Company).options(
        selectinload(Company.source_urls),
        selectinload(Company.search_settings)
    )
    count_query = select(func.count(Company.id))

    if is_active is not None:
        query = query.where(Company.is_active == is_active)
        count_query = count_query.where(Company.is_active == is_active)

    # ID順でソート（安定した順序を保証）
    query = query.order_by(Company.id).offset(skip).limit(limit)

    result = await db.execute(query)
    companies = result.scalars().all()

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return companies, total


async def get_company(db: AsyncSession, company_id: int) -> Optional[Company]:
    query = select(Company).options(
        selectinload(Company.source_urls)
    ).where(Company.id == company_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_company(db: AsyncSession, company: CompanyCreate) -> Company:
    db_company = Company(
        name=company.name,
        name_en=company.name_en,
        country=company.country,
        is_active=company.is_active,
    )
    db.add(db_company)
    await db.flush()

    # ソースURLを追加
    for url_data in company.source_urls:
        db_url = SourceUrl(
            company_id=db_company.id,
            url=url_data.url,
            url_type=url_data.url_type,
            is_active=url_data.is_active,
        )
        db.add(db_url)

    await db.commit()

    # リレーションシップを明示的にロードして返す
    from sqlalchemy.orm import selectinload
    query = select(Company).options(
        selectinload(Company.source_urls)
    ).where(Company.id == db_company.id)
    result = await db.execute(query)
    return result.scalar_one()


async def update_company(
    db: AsyncSession,
    company_id: int,
    company: CompanyUpdate
) -> Optional[Company]:
    db_company = await get_company(db, company_id)
    if not db_company:
        return None
    
    update_data = company.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_company, field, value)
    
    await db.commit()
    await db.refresh(db_company)
    return db_company


async def delete_company(db: AsyncSession, company_id: int) -> bool:
    db_company = await get_company(db, company_id)
    if not db_company:
        return False
    
    await db.delete(db_company)
    await db.commit()
    return True
