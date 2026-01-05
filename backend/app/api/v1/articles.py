from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from app.api.deps import get_db
from app.crud import article as crud_article
from app.crud import job as crud_job
from app.schemas import (
    ArticleListResponse,
    ArticleUpdate,
    ArticleAnalysisStats,
    ArticleAnalysisCoefficients,
    ArticleResponse,
    ArticleCreate,
)
from pydantic import BaseModel, HttpUrl

router = APIRouter()


@router.get("", response_model=ArticleListResponse)
async def list_articles(
    skip: int = 0,
    limit: int = 100,
    company_id: Optional[int] = None,
    category: Optional[str] = Query(None, description="Filter by category"),
    business_area: Optional[str] = Query(None, description="Filter by business area"),
    tags: Optional[str] = Query(None, description="Filter by tag"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    include_unknown_dates: Optional[bool] = Query(None, description="Include articles with unknown dates"),
    is_reviewed: Optional[bool] = Query(None, description="Filter by review status"),
    db: AsyncSession = Depends(get_db)
):
    articles, total = await crud_article.get_articles(
        db,
        skip=skip,
        limit=limit,
        company_id=company_id,
        category=category,
        business_area=business_area,
        tags=tags,
        start_date=start_date,
        end_date=end_date,
        include_unknown_dates=include_unknown_dates,
        is_reviewed=is_reviewed,
    )
    return ArticleListResponse(items=articles, total=total)


@router.get("/analysis-stats", response_model=ArticleAnalysisStats)
async def get_article_analysis_stats(
    company_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    total, analyzed = await crud_article.get_analysis_stats(
        db,
        company_id=company_id,
    )
    coefficient = round((analyzed / total) * 100, 1) if total else 0.0
    return ArticleAnalysisStats(
        total=total,
        analyzed=analyzed,
        coefficient=coefficient,
    )


@router.get("/analysis-coefficients", response_model=ArticleAnalysisCoefficients)
async def get_article_analysis_coefficients(
    company_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    data = await crud_article.get_analysis_coefficients(
        db,
        company_id=company_id,
    )
    return ArticleAnalysisCoefficients(**data)


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    article_update: ArticleUpdate,
    db: AsyncSession = Depends(get_db)
):
    updated = await crud_article.update_article(db, article_id, article_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Article not found")
    return updated


class AddArticleFromUrlRequest(BaseModel):
    url: HttpUrl
    company_id: int


class AddArticlesFromUrlsRequest(BaseModel):
    urls: list[HttpUrl]
    company_id: int


class AddArticleFromUrlResponse(BaseModel):
    job_id: int
    message: str


@router.post("/from-url", response_model=AddArticleFromUrlResponse)
async def add_article_from_url(
    request: AddArticleFromUrlRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """URLから記事を追加（非同期処理）"""
    from app.crud import company as crud_company

    # 企業を取得
    company = await crud_company.get_company(db, request.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # URLの重複チェック
    existing = await crud_article.get_article_by_url(db, str(request.url))
    if existing:
        raise HTTPException(status_code=400, detail="Article with this URL already exists")

    # ジョブを作成（total_companies=1で進捗表示用）
    job = await crud_job.create_job(db, job_type="url_addition")

    # total_companies を1に設定（進捗表示用）
    from sqlalchemy import select
    from app.models import JobHistory
    query = select(JobHistory).where(JobHistory.id == job.id)
    result = await db.execute(query)
    db_job = result.scalar_one()
    db_job.total_companies = 1
    await db.commit()

    # バックグラウンドで実行
    background_tasks.add_task(
        process_url_addition,
        job.id,
        str(request.url),
        request.company_id
    )

    return AddArticleFromUrlResponse(
        job_id=job.id,
        message=f"URL addition job started for {company.name}"
    )


@router.post("/from-urls", response_model=AddArticleFromUrlResponse)
async def add_articles_from_urls(
    request: AddArticlesFromUrlsRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """複数URLから記事を一括追加（非同期処理）"""
    from app.crud import company as crud_company

    # 企業を取得
    company = await crud_company.get_company(db, request.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # URLリストの検証
    if not request.urls:
        raise HTTPException(status_code=400, detail="At least one URL is required")

    # 重複チェック
    url_strings = [str(url) for url in request.urls]
    for url_str in url_strings:
        existing = await crud_article.get_article_by_url(db, url_str)
        if existing:
            raise HTTPException(status_code=400, detail=f"Article already exists: {url_str}")

    # ジョブを作成
    job = await crud_job.create_job(db, job_type="url_addition")

    # total_companies をURL数に設定（進捗表示用）
    from sqlalchemy import select
    from app.models import JobHistory
    query = select(JobHistory).where(JobHistory.id == job.id)
    result = await db.execute(query)
    db_job = result.scalar_one()
    db_job.total_companies = len(url_strings)
    await db.commit()

    # バックグラウンドで実行
    background_tasks.add_task(
        process_urls_addition,
        job.id,
        url_strings,
        request.company_id
    )

    return AddArticleFromUrlResponse(
        job_id=job.id,
        message=f"{len(url_strings)} URL(s) addition job started for {company.name}"
    )


async def process_url_addition(job_id: int, url: str, company_id: int):
    """バックグラウンドで実行されるURL追加処理（単一URL）"""
    from app.core.database import AsyncSessionLocal
    from app.services.crawler.research_agent import ResearchAgent
    from app.crud import company as crud_company
    from datetime import datetime

    async with AsyncSessionLocal() as db:
        try:
            # 企業を取得
            company = await crud_company.get_company(db, company_id)
            if not company:
                await crud_job.complete_job(
                    db,
                    job_id,
                    status="failed",
                    error_message="Company not found"
                )
                return

            # ResearchAgentを使って記事を処理
            agent = ResearchAgent()
            item = {"url": url, "title": "", "source": "manual"}

            article = await agent._fetch_and_process_article(
                db,
                company,
                item,
                datetime.now().date(),
                datetime.now().date()
            )

            if not article:
                await crud_job.complete_job(
                    db,
                    job_id,
                    status="failed",
                    error_message="Failed to fetch or process article"
                )
                return

            # 成功
            await crud_job.update_job_progress(db, job_id, 1, 1)
            await crud_job.complete_job(db, job_id, status="completed")

        except Exception as e:
            await crud_job.complete_job(
                db,
                job_id,
                status="failed",
                error_message=str(e)
            )


async def process_urls_addition(job_id: int, urls: list[str], company_id: int):
    """バックグラウンドで実行されるURL追加処理（複数URL）"""
    from app.core.database import AsyncSessionLocal
    from app.services.crawler.research_agent import ResearchAgent
    from app.crud import company as crud_company
    from datetime import datetime
    import asyncio

    async with AsyncSessionLocal() as db:
        try:
            # 企業を取得
            company = await crud_company.get_company(db, company_id)
            if not company:
                await crud_job.complete_job(
                    db,
                    job_id,
                    status="failed",
                    error_message="Company not found"
                )
                return

            agent = ResearchAgent()
            successful = 0
            failed = 0

            # URLを順番に処理
            for i, url in enumerate(urls):
                try:
                    item = {"url": url, "title": "", "source": "manual"}

                    article = await agent._fetch_and_process_article(
                        db,
                        company,
                        item,
                        datetime.now().date(),
                        datetime.now().date()
                    )

                    if article:
                        successful += 1
                    else:
                        failed += 1

                    # 進捗を更新
                    await crud_job.update_job_progress(db, job_id, i + 1, successful)

                except Exception as e:
                    print(f"Error processing URL {url}: {e}")
                    failed += 1
                    await crud_job.update_job_progress(db, job_id, i + 1, successful)

                # レート制限対策
                await asyncio.sleep(2)

            # 完了
            if failed > 0:
                await crud_job.complete_job(
                    db,
                    job_id,
                    status="completed",
                    error_message=f"Completed with {failed} failed URL(s)"
                )
            else:
                await crud_job.complete_job(db, job_id, status="completed")

        except Exception as e:
            await crud_job.complete_job(
                db,
                job_id,
                status="failed",
                error_message=str(e)
            )
