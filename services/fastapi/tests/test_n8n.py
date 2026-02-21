"""Tests for n8n management routes."""
import sys
import os
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

MOCK_WORKFLOWS = [
    {"id": "wf-1", "name": "Test Workflow", "active": True,
     "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z"},
    {"id": "wf-2", "name": "Another Workflow", "active": False,
     "createdAt": "2026-01-02T00:00:00Z", "updatedAt": "2026-01-02T00:00:00Z"},
]


class TestListWorkflows:
    @patch("routes.n8n.n8n_client")
    def test_list_workflows(self, mock_client, client):
        mock_client.list_workflows = AsyncMock(return_value=MOCK_WORKFLOWS)

        resp = client.get("/n8n/workflows")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert data["workflows"][0]["name"] == "Test Workflow"
        assert data["workflows"][1]["active"] is False


class TestGetWorkflow:
    @patch("routes.n8n.n8n_client")
    def test_get_workflow_success(self, mock_client, client):
        mock_client.get_workflow = AsyncMock(return_value={
            "id": "wf-1", "name": "Test Workflow", "active": True,
            "nodes": [], "connections": {},
        })

        resp = client.get("/n8n/workflows/wf-1")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Workflow"

    @patch("routes.n8n.n8n_client")
    def test_get_workflow_not_found(self, mock_client, client):
        mock_client.get_workflow = AsyncMock(return_value={"error": "Not found"})

        resp = client.get("/n8n/workflows/bad-id")
        assert resp.status_code == 502


class TestCreateWorkflow:
    @patch("routes.n8n.n8n_client")
    def test_create_workflow(self, mock_client, client):
        mock_client.create_workflow = AsyncMock(return_value={
            "id": "new-wf", "name": "New Workflow",
        })

        resp = client.post("/n8n/workflows", json={
            "name": "New Workflow",
            "nodes": [{"type": "test", "name": "Node1"}],
        })
        assert resp.status_code == 201
        assert resp.json()["id"] == "new-wf"


class TestDeleteWorkflow:
    @patch("routes.n8n.n8n_client")
    def test_delete_workflow(self, mock_client, client):
        mock_client.delete_workflow = AsyncMock(return_value={"id": "wf-1"})

        resp = client.delete("/n8n/workflows/wf-1")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"


class TestActivateDeactivate:
    @patch("routes.n8n.n8n_client")
    def test_activate(self, mock_client, client):
        mock_client.activate_workflow = AsyncMock(return_value={
            "id": "wf-1", "active": True,
        })

        resp = client.post("/n8n/workflows/wf-1/activate")
        assert resp.status_code == 200
        assert resp.json()["status"] == "activated"
        assert resp.json()["active"] is True

    @patch("routes.n8n.n8n_client")
    def test_deactivate(self, mock_client, client):
        mock_client.deactivate_workflow = AsyncMock(return_value={
            "id": "wf-1", "active": False,
        })

        resp = client.post("/n8n/workflows/wf-1/deactivate")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deactivated"
        assert resp.json()["active"] is False


class TestExecutions:
    @patch("routes.n8n.n8n_client")
    def test_list_executions(self, mock_client, client):
        mock_client.list_executions = AsyncMock(return_value=[
            {"id": "exec-1", "status": "success"},
        ])

        resp = client.get("/n8n/executions")
        assert resp.status_code == 200
        assert resp.json()["count"] == 1


class TestWebhookProxy:
    @patch("routes.n8n.n8n_client")
    def test_trigger_webhook(self, mock_client, client):
        mock_client.trigger_webhook = AsyncMock(return_value={
            "status": "reminder_scheduled",
        })

        resp = client.post("/n8n/webhook/reminder", json={
            "payload": {"user_id": "u1", "text": "test"},
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "reminder_scheduled"
