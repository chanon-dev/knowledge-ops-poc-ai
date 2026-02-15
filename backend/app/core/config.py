from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, EmailStr, validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "KnowledgeOps"
    ENVIRONMENT: str = "local"  # local, staging, production

    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}:{values.get('POSTGRES_PORT')}/{values.get('POSTGRES_DB')}"

    # Redis
    REDIS_URL: str

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Auth
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days (for dev)

    # Keycloak
    KEYCLOAK_URL: str
    KEYCLOAK_REALM: str = "the-expert"
    KEYCLOAK_CLIENT_ID: str = "the-expert-api"
    KEYCLOAK_PUBLIC_KEY: Optional[str] = None

    # Rate Limiting (daily query quotas per tenant)
    RATE_LIMIT_FREE: int = 50
    RATE_LIMIT_PRO: int = 500
    RATE_LIMIT_ENTERPRISE: int = 0  # 0 = unlimited

    # Qdrant
    QDRANT_URL: str

    # Ollama
    OLLAMA_URL: str
    OLLAMA_MODEL: str

    # Training / ML
    TRAINING_DEFAULT_BASE_MODEL: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    TRAINING_DEFAULT_EPOCHS: int = 3
    TRAINING_DEFAULT_LR: float = 2e-4
    TRAINING_DEFAULT_BATCH_SIZE: int = 4
    TRAINING_MIN_SAMPLES: int = 10
    TRAINING_OUTPUT_DIR: str = "/tmp/lora_models"
    TRAINING_DEPLOY_TO_OLLAMA: bool = True
    TRAINING_SYSTEM_PROMPT: str = "You are an enterprise AI assistant. Answer questions accurately based on the provided context and knowledge base."

    # Logging
    LOG_LEVEL: str = "INFO"

settings = Settings()
