"""
Test fixtures and shared configuration for Jarvis Control Tower tests.
"""
import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure the app root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def mock_qdrant_service():
    """Mock the Qdrant service for tests that don't need a real DB."""
    with patch("services.qdrant_service.qdrant_service") as mock:
        mock.ensure_collections = MagicMock()
        mock.is_healthy = MagicMock(return_value=True)
        mock.store = MagicMock(return_value="test-point-id")
        mock.search = MagicMock(return_value=[])
        yield mock


@pytest.fixture
def mock_ollama_client():
    """Mock the Ollama client for tests that don't need a real LLM."""
    with patch("services.ollama_client.ollama_client") as mock:
        mock.is_healthy = AsyncMock(return_value=True)
        mock.generate = AsyncMock(return_value="Test response")
        mock.generate_json = AsyncMock(return_value={"intent": "question"})
        yield mock


@pytest.fixture
def mock_n8n_client():
    """Mock the n8n client for tests that don't need a real n8n instance."""
    with patch("services.n8n_client.n8n_client") as mock:
        mock.is_healthy = AsyncMock(return_value=True)
        mock.list_workflows = AsyncMock(return_value=[
            {"id": "test-id-1", "name": "Test Workflow", "active": True,
             "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z"},
        ])
        mock.get_workflow = AsyncMock(return_value={
            "id": "test-id-1", "name": "Test Workflow", "active": True,
            "nodes": [], "connections": {},
        })
        mock.create_workflow = AsyncMock(return_value={"id": "new-id", "name": "New"})
        mock.delete_workflow = AsyncMock(return_value={"id": "test-id-1"})
        mock.activate_workflow = AsyncMock(return_value={"id": "test-id-1", "active": True})
        mock.deactivate_workflow = AsyncMock(return_value={"id": "test-id-1", "active": False})
        mock.execute_workflow = AsyncMock(return_value={"id": "exec-1"})
        mock.list_executions = AsyncMock(return_value=[])
        mock.trigger_webhook = AsyncMock(return_value={"status": "ok"})
        yield mock


@pytest.fixture
def app():
    """Create a FastAPI test application."""
    from main import app
    return app


@pytest.fixture
def client(app):
    """Create a synchronous test client."""
    from fastapi.testclient import TestClient
    return TestClient(app)
