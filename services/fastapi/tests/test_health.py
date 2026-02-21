"""Tests for health and diagnostics routes."""
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestHealthRoute:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    @patch("routes.health.db")
    @patch("routes.health.n8n_client")
    @patch("routes.health.qdrant_service")
    @patch("routes.health.ollama_client")
    def test_diagnostics_all_healthy(self, mock_ollama, mock_qdrant, mock_n8n, mock_db, client):
        mock_ollama.is_healthy = AsyncMock(return_value=True)
        mock_ollama.base_url = "http://ollama:11434"
        mock_qdrant.is_healthy = MagicMock(return_value=True)
        mock_n8n.is_healthy = AsyncMock(return_value=True)
        mock_n8n.base_url = "http://n8n:5678"
        mock_db.is_healthy = MagicMock(return_value=True)

        resp = client.get("/diagnostics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["services"]["ollama"]["status"] == "up"
        assert data["services"]["qdrant"]["status"] == "up"
        assert data["services"]["n8n"]["status"] == "up"
        assert data["services"]["postgres"]["status"] == "up"

    @patch("routes.health.db")
    @patch("routes.health.n8n_client")
    @patch("routes.health.qdrant_service")
    @patch("routes.health.ollama_client")
    def test_diagnostics_degraded(self, mock_ollama, mock_qdrant, mock_n8n, mock_db, client):
        mock_ollama.is_healthy = AsyncMock(return_value=False)
        mock_ollama.base_url = "http://ollama:11434"
        mock_qdrant.is_healthy = MagicMock(return_value=True)
        mock_n8n.is_healthy = AsyncMock(return_value=True)
        mock_n8n.base_url = "http://n8n:5678"
        mock_db.is_healthy = MagicMock(return_value=True)

        resp = client.get("/diagnostics")
        data = resp.json()
        assert data["status"] == "degraded"
        assert data["services"]["ollama"]["status"] == "down"
