"""
Jarvis Control Tower — Diagnosis Route
Receives n8n error payloads, stores them, and returns fix suggestions.
"""
import logging
from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter
from services.database import db
from services.ollama_client import ollama_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["diagnose"])

DIAGNOSE_SYSTEM = """You are a DevOps assistant. Given an n8n workflow error,
provide a short, actionable diagnosis. Include:
1. What went wrong (1 sentence)
2. Most likely cause
3. Suggested fix (1-3 steps)

Respond in plain text, keep it concise and human-readable."""


class DiagnoseRequest(BaseModel):
    workflow_name: str
    error: dict
    run_id: Optional[str] = None


class DiagnoseResponse(BaseModel):
    error_id: str
    workflow_name: str
    diagnosis: str


@router.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose_error(payload: DiagnoseRequest):
    """
    Receive an n8n error payload, store it in workflow_errors,
    and use the LLM to generate a human-readable fix suggestion.
    """
    # Generate diagnosis using LLM
    prompt = f"""Workflow: {payload.workflow_name}
Error details:
{payload.error}

Diagnose this error and suggest a fix."""

    try:
        diagnosis = await ollama_client.generate(prompt, system=DIAGNOSE_SYSTEM)
    except Exception as e:
        logger.error("LLM diagnosis failed: %s", e)
        diagnosis = f"LLM unavailable. Raw error: {payload.error.get('message', str(payload.error))}"

    # Store in Postgres
    diagnosis_json = {"summary": diagnosis}
    error_id = await db.create_workflow_error(
        workflow_name=payload.workflow_name,
        error_json=payload.error,
        diagnosis_json=diagnosis_json,
        run_id=payload.run_id,
    )

    return DiagnoseResponse(
        error_id=error_id,
        workflow_name=payload.workflow_name,
        diagnosis=diagnosis,
    )


@router.get("/diagnose/errors")
async def get_recent_errors(limit: int = 20):
    """Get recent workflow errors with diagnosis."""
    errors = await db.get_recent_errors(limit)
    return {"errors": errors}
