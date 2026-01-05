from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.api.deps import get_db
from app.crud import company as crud_company
from app.crud import source_url as crud_source_url
from app.schemas import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyListResponse,
    SourceUrlCreate,
    SourceUrlUpdate,
    SourceUrlResponse,
)

router = APIRouter()


@router.get("", response_model=CompanyListResponse)
async def list_companies(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    companies, total = await crud_company.get_companies(
        db, skip=skip, limit=limit, is_active=is_active
    )
    return CompanyListResponse(items=companies, total=total)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: int, db: AsyncSession = Depends(get_db)):
    company = await crud_company.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("", response_model=CompanyResponse)
async def create_company(
    company: CompanyCreate,
    db: AsyncSession = Depends(get_db)
):
    return await crud_company.create_company(db, company)


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    company: CompanyUpdate,
    db: AsyncSession = Depends(get_db)
):
    updated = await crud_company.update_company(db, company_id, company)
    if not updated:
        raise HTTPException(status_code=404, detail="Company not found")
    return updated


@router.delete("/{company_id}")
async def delete_company(company_id: int, db: AsyncSession = Depends(get_db)):
    success = await crud_company.delete_company(db, company_id)
    if not success:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"message": "Company deleted successfully"}


@router.post("/{company_id}/urls", response_model=SourceUrlResponse)
async def add_source_url(
    company_id: int,
    source_url: SourceUrlCreate,
    db: AsyncSession = Depends(get_db)
):
    company = await crud_company.get_company(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return await crud_source_url.create_source_url(db, company_id, source_url)


@router.put("/{company_id}/urls/{url_id}", response_model=SourceUrlResponse)
async def update_source_url(
    company_id: int,
    url_id: int,
    source_url: SourceUrlUpdate,
    db: AsyncSession = Depends(get_db)
):
    updated = await crud_source_url.update_source_url(db, url_id, source_url)
    if not updated:
        raise HTTPException(status_code=404, detail="URL not found")
    return updated


@router.delete("/{company_id}/urls/{url_id}")
async def delete_source_url(
    company_id: int,
    url_id: int,
    db: AsyncSession = Depends(get_db)
):
    success = await crud_source_url.delete_source_url(db, url_id)
    if not success:
        raise HTTPException(status_code=404, detail="URL not found")
    return {"message": "URL deleted successfully"}
