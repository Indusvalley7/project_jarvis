"""
Jarvis Control Tower — n8n Management Routes
Exposes n8n workflow management through the FastAPI control tower.
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.n8n_client import n8n_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/n8n", tags=["n8n"])


# ── Request / Response Models ────────────────────────────────────────


class WorkflowCreateRequest(BaseModel):
    """Body for POST /n8n/workflows."""
    name: str
    nodes: list[dict]
    connections: dict = {}
    settings: dict = {"executionOrder": "v1"}


class WorkflowExecuteRequest(BaseModel):
    """Body for POST /n8n/workflows/{id}/execute."""
    payload: dict | None = None


class WebhookTriggerRequest(BaseModel):
    """Body for POST /n8n/webhook/{path}."""
    payload: dict


# ── Workflow Endpoints ───────────────────────────────────────────────


@router.get("/workflows")
async def list_workflows():
    """List all n8n workflows."""
    workflows = await n8n_client.list_workflows()
    return {
        "count": len(workflows),
        "workflows": [
            {
                "id": w.get("id"),
                "name": w.get("name"),
                "active": w.get("active"),
                "createdAt": w.get("createdAt"),
                "updatedAt": w.get("updatedAt"),
            }
            for w in workflows
        ],
    }


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get details of a single workflow."""
    result = await n8n_client.get_workflow(workflow_id)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return result


@router.post("/workflows", status_code=201)
async def create_workflow(body: WorkflowCreateRequest):
    """Create a new n8n workflow."""
    result = await n8n_client.create_workflow(body.model_dump())
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return result


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete an n8n workflow."""
    result = await n8n_client.delete_workflow(workflow_id)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return {"status": "deleted", "id": workflow_id}


# ── Activation Endpoints ────────────────────────────────────────────


@router.post("/workflows/{workflow_id}/activate")
async def activate_workflow(workflow_id: str):
    """Activate an n8n workflow."""
    result = await n8n_client.activate_workflow(workflow_id)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return {"status": "activated", "id": workflow_id, "active": result.get("active")}


@router.post("/workflows/{workflow_id}/deactivate")
async def deactivate_workflow(workflow_id: str):
    """Deactivate an n8n workflow."""
    result = await n8n_client.deactivate_workflow(workflow_id)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return {"status": "deactivated", "id": workflow_id, "active": result.get("active")}


# ── Execution Endpoints ──────────────────────────────────────────────


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, body: WorkflowExecuteRequest | None = None):
    """Manually trigger a workflow execution."""
    payload = body.payload if body else None
    result = await n8n_client.execute_workflow(workflow_id, payload)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return result


@router.get("/executions")
async def list_executions(limit: int = 20):
    """List recent workflow executions."""
    executions = await n8n_client.list_executions(limit)
    return {"count": len(executions), "executions": executions}


# ── Webhook Proxy ────────────────────────────────────────────────────


@router.post("/webhook/{webhook_path:path}")
async def trigger_webhook(webhook_path: str, body: WebhookTriggerRequest):
    """Trigger an n8n workflow via its webhook path."""
    result = await n8n_client.trigger_webhook(webhook_path, body.payload)
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return result
