from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class SourceUrlBase(BaseModel):
    url: str
    url_type: str = "press_release"
    is_active: bool = True


class SourceUrlCreate(SourceUrlBase):
    pass


class SourceUrlUpdate(BaseModel):
    url: Optional[str] = None
    url_type: Optional[str] = None
    is_active: Optional[bool] = None


class SourceUrlResponse(SourceUrlBase):
    id: int
    company_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CompanyBase(BaseModel):
    name: str
    name_en: Optional[str] = None
    country: Optional[str] = None
    is_active: bool = True


class CompanyCreate(CompanyBase):
    source_urls: Optional[List[SourceUrlCreate]] = []


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    name_en: Optional[str] = None
    country: Optional[str] = None
    is_active: Optional[bool] = None


class CompanyResponse(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    source_urls: List[SourceUrlResponse] = []

    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    items: List[CompanyResponse]
    total: int
