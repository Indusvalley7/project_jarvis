"""
Jarvis Control Tower — n8n Client
Triggers n8n workflows via webhooks and REST API.
"""
import httpx
import logging
from config import settings

logger = logging.getLogger(__name__)


class N8nClient:
    """Client for triggering and managing n8n workflows."""

    def __init__(self):
        self.base_url = settings.N8N_URL
        self.api_key = settings.N8N_API_KEY

    def _headers(self) -> dict:
        """Build request headers with API key."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key
        return headers

    # ── Webhook ──────────────────────────────────────────────────────

    async def trigger_webhook(self, webhook_path: str, payload: dict) -> dict:
        """
        Trigger an n8n workflow via its webhook URL.

        Args:
            webhook_path: The webhook path (e.g., 'reminder', 'note-save')
            payload: Data to send to the workflow

        Returns:
            Response from n8n
        """
        url = f"{self.base_url}/webhook/{webhook_path}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error("Failed to trigger n8n webhook '%s': %s", webhook_path, str(e))
            return {"error": str(e)}

    # ── Workflow CRUD ────────────────────────────────────────────────

    async def list_workflows(self) -> list[dict]:
        """List all workflows via n8n REST API."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/workflows",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json().get("data", [])
        except Exception as e:
            logger.error("Failed to list n8n workflows: %s", str(e))
            return []

    async def get_workflow(self, workflow_id: str) -> dict:
        """Get a single workflow by ID."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/workflows/{workflow_id}",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error("Failed to get workflow %s: %s", workflow_id, str(e))
            return {"error": str(e)}

    async def create_workflow(self, workflow_json: dict) -> dict:
        """Create a new workflow via n8n REST API."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/workflows",
                    headers=self._headers(),
                    json=workflow_json,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error("Failed to create n8n workflow: %s", str(e))
            return {"error": str(e)}

    async def delete_workflow(self, workflow_id: str) -> dict:
        """Delete a workflow by ID."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.delete(
                    f"{self.base_url}/api/v1/workflows/{workflow_id}",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error("Failed to delete workflow %s: %s", workflow_id, str(e))
            return {"error": str(e)}

    # ── Workflow Activation ──────────────────────────────────────────

    async def activate_workflow(self, workflow_id: str) -> dict:
        """Activate a workflow by ID (uses POST /activate)."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/workflows/{workflow_id}/activate",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error("Failed to activate workflow %s: %s", workflow_id, str(e))
            return {"error": str(e)}

    async def deactivate_workflow(self, workflow_id: str) -> dict:
        """Deactivate a workflow by ID (uses POST /deactivate)."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/workflows/{workflow_id}/deactivate",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error("Failed to deactivate workflow %s: %s", workflow_id, str(e))
            return {"error": str(e)}

    # ── Executions ───────────────────────────────────────────────────

    async def execute_workflow(self, workflow_id: str, payload: dict | None = None) -> dict:
        """Manually trigger a workflow execution via the REST API."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/executions",
                    headers=self._headers(),
                    json={"workflowId": workflow_id, **(payload or {})},
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error("Failed to execute workflow %s: %s", workflow_id, str(e))
            return {"error": str(e)}

    async def list_executions(self, limit: int = 20) -> list[dict]:
        """List recent workflow executions."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/executions",
                    headers=self._headers(),
                    params={"limit": limit},
                )
                response.raise_for_status()
                return response.json().get("data", [])
        except Exception as e:
            logger.error("Failed to list executions: %s", str(e))
            return []

    # ── Health ───────────────────────────────────────────────────────

    async def is_healthy(self) -> bool:
        """Check if n8n is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/healthz")
                return resp.status_code == 200
        except Exception:
            return False


# Singleton instance
n8n_client = N8nClient()
