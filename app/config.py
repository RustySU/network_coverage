"""Application configuration settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/mobile_coverage"
    )

    # Environment
    environment: str = "development"
    debug: bool = True

    # API
    api_title: str = "Mobile Coverage API"
    api_version: str = "0.1.0"
    api_description: str = "API for mobile coverage data in France"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
