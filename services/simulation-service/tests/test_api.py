"""Integration tests for the simulation service API."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from src.api import app, _simulations
from src.models import (
    AgentRole,
    KnowledgeGraph,
    Entity,
    SimulationResult,
    SimulationStatus,
)


@pytest.fixture(autouse=True)
def clear_simulations():
    """Clear in-memory store between tests."""
    _simulations.clear()
    yield
    _simulations.clear()


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
class TestHealth:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "simulation-service"


# ---------------------------------------------------------------------------
# Start simulation
# ---------------------------------------------------------------------------
class TestStartSimulation:
    @patch("src.api._openai_client")
    @patch("src.api.asyncio.create_task")
    def test_start_returns_202(self, mock_task, mock_client, client):
        mock_task.return_value = MagicMock()
        payload = {
            "seed_text": "The ECB raised rates by 25bps at its March meeting. " * 5,
            "prediction_query": "Will DAX correct more than 5% in the next 30 days?",
        }
        response = client.post("/simulate", json=payload)
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "pending"
        assert "simulation_id" in data

    def test_short_seed_returns_422(self, client):
        payload = {
            "seed_text": "Too short",
            "prediction_query": "Will markets fall?",
        }
        response = client.post("/simulate", json=payload)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Get simulation
# ---------------------------------------------------------------------------
class TestGetSimulation:
    def test_not_found(self, client):
        response = client.get("/simulate/nonexistent-id")
        assert response.status_code == 404

    def test_found(self, client):
        from src.models import SimulationRequest
        sim_id = "test-sim-123"
        req = SimulationRequest(
            seed_text="Market data " * 10,
            prediction_query="Will S&P 500 rally?",
        )
        _simulations[sim_id] = SimulationResult(
            simulation_id=sim_id,
            status=SimulationStatus.COMPLETED,
            request=req,
        )
        response = client.get(f"/simulate/{sim_id}")
        assert response.status_code == 200
        assert response.json()["simulation_id"] == sim_id


# ---------------------------------------------------------------------------
# Ask endpoint
# ---------------------------------------------------------------------------
class TestAsk:
    def test_ask_on_non_completed_returns_409(self, client):
        from src.models import SimulationRequest
        sim_id = "running-sim"
        req = SimulationRequest(
            seed_text="Market data " * 10,
            prediction_query="Will BTC hit 100k?",
        )
        _simulations[sim_id] = SimulationResult(
            simulation_id=sim_id,
            status=SimulationStatus.RUNNING,
            request=req,
        )
        response = client.post(f"/simulate/{sim_id}/ask", json={"question": "What are the risks?"})
        assert response.status_code == 409

    def test_ask_on_missing_sim_returns_404(self, client):
        response = client.post("/simulate/no-such-sim/ask", json={"question": "What?"})
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Delete simulation
# ---------------------------------------------------------------------------
class TestDeleteSimulation:
    def test_delete_existing(self, client):
        from src.models import SimulationRequest
        sim_id = "to-delete"
        req = SimulationRequest(
            seed_text="Market data " * 10,
            prediction_query="Will bonds rally?",
        )
        _simulations[sim_id] = SimulationResult(
            simulation_id=sim_id,
            status=SimulationStatus.COMPLETED,
            request=req,
        )
        response = client.delete(f"/simulate/{sim_id}")
        assert response.status_code == 204
        assert sim_id not in _simulations

    def test_delete_missing_returns_404(self, client):
        response = client.delete("/simulate/ghost-sim")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# List simulations
# ---------------------------------------------------------------------------
class TestListSimulations:
    def test_empty_list(self, client):
        response = client.get("/simulate")
        assert response.status_code == 200
        assert response.json() == []
