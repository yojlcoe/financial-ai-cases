from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://casestudy:casestudy123@db:5432/casestudy"

    # Ollama
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "gemma3:4b"

    # App
    app_name: str = "Case Study Agent"
    debug: bool = True

    # Timezone
    timezone: str = "Asia/Tokyo"

    # CORS
    cors_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
