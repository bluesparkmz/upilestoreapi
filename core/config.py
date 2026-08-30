from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "UpileStore"
    environment: str = "development"
    database_url: str = "sqlite:///./upilestore.db"

    @property
    def sync_database_url(self) -> str:
        """Garante que postgres:// seja convertido para postgresql:// para o SQLAlchemy."""
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    cors_origins: str = "http://localhost:3000,https://upile-store-moz.vercel.app"

    # Storage & Upload Settings
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10
    storage_provider: str = "local"  # "local" or "cloudflare"

    # Cloudflare R2 Settings (for future phase)
    r2_account_id: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_bucket_name: str | None = None
    r2_public_domain: str | None = None

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
