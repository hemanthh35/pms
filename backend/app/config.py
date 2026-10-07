from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "sqlite:///./civicconnect.db"
    secret_key: str = "civicconnect-dev-secret-change-me"
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
        if self.environment.lower() in {"production", "prod"} and self.database_url.lower().startswith("sqlite"):
            raise ValueError("Production requires a persistent PostgreSQL DATABASE_URL; SQLite is disabled.")
        if self.environment.lower() in {"production", "prod"}:
            if self.secret_key == "civicconnect-dev-secret-change-me" or len(self.secret_key) < 32:
                raise ValueError("Production requires a generated SECRET_KEY of at least 32 characters.")
            if not self.frontend_origin.lower().startswith("https://"):
                raise ValueError("Production FRONTEND_ORIGIN must use HTTPS.")
        if bool(self.vapid_public_key) != bool(self.vapid_private_key):
            raise ValueError("VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY must be configured together.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
