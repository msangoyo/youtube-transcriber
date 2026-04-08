from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    PROJECT_NAME: str = "YouTube AI Transcriber"
    API_V1_STR: str = "/api/v1"
    # Comma-separated origins, e.g. "http://localhost:5173,https://yourdomain.com"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(env_file=".env")

    @field_validator("GOOGLE_API_KEY")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("GOOGLE_API_KEY is not configured in .env")
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
