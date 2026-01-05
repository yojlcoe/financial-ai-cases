from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class JobHistoryBase(BaseModel):
    job_type: str
    status: str


class JobHistoryResponse(JobHistoryBase):
    id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_companies: int
    processed_companies: int
    total_articles: int
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class JobHistoryListResponse(BaseModel):
    items: List[JobHistoryResponse]
    total: int


class JobStartRequest(BaseModel):
    job_type: str = "manual"  # manual, daily, weekly


class JobStartResponse(BaseModel):
    job_id: int
    message: str
