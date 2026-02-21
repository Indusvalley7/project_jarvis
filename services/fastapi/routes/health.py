"""
Jarvis Control Tower — Health & Diagnostics Routes
System health, execution traces, and diagnostics.
Now reads from Postgres for persistent run data.
"""
from datetime import datetime, timezone
from fastapi import APIRouter
from models.schemas import HealthResponse
from config import settings
from services.ollama_client import ollama_client
from services.qdrant_service import qdrant_service
from services.n8n_client import n8n_client
from services.database import db

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    """Basic health check."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/diagnostics", response_model=HealthResponse)
async def diagnostics():
    """Full system diagnostics — checks all services."""
    ollama_ok = await ollama_client.is_healthy()
    qdrant_ok = qdrant_service.is_healthy()
    n8n_ok = await n8n_client.is_healthy()
    postgres_ok = db.is_healthy()

    all_ok = ollama_ok and qdrant_ok and n8n_ok and postgres_ok

    return HealthResponse(
        status="healthy" if all_ok else "degraded",
        services={
            "ollama": {"status": "up" if ollama_ok else "down", "url": ollama_client.base_url},
            "qdrant": {"status": "up" if qdrant_ok else "down", "url": settings.QDRANT_URL},
            "n8n": {"status": "up" if n8n_ok else "down", "url": n8n_client.base_url},
            "postgres": {"status": "up" if postgres_ok else "down"},
        },
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/trace/{run_id}")
async def get_trace(run_id: str):
    """Get execution trace for a specific run (from Postgres)."""
    run = await db.get_run(run_id)
    if not run:
        return {"error": "Run not found", "run_id": run_id}
    return run


@router.get("/trace/latest/run")
async def get_latest_trace():
    """Get the most recent execution trace."""
    runs = await db.get_recent_runs(limit=1)
    if not runs:
        return {"error": "No runs found"}
    return await db.get_run(runs[0]["run_id"])


@router.get("/runs")
async def get_recent_runs(limit: int = 10):
    """Get recent execution runs (from Postgres)."""
    runs = await db.get_recent_runs(limit)
    return {"runs": runs}


@router.get("/dashboard/runs")
async def dashboard_runs(limit: int = 20):
    """Dashboard endpoint — recent runs with summary data."""
    return {"runs": await db.get_recent_runs(limit)}


@router.get("/dashboard/runs/{run_id}")
async def dashboard_run_detail(run_id: str):
    """Dashboard endpoint — full run detail with agent steps."""
    run = await db.get_run(run_id)
    if not run:
        return {"error": "Run not found", "run_id": run_id}
    return run
