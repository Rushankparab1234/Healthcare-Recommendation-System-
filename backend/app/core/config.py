import secrets
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = Field(
        default_factory=lambda: f"sqlite:///{REPOSITORY_ROOT / 'healthwise.db'}"
    )
    jwt_secret_key: SecretStr | None = None
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 60
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @model_validator(mode="after")
    def validate_security_settings(self):
        production = self.app_env.strip().casefold() in {"prod", "production"}
        secret = self.jwt_secret_key.get_secret_value() if self.jwt_secret_key else ""
        if production:
            if len(secret.strip()) < 32:
                raise ValueError("Production requires JWT_SECRET_KEY with at least 32 characters")
            origins = self.allowed_cors_origins
            parsed_origins = [urlparse(origin) for origin in origins]
            if not origins or any(
                parsed.scheme != "https"
                or not parsed.netloc
                or parsed.path
                or parsed.query
                or parsed.fragment
                or parsed.username
                or parsed.password
                for parsed in parsed_origins
            ):
                raise ValueError("Production CORS_ORIGINS must contain explicit HTTPS origins")
        elif not secret:
            object.__setattr__(self, "jwt_secret_key", SecretStr(secrets.token_urlsafe(48)))
        return self

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
