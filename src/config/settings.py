"""
Configuration management for chatPDF application.

This module handles all configuration settings using Pydantic for validation
and environment variable loading.
"""

import os
from typing import List, Optional
from pathlib import Path

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden by environment variables.
    """
    
    # =========================================================================
    # Application Settings
    # =========================================================================
    APP_NAME: str = "chatPDF"
    APP_ENV: str = Field(default="development", description="Application environment")
    DEBUG: bool = Field(default=False, description="Debug mode")
    SECRET_KEY: str = Field(default="change-this-secret-key", description="Secret key for encryption")
    
    # =========================================================================
    # OpenAI Configuration
    # =========================================================================
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    OPENAI_ORG_ID: Optional[str] = Field(default=None, description="OpenAI organization ID")
    
    # =========================================================================
    # Ollama Configuration (Local LLM)
    # =========================================================================
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL"
    )
    OLLAMA_TIMEOUT: int = Field(default=120, description="Ollama request timeout in seconds")
    
    # =========================================================================
    # HuggingFace Configuration
    # =========================================================================
    HF_API_KEY: Optional[str] = Field(default=None, description="HuggingFace API token")
    HF_CACHE_DIR: str = Field(
        default="./data/models/huggingface",
        description="HuggingFace model cache directory"
    )
    
    # =========================================================================
    # File Storage Configuration
    # =========================================================================
    UPLOAD_FOLDER: str = Field(default="./data/uploads", description="Document upload directory")
    MAX_FILE_SIZE: int = Field(default=50, description="Maximum file size in MB")
    ALLOWED_EXTENSIONS: str = Field(
        default="pdf,docx,txt,md",
        description="Allowed file extensions (comma-separated)"
    )
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get allowed extensions as a list."""
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]
    
    # =========================================================================
    # Vector Store Configuration
    # =========================================================================
    VECTOR_STORE_TYPE: str = Field(default="faiss", description="Vector store type")
    VECTOR_STORE_PATH: str = Field(
        default="./data/vector_stores",
        description="Vector store data directory"
    )
    EMBEDDING_MODEL: str = Field(
        default="text-embedding-ada-002",
        description="Default embedding model"
    )
    EMBEDDING_DIMENSION: int = Field(default=1536, description="Embedding dimension")
    
    # =========================================================================
    # RAG Pipeline Configuration
    # =========================================================================
    CHUNK_SIZE: int = Field(default=1000, description="Text chunk size in characters")
    CHUNK_OVERLAP: int = Field(default=200, description="Overlap between chunks")
    TOP_K_RETRIEVAL: int = Field(default=10, description="Number of chunks to retrieve")
    USE_RERANKING: bool = Field(default=True, description="Enable re-ranking")
    USE_COMPRESSION: bool = Field(default=False, description="Enable contextual compression")
    
    # Hybrid Search Weights
    SEMANTIC_SEARCH_WEIGHT: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Weight for semantic search"
    )
    KEYWORD_SEARCH_WEIGHT: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for keyword search"
    )
    
    @validator("KEYWORD_SEARCH_WEIGHT")
    def validate_search_weights(cls, v, values):
        """Ensure search weights sum to 1.0."""
        if "SEMANTIC_SEARCH_WEIGHT" in values:
            semantic_weight = values["SEMANTIC_SEARCH_WEIGHT"]
            if abs(semantic_weight + v - 1.0) > 0.01:
                # Auto-adjust keyword weight
                return 1.0 - semantic_weight
        return v
    
    # =========================================================================
    # LLM Default Configuration
    # =========================================================================
    DEFAULT_MODEL: str = Field(default="gpt-3.5-turbo", description="Default LLM model")
    DEFAULT_TEMPERATURE: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="LLM temperature"
    )
    DEFAULT_MAX_TOKENS: int = Field(default=500, description="Maximum tokens in response")
    DEFAULT_TOP_P: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p sampling")
    DEFAULT_FREQUENCY_PENALTY: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Frequency penalty"
    )
    DEFAULT_PRESENCE_PENALTY: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Presence penalty"
    )
    
    # =========================================================================
    # Database Configuration
    # =========================================================================
    DATABASE_URL: str = Field(
        default="sqlite:///./data/chatpdf.db",
        description="Database connection URL"
    )
    
    # =========================================================================
    # Logging Configuration
    # =========================================================================
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE: str = Field(default="./logs/app.log", description="Log file path")
    LOG_MAX_BYTES: int = Field(default=10485760, description="Max log file size (10MB)")
    LOG_BACKUP_COUNT: int = Field(default=5, description="Number of log backups to keep")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )
    
    # =========================================================================
    # Cache Configuration
    # =========================================================================
    ENABLE_CACHE: bool = Field(default=True, description="Enable caching")
    CACHE_TYPE: str = Field(default="memory", description="Cache type (memory or redis)")
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    CACHE_TTL: int = Field(default=3600, description="Cache TTL in seconds")
    
    # =========================================================================
    # Security & Rate Limiting
    # =========================================================================
    JWT_SECRET_KEY: str = Field(default="change-this-jwt-secret", description="JWT secret key")
    JWT_ACCESS_TOKEN_EXPIRES: int = Field(default=3600, description="JWT expiry (seconds)")
    JWT_REFRESH_TOKEN_EXPIRES: int = Field(default=2592000, description="Refresh token expiry")
    RATE_LIMIT: int = Field(default=100, description="Rate limit (requests per minute)")
    
    # =========================================================================
    # CORS Configuration
    # =========================================================================
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Allowed CORS origins (comma-separated)"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # =========================================================================
    # Model-Specific Configuration
    # =========================================================================
    OLLAMA_MODELS: str = Field(
        default="llama3:8b,mistral:7b",
        description="Ollama models to download (comma-separated)"
    )
    SENTENCE_TRANSFORMER_MODEL: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence transformer model"
    )
    CROSS_ENCODER_MODEL: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-12-v2",
        description="Cross-encoder model for re-ranking"
    )
    
    # =========================================================================
    # Monitoring & Analytics
    # =========================================================================
    ENABLE_ANALYTICS: bool = Field(default=True, description="Enable analytics tracking")
    TRACK_TOKEN_USAGE: bool = Field(default=True, description="Track token usage")
    TRACK_COSTS: bool = Field(default=True, description="Track API costs")
    
    # =========================================================================
    # Development Settings
    # =========================================================================
    USE_MOCK_SERVICES: bool = Field(
        default=False,
        description="Use mock services (for testing)"
    )
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from environment
    
    def create_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.UPLOAD_FOLDER,
            self.VECTOR_STORE_PATH,
            self.HF_CACHE_DIR,
            Path(self.LOG_FILE).parent,
            Path(self.DATABASE_URL.replace("sqlite:///", "")).parent,
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def validate_settings(self) -> bool:
        """
        Validate settings and return True if valid.
        
        Raises:
            ValueError: If settings are invalid.
        """
        # Check if at least one LLM provider is configured
        has_openai = bool(self.OPENAI_API_KEY)
        has_ollama = self.OLLAMA_BASE_URL is not None
        
        if not (has_openai or has_ollama):
            raise ValueError(
                "At least one LLM provider must be configured "
                "(OpenAI API key or Ollama URL)"
            )
        
        # Validate file size
        if self.MAX_FILE_SIZE <= 0:
            raise ValueError("MAX_FILE_SIZE must be positive")
        
        # Validate chunk settings
        if self.CHUNK_SIZE <= self.CHUNK_OVERLAP:
            raise ValueError("CHUNK_SIZE must be greater than CHUNK_OVERLAP")
        
        return True
    
    def get_max_file_size_bytes(self) -> int:
        """Get maximum file size in bytes."""
        return self.MAX_FILE_SIZE * 1024 * 1024
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.APP_ENV.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.APP_ENV.lower() == "development"


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the singleton settings instance.
    
    Returns:
        Settings: Application settings instance.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.create_directories()
        _settings.validate_settings()
    return _settings


# Export for convenience
settings = get_settings()
