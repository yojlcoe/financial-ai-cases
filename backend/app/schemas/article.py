from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List


class ArticleBase(BaseModel):
    title: str
    url: str
    content: Optional[str] = None
    summary: Optional[str] = None
    published_date: Optional[date] = None
    category: Optional[str] = None
    business_area: Optional[str] = None
    tags: Optional[str] = None
    is_inappropriate: bool = False
    inappropriate_reason: Optional[str] = None
    is_reviewed: bool = False


class ArticleCreate(ArticleBase):
    company_id: int


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    published_date: Optional[date] = None
    category: Optional[str] = None
    business_area: Optional[str] = None
    tags: Optional[str] = None
    is_inappropriate: Optional[bool] = None
    inappropriate_reason: Optional[str] = None
    is_reviewed: Optional[bool] = None


class ArticleResponse(ArticleBase):
    id: int
    company_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    items: List[ArticleResponse]
    total: int


class ArticleAnalysisStats(BaseModel):
    total: int
    analyzed: int
    coefficient: float


class ArticleAnalysisGroup(BaseModel):
    label: str
    count: int


class ArticleAnalysisTimeSeries(BaseModel):
    period: str
    count: int


class ArticleAnalysisCoefficients(BaseModel):
    total: int
    by_category: List[ArticleAnalysisGroup]
    by_business_area: List[ArticleAnalysisGroup]
    by_region: List[ArticleAnalysisGroup]
    by_month: List[ArticleAnalysisTimeSeries]
