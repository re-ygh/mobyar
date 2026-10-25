"""
Application configuration using environment variables.

We keep this minimal and explicit for an educational project.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    # API
    api_v1_prefix: str = "/api/v1"

    # Database
    # Example: postgresql+psycopg2://mobyar:mobyar@db:5432/mobyar
    database_url: str = "postgresql+psycopg2://mobyar:mobyar@db:5432/mobyar"

    # JWT
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # CORS
    cors_origins: List[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """
        Allow either:
        - a JSON array string: '["http://localhost:5173"]'
        - a comma separated string: "http://localhost:5173,http://127.0.0.1:5173"
        - a python list
        """
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                # JSON style
                import json
                return json.loads(v)
            return [item.strip() for item in v.split(",") if item.strip()]
        return ["http://localhost:5173"]


settings = Settings()
