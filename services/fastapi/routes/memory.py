"""
Jarvis Control Tower — Memory Routes
Endpoints for storing and searching vector memory.
"""
from fastapi import APIRouter
from models.schemas import MemoryStoreRequest, MemorySearchRequest
from services.memory import memory_service
from services.qdrant_service import qdrant_service
from config import settings

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/store")
async def store_memory(payload: MemoryStoreRequest):
    """Store text in vector memory."""
    if payload.memory_type == "knowledge":
        point_id = memory_service.store_knowledge(
            text=payload.text,
            metadata={"user_id": payload.user_id, **payload.metadata},
        )
    elif payload.memory_type == "user_preferences":
        point_id = memory_service.store_preference(
            user_id=payload.user_id,
            text=payload.text,
            category=payload.metadata.get("category", "general"),
        )
    else:
        # Default: store as conversation
        point_id = memory_service.save_interaction(
            user_id=payload.user_id,
            message=payload.text,
            intent="manual_store",
            response="",
        )

    return {"stored": True, "point_id": point_id, "collection": payload.memory_type}


@router.post("/search")
async def search_memory(payload: MemorySearchRequest):
    """Search vector memory semantically."""
    if payload.memory_type == "knowledge":
        results = memory_service.search_knowledge(payload.query, top_k=payload.top_k)
    else:
        results = qdrant_service.search(
            collection=payload.memory_type,
            query=payload.query,
            top_k=payload.top_k,
            filters={"user_id": payload.user_id},
        )

    return {"results": results, "count": len(results)}
