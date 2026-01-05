"""Search settings database models."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.company import Company


class SearchSettings(Base):
    """Global search settings."""

    __tablename__ = "global_search_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Default region (null = global)
    # Keywords are automatically determined by region in code
    default_region: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class CompanySearchSettings(Base):
    """Per-company search settings (overrides global settings)."""

    __tablename__ = "company_search_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign key to companies table
    company_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    # Relationship to company
    company: Mapped["Company"] = relationship("Company", back_populates="search_settings")

    # Region override for this company
    region: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Optional: custom keywords for this company
    custom_keywords: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )