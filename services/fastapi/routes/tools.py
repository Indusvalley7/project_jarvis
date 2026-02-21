"""
Jarvis Control Tower — Tool Routes
Endpoints for memory writes and reminder creation.
"""
import logging
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter
from services.database import db
from services.qdrant_service import qdrant_service
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tools", tags=["tools"])


class MemoryWriteRequest(BaseModel):
    user_id: str
    content: str
    tags: list[str] = []
    embed: bool = True  # Also store embedding in Qdrant


class MemoryWriteResponse(BaseModel):
    note_id: str
    qdrant_id: Optional[str] = None
    message: str


class ReminderCreateRequest(BaseModel):
    user_id: str
    chat_id: str
    remind_at: str  # ISO 8601 timestamp
    message: str


class ReminderCreateResponse(BaseModel):
    reminder_id: str
    remind_at: str
    message: str
    status: str = "scheduled"


@router.post("/memory_write", response_model=MemoryWriteResponse)
async def memory_write(payload: MemoryWriteRequest):
    """
    Write a note to Postgres. Optionally embed in Qdrant for RAG retrieval.
    """
    qdrant_id = None

    # Store embedding in Qdrant if requested
    if payload.embed:
        try:
            qdrant_id = qdrant_service.store(
                collection=settings.COLLECTION_KNOWLEDGE,
                text=payload.content,
                metadata={
                    "user_id": payload.user_id,
                    "tags": payload.tags,
                    "source": "memory_write",
                },
            )
        except Exception as e:
            logger.warning("Failed to store embedding in Qdrant: %s", e)

    # Ensure user exists
    await db.ensure_user(payload.user_id)

    # Store note in Postgres
    note_id = await db.create_note(
        user_id=payload.user_id,
        content=payload.content,
        tags=payload.tags,
        qdrant_id=qdrant_id,
    )

    return MemoryWriteResponse(
        note_id=note_id,
        qdrant_id=qdrant_id,
        message=f"Note saved successfully",
    )


@router.post("/reminder_create", response_model=ReminderCreateResponse)
async def reminder_create(payload: ReminderCreateRequest):
    """
    Create a scheduled reminder. The n8n cron workflow will send it when due.
    """
    # Parse the remind_at timestamp
    remind_at = datetime.fromisoformat(payload.remind_at)

    # Ensure user exists
    await db.ensure_user(payload.user_id)

    reminder_id = await db.create_reminder(
        user_id=payload.user_id,
        chat_id=payload.chat_id,
        remind_at=remind_at,
        message=payload.message,
    )

    return ReminderCreateResponse(
        reminder_id=reminder_id,
        remind_at=remind_at.isoformat(),
        message=payload.message,
        status="scheduled",
    )


@router.get("/reminders/due")
async def get_due_reminders():
    """Get all reminders that are due now (used by n8n cron)."""
    reminders = await db.get_due_reminders()
    return {"reminders": reminders}


@router.post("/reminders/{reminder_id}/sent")
async def mark_reminder_sent(reminder_id: str):
    """Mark a reminder as sent (called by n8n after sending)."""
    await db.update_reminder_status(reminder_id, "sent")
    return {"status": "ok", "reminder_id": reminder_id}
