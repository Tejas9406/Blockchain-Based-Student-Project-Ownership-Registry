from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings loaded from Environment variables or .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Core Application Settings
    PROJECT_NAME: str = "Student Project Ownership Registry API"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # Database Settings
    POSTGRES_USER: str = "registry_user"
    POSTGRES_PASSWORD: str = "registry_password_dev"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "project_registry_db"
    DATABASE_URL: str = "postgresql://registry_user:registry_password_dev@localhost:5432/project_registry_db"

    # CORS Settings
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    # JWT Authentication Settings
    JWT_SECRET_KEY: str = "dev_insecure_jwt_secret_key_change_in_production_sih2026_cyb05"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Blockchain & Web3.py Settings
    BLOCKCHAIN_RPC_URL: str = "http://127.0.0.1:8545"
    WEB3_PROVIDER_URI: str = "http://127.0.0.1:8545"  # Backward compatibility alias
    PROJECT_REGISTRY_CONTRACT_ADDRESS: str = ""
    BLOCKCHAIN_CHAIN_ID: int = 31337
    RELAYER_PRIVATE_KEY: str = ""
    BLOCKCHAIN_CONFIRMATION_BLOCKS: int = 1
    BLOCKCHAIN_TIMEOUT_SECONDS: int = 30

    # Local Artifact Storage Settings
    ARTIFACT_STORAGE_DIR: str = "storage/artifacts"

    # Decentralized IPFS Storage Settings (Kubo HTTP RPC API)
    IPFS_API_URL: str = "http://127.0.0.1:5001"
    IPFS_GATEWAY_URL: str = "http://127.0.0.1:8080"
    IPFS_TIMEOUT_SECONDS: int = 30
    STORAGE_BACKEND: str = "local"  # "local" or "ipfs"


settings = Settings()
