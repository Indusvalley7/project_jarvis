"""
Jarvis Control Tower — Run Logger
Tracks agent execution runs with full trace data.
"""
import uuid
import time
import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# In-memory store for recent runs (could be moved to Qdrant or a file later)
_run_store: dict[str, dict] = {}
MAX_STORED_RUNS = 100


class RunLogger:
    """Logs and tracks agent pipeline execution runs."""

    def start_run(self, user_id: str, text: str) -> str:
        """Start a new run and return its ID."""
        run_id = str(uuid.uuid4())[:8]
        _run_store[run_id] = {
            "run_id": run_id,
            "user_id": user_id,
            "input_text": text,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "status": "running",
            "steps": [],
            "final_response": None,
            "total_duration_ms": None,
        }

        # Evict old runs if we're over the limit
        if len(_run_store) > MAX_STORED_RUNS:
            oldest_key = next(iter(_run_store))
            del _run_store[oldest_key]

        logger.info("[run:%s] Started for user=%s", run_id, user_id)
        return run_id

    def log_step(self, run_id: str, agent_name: str, output: dict):
        """Log an agent step to the run."""
        if run_id not in _run_store:
            return

        _run_store[run_id]["steps"].append({
            "agent": agent_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success": output.get("success", False),
            "duration_ms": output.get("duration_ms", 0),
            "data": output.get("data", {}),
            "error": output.get("error"),
        })

    def complete_run(self, run_id: str, response: str, total_ms: float):
        """Mark a run as complete."""
        if run_id not in _run_store:
            return

        run = _run_store[run_id]
        run["completed_at"] = datetime.now(timezone.utc).isoformat()
        run["status"] = "completed"
        run["final_response"] = response
        run["total_duration_ms"] = round(total_ms, 2)
        logger.info("[run:%s] Completed in %.0fms", run_id, total_ms)

    def fail_run(self, run_id: str, error: str, total_ms: float):
        """Mark a run as failed."""
        if run_id not in _run_store:
            return

        run = _run_store[run_id]
        run["completed_at"] = datetime.now(timezone.utc).isoformat()
        run["status"] = "failed"
        run["error"] = error
        run["total_duration_ms"] = round(total_ms, 2)
        logger.error("[run:%s] Failed: %s", run_id, error)

    def get_run(self, run_id: str) -> Optional[dict]:
        """Get a run by ID."""
        return _run_store.get(run_id)

    def get_latest_run(self) -> Optional[dict]:
        """Get the most recent run."""
        if not _run_store:
            return None
        return list(_run_store.values())[-1]

    def get_recent_runs(self, limit: int = 10) -> list[dict]:
        """Get the N most recent runs."""
        runs = list(_run_store.values())
        return runs[-limit:]


# Singleton instance
run_logger = RunLogger()
