from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "SIH26104 Voice Cloning Detection Backend"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database: SQLite is the zero-config local/demo default. Override with MySQL/Postgres in .env.
    DATABASE_URL: str = "sqlite+aiosqlite:///./voice_shield.db"

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production-min-32-chars-long!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 120

    # ML Service (Member 1)
    ML_SERVICE_URL: str = "http://127.0.0.1:8001/predict"
    MOCK_ML_SERVICE: bool = False
    ML_REQUEST_TIMEOUT_SECONDS: float = 8.0

    # Risk Engine Thresholds
    RISK_THRESHOLD_LOW: float = 30.0
    RISK_THRESHOLD_HIGH: float = 70.0
    CONFIDENCE_THRESHOLD: float = 0.65

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, list):
            return v
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
