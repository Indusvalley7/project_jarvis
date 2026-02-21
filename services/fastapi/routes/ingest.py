"""
Jarvis Control Tower — RAG Ingestion Route
Accepts text chunks, embeds them, and upserts into Qdrant.
"""
import logging
from pydantic import BaseModel
from fastapi import APIRouter
from services.qdrant_service import qdrant_service
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["rag"])


class IngestRequest(BaseModel):
    chunks: list[str]
    collection: str = "knowledge"
    metadata: dict = {}


class IngestResponse(BaseModel):
    ingested: int
    point_ids: list[str]


@router.post("/rag/ingest", response_model=IngestResponse)
async def ingest_chunks(payload: IngestRequest):
    """
    Accept text chunks, embed them via fastembed, and upsert into Qdrant.
    Used for document ingestion and long-text storage.
    """
    collection = payload.collection
    if collection not in [
        settings.COLLECTION_KNOWLEDGE,
        settings.COLLECTION_CONVERSATIONS,
        settings.COLLECTION_USER_PREFS,
    ]:
        collection = settings.COLLECTION_KNOWLEDGE

    point_ids = []
    for chunk in payload.chunks:
        try:
            pid = qdrant_service.store(
                collection=collection,
                text=chunk,
                metadata={
                    "source": "rag_ingest",
                    **payload.metadata,
                },
            )
            point_ids.append(pid)
        except Exception as e:
            logger.error("Failed to ingest chunk: %s", str(e))

    logger.info("Ingested %d/%d chunks into %s", len(point_ids), len(payload.chunks), collection)
    return IngestResponse(ingested=len(point_ids), point_ids=point_ids)
