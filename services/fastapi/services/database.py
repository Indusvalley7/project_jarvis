"""
Jarvis Control Tower — Database Service
Async Postgres client with CRUD operations for all tables.
"""
import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

import asyncpg
from config import settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """Async Postgres client for persistent storage."""

    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def connect(self):
        """Create connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=2,
                max_size=10,
            )
            logger.info("Connected to Postgres")
        except Exception as e:
            logger.error("Failed to connect to Postgres: %s", e)
            raise

    async def disconnect(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from Postgres")

    def is_healthy(self) -> bool:
        """Check if database pool is available."""
        return self.pool is not None and not self.pool._closed

    # ──────────────── Users ────────────────

    async def ensure_user(self, user_id: str, username: str = None):
        """Create user if not exists, return user row."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
            if row:
                return dict(row)
            await conn.execute(
                "INSERT INTO users (id, username) VALUES ($1, $2) ON CONFLICT (id) DO NOTHING",
                user_id, username,
            )
            return {"id": user_id, "username": username}

    # ──────────────── Runs ────────────────

    async def create_run(self, user_id: str, input_text: str) -> str:
        """Create a new run, return run_id."""
        run_id = str(uuid4())
        async with self.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO runs (run_id, user_id, input_text, status)
                   VALUES ($1, $2, $3, 'running')""",
                run_id, user_id, input_text,
            )
        return run_id

    async def complete_run(
        self, run_id: str, intent: str, reply: str, duration_ms: float
    ):
        """Mark a run as successful."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """UPDATE runs SET status='success', intent=$2, reply=$3,
                   duration_ms=$4 WHERE run_id=$1""",
                run_id, intent, reply, duration_ms,
            )

    async def fail_run(self, run_id: str, error: str, duration_ms: float):
        """Mark a run as failed."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """UPDATE runs SET status='failed', reply=$2,
                   duration_ms=$3 WHERE run_id=$1""",
                run_id, error, duration_ms,
            )

    async def get_run(self, run_id: str) -> dict | None:
        """Get a run by ID with its steps."""
        async with self.pool.acquire() as conn:
            run = await conn.fetchrow("SELECT * FROM runs WHERE run_id = $1", run_id)
            if not run:
                return None
            steps = await conn.fetch(
                "SELECT * FROM run_steps WHERE run_id = $1 ORDER BY created_at",
                run_id,
            )
            result = dict(run)
            result["run_id"] = str(result["run_id"])
            result["steps"] = [
                {
                    "id": str(s["id"]),
                    "step_name": s["step_name"],
                    "input_json": s["input_json"],
                    "output_json": s["output_json"],
                    "error": s["error"],
                    "latency_ms": s["latency_ms"],
                    "created_at": s["created_at"].isoformat() if s["created_at"] else None,
                }
                for s in steps
            ]
            result["created_at"] = result["created_at"].isoformat() if result["created_at"] else None
            return result

    async def get_recent_runs(self, limit: int = 20) -> list[dict]:
        """Get recent runs."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM runs ORDER BY created_at DESC LIMIT $1", limit
            )
            return [
                {
                    "run_id": str(r["run_id"]),
                    "user_id": r["user_id"],
                    "input_text": r["input_text"],
                    "intent": r["intent"],
                    "status": r["status"],
                    "reply": r["reply"],
                    "duration_ms": r["duration_ms"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                }
                for r in rows
            ]

    # ──────────────── Run Steps ────────────────

    async def create_run_step(
        self,
        run_id: str,
        step_name: str,
        input_json: dict = None,
        output_json: dict = None,
        error: str = None,
        latency_ms: float = None,
    ):
        """Log a step within a run."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO run_steps (run_id, step_name, input_json, output_json, error, latency_ms)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                run_id,
                step_name,
                json.dumps(input_json) if input_json else None,
                json.dumps(output_json) if output_json else None,
                error,
                latency_ms,
            )

    # ──────────────── Notes ────────────────

    async def create_note(
        self, user_id: str, content: str, tags: list[str] = None, qdrant_id: str = None
    ) -> str:
        """Create a note, return note ID."""
        note_id = str(uuid4())
        async with self.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO notes (id, user_id, content, tags, qdrant_id)
                   VALUES ($1, $2, $3, $4, $5)""",
                note_id, user_id, content, tags or [], qdrant_id,
            )
        return note_id

    async def get_user_notes(self, user_id: str, limit: int = 20) -> list[dict]:
        """Get notes for a user."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM notes WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2",
                user_id, limit,
            )
            return [
                {
                    "id": str(r["id"]),
                    "content": r["content"],
                    "tags": r["tags"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                }
                for r in rows
            ]

    # ──────────────── Reminders ────────────────

    async def create_reminder(
        self, user_id: str, chat_id: str, remind_at: datetime, message: str
    ) -> str:
        """Create a scheduled reminder, return reminder ID."""
        reminder_id = str(uuid4())
        async with self.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO reminders (id, user_id, chat_id, remind_at, message, status)
                   VALUES ($1, $2, $3, $4, $5, 'scheduled')""",
                reminder_id, user_id, chat_id, remind_at, message,
            )
        return reminder_id

    async def get_due_reminders(self) -> list[dict]:
        """Get all reminders that are due now."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT * FROM reminders
                   WHERE status = 'scheduled' AND remind_at <= NOW()
                   ORDER BY remind_at""",
            )
            return [
                {
                    "id": str(r["id"]),
                    "user_id": r["user_id"],
                    "chat_id": r["chat_id"],
                    "message": r["message"],
                    "remind_at": r["remind_at"].isoformat() if r["remind_at"] else None,
                }
                for r in rows
            ]

    async def update_reminder_status(self, reminder_id: str, status: str):
        """Update reminder status (sent, cancelled)."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE reminders SET status = $2 WHERE id = $1",
                reminder_id, status,
            )

    # ──────────────── Workflow Errors ────────────────

    async def create_workflow_error(
        self,
        workflow_name: str,
        error_json: dict,
        diagnosis_json: dict = None,
        run_id: str = None,
    ) -> str:
        """Log a workflow error."""
        error_id = str(uuid4())
        async with self.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO workflow_errors (id, workflow_name, run_id, error_json, diagnosis_json)
                   VALUES ($1, $2, $3, $4, $5)""",
                error_id,
                workflow_name,
                run_id,
                json.dumps(error_json),
                json.dumps(diagnosis_json) if diagnosis_json else None,
            )
        return error_id

    async def get_recent_errors(self, limit: int = 20) -> list[dict]:
        """Get recent workflow errors."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM workflow_errors ORDER BY created_at DESC LIMIT $1",
                limit,
            )
            return [
                {
                    "id": str(r["id"]),
                    "workflow_name": r["workflow_name"],
                    "run_id": str(r["run_id"]) if r["run_id"] else None,
                    "error_json": r["error_json"],
                    "diagnosis_json": r["diagnosis_json"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                }
                for r in rows
            ]


# Singleton instance
db = DatabaseService()
