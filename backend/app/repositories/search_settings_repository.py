"""Repository for search settings."""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company import Company
from app.models.search_settings import CompanySearchSettings, SearchSettings


class SearchSettingsRepository:
    """Repository for managing search settings."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_global_settings(self) -> Optional[SearchSettings]:
        """Get global search settings."""
        result = await self.session.execute(select(SearchSettings).limit(1))
        return result.scalar_one_or_none()

    async def create_or_update_global_settings(
        self,
        default_region: Optional[str] = None,
    ) -> SearchSettings:
        """Create or update global search settings."""
        existing = await self.get_global_settings()

        if existing:
            # Update existing
            existing.default_region = default_region
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            # Create new
            settings = SearchSettings(
                default_region=default_region,
            )
            self.session.add(settings)
            await self.session.commit()
            await self.session.refresh(settings)
            return settings

    async def get_company_by_name(self, company_name: str) -> Optional[Company]:
        """Get company by name."""
        result = await self.session.execute(
            select(Company).where(Company.name == company_name)
        )
        return result.scalar_one_or_none()

    async def get_company_settings(self, company_id: int) -> Optional[CompanySearchSettings]:
        """Get search settings for a specific company by ID."""
        result = await self.session.execute(
            select(CompanySearchSettings).where(CompanySearchSettings.company_id == company_id)
        )
        return result.scalar_one_or_none()

    async def get_company_settings_by_name(self, company_name: str) -> Optional[CompanySearchSettings]:
        """Get search settings for a specific company by name."""
        company = await self.get_company_by_name(company_name)
        if not company:
            return None

        # Load settings with company relationship
        result = await self.session.execute(
            select(CompanySearchSettings)
            .options(selectinload(CompanySearchSettings.company))
            .where(CompanySearchSettings.company_id == company.id)
        )
        return result.scalar_one_or_none()

    async def create_or_update_company_settings(
        self,
        company_name: str,
        region: Optional[str] = None,
        custom_keywords: Optional[list[str]] = None,
    ) -> CompanySearchSettings:
        """Create or update company-specific search settings."""
        # Get company by name
        company = await self.get_company_by_name(company_name)
        if not company:
            raise ValueError(f"Company '{company_name}' not found")

        # Check if settings already exist
        existing = await self.get_company_settings(company.id)

        if existing:
            # Update existing
            if region is not None:
                existing.region = region
            if custom_keywords is not None:
                existing.custom_keywords = custom_keywords
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        else:
            # Create new
            settings = CompanySearchSettings(
                company_id=company.id,
                region=region,
                custom_keywords=custom_keywords,
            )
            self.session.add(settings)
            await self.session.commit()
            await self.session.refresh(settings)
            return settings

    async def delete_company_settings(self, company_name: str) -> bool:
        """Delete company-specific search settings."""
        company = await self.get_company_by_name(company_name)
        if not company:
            return False

        existing = await self.get_company_settings(company.id)
        if existing:
            await self.session.delete(existing)
            await self.session.commit()
            return True
        return False