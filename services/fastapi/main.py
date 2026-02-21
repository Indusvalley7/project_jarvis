"""
Jarvis Control Tower — FastAPI Application
Main entrypoint for the AI orchestration layer.
"""
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routes.orchestrate import router as orchestrate_router
from routes.health import router as health_router
from routes.memory import router as memory_router
from routes.n8n import router as n8n_router
from routes.tools import router as tools_router
from routes.ingest import router as ingest_router
from routes.diagnose import router as diagnose_router
from services.qdrant_service import qdrant_service
from services.database import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("jarvis")

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 Jarvis Control Tower starting up...")

    # Initialize Qdrant collections
    try:
        qdrant_service.ensure_collections()
        logger.info("✅ Qdrant collections ready")
    except Exception as e:
        logger.warning("⚠️  Qdrant init failed (will retry on first use): %s", e)

    # Connect to Postgres
    try:
        await db.connect()
        logger.info("✅ Postgres connected")
    except Exception as e:
        logger.warning("⚠️  Postgres connection failed: %s", e)

    yield

    # Cleanup
    await db.disconnect()
    logger.info("👋 Jarvis Control Tower shutting down...")


app = FastAPI(
    title="Jarvis Control Tower",
    description="Multi-Agent AI System with RAG and Self-Monitoring",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount API routes
app.include_router(orchestrate_router)
app.include_router(health_router)
app.include_router(memory_router)
app.include_router(n8n_router)
app.include_router(tools_router)
app.include_router(ingest_router)
app.include_router(diagnose_router)

# Mount static files and dashboard
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def dashboard():
    """Serve the Jarvis Control Tower dashboard."""
    return FileResponse(str(STATIC_DIR / "index.html"))

