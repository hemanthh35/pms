from functools import lru_cache
from secrets import token_urlsafe

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "sqlite:///./civicconnect.db"
    secret_key: str = ""
    access_token_expire_minutes: int = 1440
    frontend_origin: str = "http://localhost:5173"
    uploads_dir: str = "uploads"
    frontend_dist_dir: str = ""
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:admin@civicconnect.app"
    sla_hours: int = 48

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def require_persistent_production_database(self):
        if not self.secret_key:
            if self.environment.lower() in {"production", "prod"}:
                raise ValueError("Production requires SECRET_KEY to be set.")
            self.secret_key = token_urlsafe(32)
        if self.environment.lower() in {"production", "prod"} and self.database_url.lower().startswith("sqlite"):
            raise ValueError("Production requires a persistent PostgreSQL DATABASE_URL; SQLite is disabled.")
        if self.environment.lower() in {"production", "prod"}:
            if len(self.secret_key) < 32:
                raise ValueError("Production requires a generated SECRET_KEY of at least 32 characters.")
            if not self.frontend_origin.lower().startswith("https://"):
                raise ValueError("Production FRONTEND_ORIGIN must use HTTPS.")
        if bool(self.vapid_public_key) != bool(self.vapid_private_key):
            raise ValueError("VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY must be configured together.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
