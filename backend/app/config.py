"""Centralised settings loaded from environment variables."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_key: str
    supabase_jwt_secret: str
    twelve_data_api_key: str = ""
    alpha_vantage_api_key: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    environment: str = "development"
    cors_origins: str = "http://localhost:3000"
    secret_key: str = "changeme"
    model_path: str = "./models"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
