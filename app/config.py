from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        extra="ignore",
        protected_namespaces=("settings_",),
    )
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_jwt_secret: str = ""
    twelve_data_api_key: str = ""
    alpha_vantage_api_key: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    environment: str = "production"
    cors_origins: str = "http://localhost:3000"
    secret_key: str = "changeme"
    model_path: str = "/tmp/models"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
