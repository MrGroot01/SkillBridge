import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("postgresql://postgres:kiran@localhost:5432/skillbridge")   # ✅ FIX
    SECRET_KEY: str = os.getenv( "change-me-in-production-use-a-long-random-string")

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    MONITORING_TOKEN_EXPIRE_MINUTES: int = 60
    MONITORING_API_KEY: str = "sk-monitoring-hardcoded-key-12345"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()