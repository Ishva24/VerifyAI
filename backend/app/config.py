from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "VerifyAI"
    environment: str = "development"
    database_url: str = "sqlite:///./verifyai.db"
    jwt_secret: str = "super-secret-key-change-me"
    jwt_algorithm: str = "HS256"
    ai_service_url: str = "http://localhost:8001"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
