"""
Jarvis Control Tower — Tool Router Agent
Decides which tool endpoints to call based on intent and plan.
"""
import logging
from datetime import datetime, timezone, timedelta
import re
from agents.base import BaseAgent
from models.schemas import AgentInput, AgentOutput
from services.database import db
from services.qdrant_service import qdrant_service
from config import settings

logger = logging.getLogger(__name__)


class ToolRouterAgent(BaseAgent):
    """Routes to appropriate tool endpoints based on intent and executor results."""

    name = "tool_router"

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        intent = agent_input.intent or "unknown"
        metadata = agent_input.metadata or {}
        user_id = agent_input.user_id
        text = agent_input.text

        tool_calls = []

        # ─── Reminder intent → create reminder in Postgres ───
        if intent == "reminder":
            try:
                remind_at = self._parse_reminder_time(text)
                reminder_id = await db.create_reminder(
                    user_id=user_id,
                    chat_id=metadata.get("chat_id", user_id),
                    remind_at=remind_at,
                    message=text,
                )
                tool_calls.append({
                    "tool": "reminder_create",
                    "status": "success",
                    "reminder_id": reminder_id,
                    "remind_at": remind_at.isoformat(),
                })
            except Exception as e:
                tool_calls.append({
                    "tool": "reminder_create",
                    "status": "failed",
                    "error": str(e),
                })

        # ─── Note / memory_update intent → store in Postgres + Qdrant ───
        elif intent in ("note", "memory_update"):
            try:
                # Store embedding in Qdrant
                qdrant_id = qdrant_service.store(
                    collection=settings.COLLECTION_KNOWLEDGE,
                    text=text,
                    metadata={"user_id": user_id, "source": "tool_router"},
                )
                # Store structured note in Postgres
                note_id = await db.create_note(
                    user_id=user_id,
                    content=text,
                    tags=self._extract_tags(text),
                    qdrant_id=qdrant_id,
                )
                tool_calls.append({
                    "tool": "memory_write",
                    "status": "success",
                    "note_id": note_id,
                    "qdrant_id": qdrant_id,
                })
            except Exception as e:
                tool_calls.append({
                    "tool": "memory_write",
                    "status": "failed",
                    "error": str(e),
                })

        return AgentOutput(
            agent_name=self.name,
            success=True,
            data={
                "tool_calls": tool_calls,
                "tools_executed": len(tool_calls),
            },
        )

    def _parse_reminder_time(self, text: str) -> datetime:
        """
        Parse natural language time from reminder text.
        Supports: 'in X minutes/hours', 'at HH:MM', 'tomorrow'.
        Falls back to 5 minutes from now.
        """
        now = datetime.now(timezone.utc)
        text_lower = text.lower()

        # "in X minutes"
        match = re.search(r"in\s+(\d+)\s+min", text_lower)
        if match:
            return now + timedelta(minutes=int(match.group(1)))

        # "in X hours"
        match = re.search(r"in\s+(\d+)\s+hour", text_lower)
        if match:
            return now + timedelta(hours=int(match.group(1)))

        # "at HH:MM"
        match = re.search(r"at\s+(\d{1,2}):(\d{2})", text_lower)
        if match:
            hour, minute = int(match.group(1)), int(match.group(2))
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                target += timedelta(days=1)
            return target

        # "tomorrow"
        if "tomorrow" in text_lower:
            return now + timedelta(days=1)

        # Default: 5 minutes
        return now + timedelta(minutes=5)

    def _extract_tags(self, text: str) -> list[str]:
        """Extract simple tags from text based on keywords."""
        tags = []
        keywords = {
            "name": ["name", "called", "i am", "i'm"],
            "preference": ["prefer", "like", "favorite", "favourite"],
            "fact": ["remember", "note", "save", "important"],
            "contact": ["phone", "email", "address", "number"],
        }
        text_lower = text.lower()
        for tag, words in keywords.items():
            if any(w in text_lower for w in words):
                tags.append(tag)
        return tags or ["general"]


tool_router_agent = ToolRouterAgent()
