"""Application configuration management."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, MongoDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # QuickSpin API Configuration
    quickspin_api_url: str = Field(
        default="https://api.quickspin.io",
        description="QuickSpin API base URL",
    )
    quickspin_auth_url: str = Field(
        default="https://auth.quickspin.io",
        description="QuickSpin authentication service URL",
    )

    # AI Services
    groq_api_key: str = Field(
        ...,
        description="Groq API key for LLM inference",
    )
    groq_model: str = Field(
        default="mixtral-8x7b-32768",
        description="Groq model to use for inference",
    )

    # Database
    mongodb_uri: MongoDsn = Field(
        default="mongodb://localhost:27017/quickspin_ai",
        description="MongoDB connection URI",
    )
    mongodb_database: str = Field(
        default="quickspin_ai",
        description="MongoDB database name",
    )

    # Vector Store
    chroma_persist_dir: str = Field(
        default="/data/chroma",
        description="ChromaDB persistence directory",
    )
    chroma_collection_name: str = Field(
        default="quickspin_knowledge",
        description="ChromaDB collection name for knowledge base",
    )

    # Security
    jwt_secret_key: str = Field(
        ...,
        description="Secret key for JWT token validation",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm",
    )

    # Application
    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    api_prefix: str = Field(
        default="/api/v1",
        description="API route prefix",
    )

    # Server
    host: str = Field(
        default="0.0.0.0",
        description="Server host",
    )
    port: int = Field(
        default=8000,
        description="Server port",
    )
    workers: int = Field(
        default=2,
        description="Number of Uvicorn workers",
    )

    # Kubernetes
    kubeconfig_path: str = Field(
        default="~/.kube/config",
        description="Path to kubeconfig file",
    )
    k8s_in_cluster: bool = Field(
        default=False,
        description="Whether running inside Kubernetes cluster",
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns:
        Settings instance loaded from environment variables.
    """
    return Settings()
