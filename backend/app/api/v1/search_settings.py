"""API endpoints for search settings management."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.repositories.search_settings_repository import SearchSettingsRepository
from app.utils.region_keywords import get_keywords_by_region

router = APIRouter(prefix="/search-settings", tags=["search-settings"])


# Pydantic models for request/response
class SearchSettingsResponse(BaseModel):
    """Global search settings response."""

    id: int
    default_region: Optional[str]

    class Config:
        from_attributes = True


class SearchSettingsUpdate(BaseModel):
    """Global search settings update request."""

    default_region: Optional[str] = Field(default=None, max_length=10)


class CompanySearchSettingsResponse(BaseModel):
    """Company-specific search settings response."""

    id: int
    company_id: int
    company_name: str
    region: Optional[str]
    custom_keywords: Optional[List[str]]

    class Config:
        from_attributes = True


class CompanySearchSettingsUpdate(BaseModel):
    """Company-specific search settings update request."""

    region: Optional[str] = Field(default=None, max_length=10)
    custom_keywords: Optional[List[str]] = None


@router.get("/global", response_model=SearchSettingsResponse)
async def get_global_settings(db: AsyncSession = Depends(get_db)):
    """Get global search settings."""
    repo = SearchSettingsRepository(db)
    settings = await repo.get_global_settings()

    if not settings:
        # Return default settings
        return SearchSettingsResponse(
            id=0,
            default_region=None,
        )

    return settings


@router.put("/global", response_model=SearchSettingsResponse)
async def update_global_settings(
    settings_update: SearchSettingsUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Create or update global search settings."""
    repo = SearchSettingsRepository(db)

    settings = await repo.create_or_update_global_settings(
        default_region=settings_update.default_region,
    )

    return settings


@router.get("/company/{company_name}", response_model=CompanySearchSettingsResponse)
async def get_company_settings(
    company_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Get company-specific search settings."""
    repo = SearchSettingsRepository(db)
    settings = await repo.get_company_settings_by_name(company_name)

    if not settings:
        raise HTTPException(
            status_code=404,
            detail=f"Settings for company '{company_name}' not found",
        )

    # Manually construct response with company name
    return CompanySearchSettingsResponse(
        id=settings.id,
        company_id=settings.company_id,
        company_name=settings.company.name,
        region=settings.region,
        custom_keywords=settings.custom_keywords,
    )


@router.put("/company/{company_name}", response_model=CompanySearchSettingsResponse)
async def update_company_settings(
    company_name: str,
    settings_update: CompanySearchSettingsUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Create or update company-specific search settings."""
    repo = SearchSettingsRepository(db)

    try:
        settings = await repo.create_or_update_company_settings(
            company_name=company_name,
            region=settings_update.region,
            custom_keywords=settings_update.custom_keywords,
        )

        # Refresh to load relationship
        await db.refresh(settings, ["company"])

        return CompanySearchSettingsResponse(
            id=settings.id,
            company_id=settings.company_id,
            company_name=settings.company.name,
            region=settings.region,
            custom_keywords=settings.custom_keywords,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/company/{company_name}")
async def delete_company_settings(
    company_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete company-specific search settings."""
    repo = SearchSettingsRepository(db)

    deleted = await repo.delete_company_settings(company_name)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Settings for company '{company_name}' not found",
        )

    return {"message": f"Settings for company '{company_name}' deleted successfully"}


@router.get("/keywords/{region}")
async def get_region_keywords(region: str):
    """Get search keywords for a specific region."""
    keywords = get_keywords_by_region(region if region != "global" else None)
    return {"region": region, "keywords": keywords}