"""Tests for configuration loading."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import Settings


class TestSettings:
    def test_default_urls(self):
        s = Settings()
        assert "11434" in s.OLLAMA_URL
        assert "6333" in s.QDRANT_URL
        assert "5678" in s.N8N_URL

    def test_default_model(self):
        s = Settings()
        assert s.LLM_MODEL == "llama3.2:3b"
        assert s.LLM_TIMEOUT == 120

    def test_collections(self):
        s = Settings()
        assert s.COLLECTION_CONVERSATIONS == "conversations"
        assert s.COLLECTION_KNOWLEDGE == "knowledge"
        assert s.COLLECTION_USER_PREFS == "user_preferences"

    def test_embedding_config(self):
        s = Settings()
        assert "bge" in s.EMBEDDING_MODEL.lower()
        assert s.EMBEDDING_DIM == 384
