from sqlalchemy import Column, Integer, String, Text, DateTime
from app.core.database import Base


class JobHistory(Base):
    __tablename__ = "job_histories"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String(50), nullable=False)  # daily, weekly, manual
    status = Column(String(50), nullable=False)  # running, completed, failed
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_companies = Column(Integer, default=0)
    processed_companies = Column(Integer, default=0)
    total_articles = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
