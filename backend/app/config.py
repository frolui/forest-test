from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_DSN: str = "postgresql+psycopg://airflow:airflow@postgres:5432/airflow"
    JWT_SECRET: str = "change-me"
    JWT_EXPIRES_MIN: int = 60
    CORS_ORIGINS: list[str] = ["http://localhost:8081"]
    COOKIE_SECURE: bool = False

settings = Settings()
