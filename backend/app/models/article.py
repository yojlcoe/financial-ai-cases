from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date, Boolean, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    url = Column(Text, nullable=False, unique=True)
    published_date = Column(Date, nullable=True)
    category = Column(String(100), nullable=True)
    business_area = Column(String(100), nullable=True)
    tags = Column(String(500), nullable=True)  # カンマ区切り
    is_inappropriate = Column(Boolean, default=False, nullable=False)
    inappropriate_reason = Column(Text, nullable=True)  # 不適切な理由
    is_reviewed = Column(Boolean, default=False, nullable=False)  # 人間による確認済みフラグ
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="articles")
