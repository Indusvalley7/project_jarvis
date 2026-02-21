"""
Jarvis Control Tower — Configuration
Centralizes all environment variables and settings.
"""
import os


class Settings:
    """Application settings loaded from environment variables."""

    # Service URLs
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    N8N_URL: str = os.getenv("N8N_URL", "http://localhost:5678")

    # Model config
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama3.2:3b")
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "120"))

    # Qdrant collections
    COLLECTION_CONVERSATIONS: str = "conversations"
    COLLECTION_KNOWLEDGE: str = "knowledge"
    COLLECTION_USER_PREFS: str = "user_preferences"

    # Embedding config
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    EMBEDDING_DIM: int = 384  # Dimension for bge-small-en-v1.5

    # n8n
    N8N_API_KEY: str = os.getenv("N8N_API_KEY", "")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://jarvis:jarvis_secret@localhost:5432/jarvis_db",
    )


settings = Settings()


