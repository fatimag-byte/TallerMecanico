from functools import lru_cache
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    app_env: str = "development"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5176,http://127.0.0.1:5176"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url", mode="before")
    @classmethod
    def use_pymysql_driver(cls, value: str) -> str:
        """Accept Railway's ``mysql://`` URL while keeping SQLAlchemy explicit."""
        return value.replace("mysql://", "mysql+pymysql://", 1) if value.startswith("mysql://") else value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.app_env.casefold() == "production":
            if len(self.jwt_secret) < 32:
                raise ValueError("JWT_SECRET debe tener al menos 32 caracteres en producción.")
            if not self.cors_origin_list or any("localhost" in origin or "127.0.0.1" in origin for origin in self.cors_origin_list):
                raise ValueError("CORS_ORIGINS debe contener únicamente los orígenes públicos autorizados en producción.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
