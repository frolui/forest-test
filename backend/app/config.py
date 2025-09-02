import os
import json
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_DSN: str = os.getenv("DB_DSN", "postgresql+psycopg://airflow:airflow@postgres:5432/airflow")
    JWT_SECRET: str = "change-me"
    JWT_EXPIRES_MIN: int = 60
    CORS_ORIGINS: list[str] = json.loads(os.getenv("CORS_ORIGINS", '["http://localhost:8081"]'))
    COOKIE_SECURE: bool = False

settings = Settings()
