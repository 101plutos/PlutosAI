"""Unit tests for simulation service models and pipeline utilities."""
from __future__ import annotations

import pytest

from src.models import (
    AgentRole,
    AskRequest,
    KnowledgeGraph,
    SimulationRequest,
    SimulationStatus,
    Entity,
)
from src.pipeline.simulator import _extract_confidence, _format_history
from src.models import RoundMessage
from datetime import datetime


# ---------------------------------------------------------------------------
# Model validation tests
# ---------------------------------------------------------------------------
class TestSimulationRequest:
    def test_valid_request(self):
        req = SimulationRequest(
            seed_text="A" * 100,
            prediction_query="Will DAX drop 5% in 30 days?",
        )
        assert req.rounds == 3
        assert AgentRole.BULL in req.active_agents

    def test_seed_too_short_raises(self):
        with pytest.raises(Exception):
            SimulationRequest(seed_text="short", prediction_query="Will markets rally?")

    def test_query_too_short_raises(self):
        with pytest.raises(Exception):
            SimulationRequest(seed_text="A" * 100, prediction_query="?")

    def test_rounds_clamped(self):
        with pytest.raises(Exception):
            SimulationRequest(seed_text="A" * 100, prediction_query="Will markets rally?", rounds=99)


class TestKnowledgeGraph:
    def test_entity_creation(self):
        e = Entity(name="DAX 40", entity_type="asset", relevance=0.9)
        assert e.relevance == 0.9

    def test_kg_creation(self):
        kg = KnowledgeGraph(
            entities=[Entity(name="DAX 40", entity_type="asset", relevance=0.9)],
            relationships=[{"source": "ECB", "relation": "sets_rates_for", "target": "EUR"}],
            summary="Test summary",
        )
        assert len(kg.entities) == 1


class TestAskRequest:
    def test_defaults_to_report_agent(self):
        r = AskRequest(question="What is the main risk?")
        assert r.as_agent is None

    def test_explicit_agent(self):
        r = AskRequest(question="What is the main risk?", as_agent=AgentRole.BEAR)
        assert r.as_agent == AgentRole.BEAR


# ---------------------------------------------------------------------------
# Pipeline utility tests
# ---------------------------------------------------------------------------
class TestExtractConfidence:
    def test_valid_confidence(self):
        text = "Markets look overvalued here. [CONFIDENCE: 0.75]"
        assert _extract_confidence(text) == 0.75

    def test_clamps_above_one(self):
        text = "Very confident. [CONFIDENCE: 1.5]"
        assert _extract_confidence(text) == 1.0

    def test_clamps_below_zero(self):
        text = "No idea. [CONFIDENCE: -0.3]"
        assert _extract_confidence(text) == 0.0

    def test_missing_tag_returns_fallback(self):
        assert _extract_confidence("No confidence tag here") == 0.5

    def test_malformed_tag(self):
        assert _extract_confidence("[CONFIDENCE: abc]") == 0.5


class TestFormatHistory:
    def test_empty_returns_empty(self):
        assert _format_history([]) == ""

    def test_single_message(self):
        msgs = [
            RoundMessage(
                round_number=1,
                agent_role=AgentRole.BULL,
                message="Markets will rise.",
                confidence=0.8,
                timestamp=datetime.utcnow(),
            )
        ]
        result = _format_history(msgs)
        assert "BULL" in result
        assert "Markets will rise." in result
        assert "confidence=0.80" in result

    def test_limits_to_last_12(self):
        msgs = [
            RoundMessage(
                round_number=i,
                agent_role=AgentRole.ANALYST,
                message=f"Message {i}",
                confidence=0.5,
                timestamp=datetime.utcnow(),
            )
            for i in range(1, 20)
        ]
        result = _format_history(msgs)
        # Should not include earliest messages
        assert "Message 1" not in result
        assert "Message 19" in result


# ---------------------------------------------------------------------------
# Status enum
# ---------------------------------------------------------------------------
class TestSimulationStatus:
    def test_all_statuses_accessible(self):
        assert SimulationStatus.PENDING == "pending"
        assert SimulationStatus.RUNNING == "running"
        assert SimulationStatus.COMPLETED == "completed"
        assert SimulationStatus.FAILED == "failed"
