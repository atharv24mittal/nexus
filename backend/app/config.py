"""
config.py
---------
Central settings object, populated from environment variables (and a local
.env file in development). Nothing secret is ever hardcoded here.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- LLM provider ---
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.3-70b-versatile"

    # --- Agent behaviour ---
    MAX_REPAIR_ATTEMPTS: int = 5
    SKILL_LIBRARY_FEW_SHOT_K: int = 2

    # --- API / security ---
    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    RATE_LIMIT_SOLVE_MAX: int = 10
    RATE_LIMIT_SOLVE_WINDOW_SECONDS: int = 60
    RATE_LIMIT_DEFAULT_MAX: int = 60
    RATE_LIMIT_DEFAULT_WINDOW_SECONDS: int = 60
    MAX_REQUEST_BODY_BYTES: int = 20_000
    DISABLE_DOCS: bool = False
    ENVIRONMENT: str = "development"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()
