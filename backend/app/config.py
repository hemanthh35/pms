from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./civicconnect.db"
    secret_key: str = "civicconnect-dev-secret-change-me"
    access_token_expire_minutes: int = 1440
    frontend_origin: str = "http://localhost:5173"
    uploads_dir: str = "uploads"
    frontend_dist_dir: str = ""
    vapid_public_key: str = "BL3eSRDC1_mBQ7EkbLpIMz4UWzP0lPZQRjXGNQEQhsU49oRycHRUZgYT9b2GNUxQV5Aw87XAOzoH5klbLdogkEU"
    vapid_private_key: str = "T9EReCJ4LyH8IpHS0bIROiotugXcl1w3UUP9J-6-7aE"
    vapid_subject: str = "mailto:admin@civicconnect.app"
    sla_hours: int = 48

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
