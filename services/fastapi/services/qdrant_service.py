"""
Jarvis Control Tower — Qdrant Vector Store Client
Manages collections and vector operations.
"""
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)
from fastembed import TextEmbedding
from config import settings
import uuid

logger = logging.getLogger(__name__)


class QdrantService:
    """Manages Qdrant vector database operations with auto-embedding."""

    def __init__(self):
        self.client = QdrantClient(url=settings.QDRANT_URL)
        self._embedder = None

    @property
    def embedder(self) -> TextEmbedding:
        """Lazy-load the embedding model."""
        if self._embedder is None:
            logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
            self._embedder = TextEmbedding(model_name=settings.EMBEDDING_MODEL)
        return self._embedder

    def ensure_collections(self):
        """Create all required collections if they don't exist."""
        collections = [
            settings.COLLECTION_CONVERSATIONS,
            settings.COLLECTION_KNOWLEDGE,
            settings.COLLECTION_USER_PREFS,
        ]
        existing = {c.name for c in self.client.get_collections().collections}

        for name in collections:
            if name not in existing:
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=settings.EMBEDDING_DIM,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info("Created Qdrant collection: %s", name)
            else:
                logger.info("Qdrant collection already exists: %s", name)

    def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text."""
        embeddings = list(self.embedder.embed([text]))
        return embeddings[0].tolist()

    def store(
        self,
        collection: str,
        text: str,
        metadata: dict = None,
    ) -> str:
        """
        Store text with auto-generated embedding.

        Returns:
            The point ID as a string.
        """
        vector = self.embed_text(text)
        point_id = str(uuid.uuid4())
        payload = {"text": text, **(metadata or {})}

        self.client.upsert(
            collection_name=collection,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )
        logger.info("Stored point %s in collection %s", point_id, collection)
        return point_id

    def search(
        self,
        collection: str,
        query: str,
        top_k: int = 5,
        filters: dict = None,
    ) -> list[dict]:
        """
        Semantic search: find the most relevant stored texts.

        Returns:
            List of dicts with 'text', 'score', and 'metadata'.
        """
        query_vector = self.embed_text(query)

        # Build optional filter
        qdrant_filter = None
        if filters:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filters.items()
            ]
            qdrant_filter = Filter(must=conditions)

        results = self.client.query_points(
            collection_name=collection,
            query=query_vector,
            query_filter=qdrant_filter,
            limit=top_k,
        )

        return [
            {
                "text": hit.payload.get("text", ""),
                "score": hit.score,
                "metadata": {
                    k: v for k, v in hit.payload.items() if k != "text"
                },
            }
            for hit in results.points
        ]

    def is_healthy(self) -> bool:
        """Check if Qdrant is reachable."""
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False


# Singleton instance
qdrant_service = QdrantService()
