import json
from typing import List, Union, Optional
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App Information
    PROJECT_NAME: str = "InsightFlow Analytics API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API Versioning
    API_V1_STR: str = "/api/v1"
    
    # CORS - Strict Origins & Localhost Pattern
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3005",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:4173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3005",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:4173",
        "http://127.0.0.1:8080"
    ]
    CORS_ALLOW_ORIGIN_REGEX: Optional[str] = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v_trimmed = v.strip()
            if v_trimmed == "*":
                return ["*"]
            if v_trimmed.startswith("[") and v_trimmed.endswith("]"):
                try:
                    return json.loads(v_trimmed)
                except Exception:
                    pass
            return [i.strip() for i in v_trimmed.split(",") if i.strip()]
        return v

    # Supabase Configuration
    SUPABASE_URL: str = Field(default="", alias="VITE_SUPABASE_URL")
    SUPABASE_KEY: str = Field(default="", alias="VITE_SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default="", alias="SUPABASE_SERVICE_ROLE_KEY")
    SUPABASE_JWT_SECRET: str = Field(default="", alias="SUPABASE_JWT_SECRET")
    DATASET_STORAGE_BUCKET: str = "datasets"
    MAX_UPLOAD_SIZE_MB: int = 100

    # LLM Provider Configuration
    LLM_PROVIDER: str = Field(default="nvidia", alias="LLM_PROVIDER")  # "nvidia" or "gemini"

    # NVIDIA API Configuration
    NVIDIA_API_KEY: str = Field(default="", alias="NVIDIA_API_KEY")
    NVIDIA_BASE_URL: str = Field(default="https://integrate.api.nvidia.com/v1", alias="NVIDIA_BASE_URL")
    NVIDIA_DEFAULT_MODEL: str = Field(default="meta/llama-3.3-70b-instruct", alias="NVIDIA_DEFAULT_MODEL")
    NVIDIA_TEMPERATURE: float = 0.2
    NVIDIA_MAX_TOKENS: int = 2048
    NVIDIA_TIMEOUT_SECONDS: float = 45.0
    NVIDIA_MAX_RETRIES: int = 3
    NVIDIA_RETRY_BACKOFF_FACTOR: float = 1.5

    # Google Gemini Configuration
    GEMINI_API_KEY: str = Field(default="", alias="GEMINI_API_KEY")

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # "json" or "text"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../Business-data-analyst/.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
