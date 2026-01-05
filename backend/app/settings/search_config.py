"""Search configuration loader."""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from app.models.search_settings import CompanySearchSettings, SearchSettings


class SearchConfig:
    """Configuration for DuckDuckGo search and LLM filtering.

    Loads from database if available, otherwise falls back to YAML file.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        db_settings: Optional["SearchSettings"] = None,
        company_settings: Optional["CompanySearchSettings"] = None,
        company_name: Optional[str] = None,
    ):
        """
        Initialize search configuration.

        Args:
            config_path: Path to YAML config file. If None, uses default config path.
            db_settings: Global settings from database (takes precedence over YAML).
            company_settings: Company-specific settings from database.
            company_name: Company name for which to load settings.
        """
        self._db_settings = db_settings
        self._company_settings = company_settings
        self._company_name = company_name

        if config_path is None:
            # Default to config/search_config.yaml in the backend directory
            backend_dir = Path(__file__).parent.parent.parent
            config_path = backend_dir / "config" / "search_config.yaml"

        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file (fallback if DB not available)."""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = {}

    @property
    def search_keywords(self) -> List[str]:
        """Get search keywords list.

        Priority:
        1. Company-specific custom keywords (if set)
        2. Database global settings
        3. YAML file
        4. Default fallback
        """
        # Company-specific keywords take highest priority
        if self._company_settings and self._company_settings.custom_keywords:
            return self._company_settings.custom_keywords

        # Database settings
        if self._db_settings:
            return self._db_settings.search_keywords

        # YAML fallback
        return self._config.get("search_keywords", [
            "AI", "artificial intelligence", "generative AI", "machine learning",
            "DX", "digital transformation", "automation",
            "生成AI", "デジタル", "自動化", "事例"
        ])

    @property
    def default_region(self) -> Optional[str]:
        """Get default search region.

        Priority:
        1. Company-specific region (if set)
        2. Database global settings
        3. YAML file
        """
        # Company-specific region takes highest priority
        if self._company_settings and self._company_settings.region:
            return self._company_settings.region

        # Database settings
        if self._db_settings:
            return self._db_settings.default_region

        # YAML fallback
        region = self._config.get("default_region")
        return region if region else None

    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()


async def load_search_config_from_db(
    session,
    company_name: Optional[str] = None,
) -> SearchConfig:
    """
    Load search configuration from database.

    Args:
        session: Database session
        company_name: Optional company name to load company-specific settings

    Returns:
        SearchConfig instance with database settings loaded
    """
    from app.repositories.search_settings_repository import SearchSettingsRepository

    repo = SearchSettingsRepository(session)

    # Load global settings
    global_settings = await repo.get_global_settings()

    # Load company-specific settings if company_name is provided
    company_settings = None
    if company_name:
        company_settings = await repo.get_company_settings_by_name(company_name)

    return SearchConfig(
        db_settings=global_settings,
        company_settings=company_settings,
        company_name=company_name,
    )