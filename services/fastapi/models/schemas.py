"""
Jarvis Control Tower — Pydantic Models
Request/response schemas for all API endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# --- Enums ---

class Intent(str, Enum):
    REMINDER = "reminder"
    NOTE = "note"
    QUESTION = "question"
    MEMORY_UPDATE = "memory_update"
    DIAGNOSTIC = "diagnostic"
    UNKNOWN = "unknown"


# --- Agent I/O ---

class AgentInput(BaseModel):
    """Standard input passed between agents."""
    user_id: str
    text: str
    intent: Optional[Intent] = None
    context: Optional[list[str]] = Field(default_factory=list)
    plan: Optional[list[str]] = Field(default_factory=list)
    metadata: Optional[dict] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    """Standard output returned by each agent."""
    agent_name: str
    success: bool
    data: dict = Field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: Optional[float] = None


# --- API Request/Response ---

class OrchestrateRequest(BaseModel):
    """Incoming orchestration request."""
    user_id: str
    text: str


class OrchestrateResponse(BaseModel):
    """Orchestration response with full trace."""
    reply: str
    intent: str
    trace: list[dict] = Field(default_factory=list)
    run_id: str = ""


class MemoryStoreRequest(BaseModel):
    """Request to store a memory."""
    user_id: str
    text: str
    memory_type: str = "knowledge"  # conversations, knowledge, user_preferences
    metadata: dict = Field(default_factory=dict)


class MemorySearchRequest(BaseModel):
    """Request to search memory."""
    user_id: str
    query: str
    memory_type: str = "conversations"
    top_k: int = 5


class MemorySearchResult(BaseModel):
    """Single memory search result."""
    text: str
    score: float
    metadata: dict = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """System health status."""
    status: str
    services: dict = Field(default_factory=dict)
    timestamp: str = ""
