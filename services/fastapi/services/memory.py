"""
Jarvis Control Tower — Memory Service
High-level memory operations using Qdrant for RAG.
"""
import logging
from datetime import datetime, timezone
from config import settings
from services.qdrant_service import qdrant_service

logger = logging.getLogger(__name__)


class MemoryService:
    """Provides high-level memory store/retrieve for the agent pipeline."""

    def save_interaction(
        self,
        user_id: str,
        message: str,
        intent: str,
        response: str,
    ) -> str:
        """Save a user interaction for future context retrieval."""
        combined = f"User: {message}\nJarvis: {response}"
        metadata = {
            "user_id": user_id,
            "intent": intent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return qdrant_service.store(
            collection=settings.COLLECTION_CONVERSATIONS,
            text=combined,
            metadata=metadata,
        )

    def get_relevant_context(
        self,
        user_id: str,
        query: str,
        top_k: int = 3,
    ) -> list[str]:
        """
        Retrieve relevant past interactions for RAG context injection.

        Returns:
            List of relevant text snippets.
        """
        results = qdrant_service.search(
            collection=settings.COLLECTION_CONVERSATIONS,
            query=query,
            top_k=top_k,
            filters={"user_id": user_id},
        )
        return [r["text"] for r in results if r["score"] > 0.5]

    def store_knowledge(self, text: str, metadata: dict = None) -> str:
        """Store a piece of knowledge in the knowledge base."""
        meta = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **(metadata or {}),
        }
        return qdrant_service.store(
            collection=settings.COLLECTION_KNOWLEDGE,
            text=text,
            metadata=meta,
        )

    def search_knowledge(self, query: str, top_k: int = 5) -> list[dict]:
        """Search the knowledge base."""
        return qdrant_service.search(
            collection=settings.COLLECTION_KNOWLEDGE,
            query=query,
            top_k=top_k,
        )

    def store_preference(self, user_id: str, text: str, category: str = "general") -> str:
        """Store a user preference."""
        metadata = {
            "user_id": user_id,
            "category": category,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return qdrant_service.store(
            collection=settings.COLLECTION_USER_PREFS,
            text=text,
            metadata=metadata,
        )


# Singleton instance
memory_service = MemoryService()
