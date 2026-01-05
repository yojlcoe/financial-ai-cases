from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime

from app.models import JobHistory
from app.utils.timezone import get_jst_now


async def get_job_histories(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20
) -> tuple[List[JobHistory], int]:
    query = select(JobHistory).order_by(
        JobHistory.started_at.desc()
    ).offset(skip).limit(limit)
    
    count_query = select(func.count(JobHistory.id))
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    return jobs, total


async def create_job(db: AsyncSession, job_type: str) -> JobHistory:
    db_job = JobHistory(
        job_type=job_type,
        status="running",
        started_at=get_jst_now(),
    )
    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    return db_job


async def update_job_progress(
    db: AsyncSession,
    job_id: int,
    processed_companies: int,
    total_articles: int
) -> Optional[JobHistory]:
    query = select(JobHistory).where(JobHistory.id == job_id)
    result = await db.execute(query)
    db_job = result.scalar_one_or_none()
    
    if not db_job:
        return None
    
    db_job.processed_companies = processed_companies
    db_job.total_articles = total_articles
    
    await db.commit()
    return db_job


async def complete_job(
    db: AsyncSession,
    job_id: int,
    status: str = "completed",
    error_message: Optional[str] = None
) -> Optional[JobHistory]:
    query = select(JobHistory).where(JobHistory.id == job_id)
    result = await db.execute(query)
    db_job = result.scalar_one_or_none()
    
    if not db_job:
        return None
    
    db_job.status = status
    db_job.completed_at = get_jst_now()
    db_job.error_message = error_message
    
    await db.commit()
    return db_job
