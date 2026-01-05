from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db
from app.crud import job as crud_job
from app.crud import company as crud_company
from app.models import JobHistory
from app.schemas import (
    JobHistoryListResponse,
    JobStartRequest,
    JobStartResponse,
)
from app.services.crawler.research_agent import ResearchAgent

router = APIRouter()


@router.get("", response_model=JobHistoryListResponse)
async def list_jobs(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    jobs, total = await crud_job.get_job_histories(db, skip=skip, limit=limit)
    return JobHistoryListResponse(items=jobs, total=total)


@router.post("/start", response_model=JobStartResponse)
async def start_job(
    request: JobStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    # アクティブな企業を取得
    companies, total = await crud_company.get_companies(db, is_active=True)
    if total == 0:
        raise HTTPException(status_code=400, detail="No active companies found")
    
    # ジョブを作成
    job = await crud_job.create_job(db, request.job_type)
    
    # total_companies を更新
    query = select(JobHistory).where(JobHistory.id == job.id)
    result = await db.execute(query)
    db_job = result.scalar_one()
    db_job.total_companies = total
    await db.commit()
    
    # バックグラウンドで実行
    background_tasks.add_task(
        run_research_job,
        job.id,
        request.job_type
    )
    
    return JobStartResponse(
        job_id=job.id,
        message=f"Job started with {total} companies"
    )


async def run_research_job(job_id: int, job_type: str):
    """バックグラウンドで実行される調査ジョブ"""
    agent = ResearchAgent()
    await agent.run(job_id)
