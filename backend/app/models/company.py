from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    name_en = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    source_urls = relationship("SourceUrl", back_populates="company", cascade="all, delete-orphan")
    articles = relationship("Article", back_populates="company", cascade="all, delete-orphan")
    search_settings = relationship("CompanySearchSettings", back_populates="company", cascade="all, delete-orphan", uselist=False)
