"""Pydantic models for the simulation service."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SimulationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRole(str, Enum):
    BULL = "bull"        # Optimistic market participant
    BEAR = "bear"        # Pessimistic / risk-focused participant
    ANALYST = "analyst"  # Neutral quantitative analyst
    MACRO = "macro"      # Macroeconomic perspective agent
    REPORT = "report"    # Final report synthesizer


class SimulationRequest(BaseModel):
    """Input for a new financial prediction simulation."""
    seed_text: str = Field(
        ...,
        description="Seed materials: market reports, news articles, financial signals",
        min_length=50,
        max_length=20_000,
    )
    prediction_query: str = Field(
        ...,
        description="Natural-language prediction question (e.g. 'Will DAX correct >5% in next 30 days?')",
        min_length=10,
        max_length=500,
    )
    rounds: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of debate rounds between agents (lower scale: 1-10)",
    )
    active_agents: list[AgentRole] = Field(
        default=[AgentRole.BULL, AgentRole.BEAR, AgentRole.ANALYST, AgentRole.MACRO],
        description="Which agent personas to activate for this simulation",
    )
    model: str = Field(
        default="gpt-4o",
        description="LLM model to use (OpenAI-compatible, swap to local Ollama endpoint)",
    )


class Entity(BaseModel):
    name: str
    entity_type: str  # asset, event, institution, person, indicator
    relevance: float  # 0.0-1.0


class KnowledgeGraph(BaseModel):
    entities: list[Entity]
    relationships: list[dict[str, str]]  # [{source, relation, target}]
    summary: str


class AgentMemory(BaseModel):
    agent_role: AgentRole
    initial_stance: str
    key_beliefs: list[str]


class RoundMessage(BaseModel):
    round_number: int
    agent_role: AgentRole
    message: str
    confidence: float  # 0.0-1.0 for their prediction stance
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PredictionVerdict(BaseModel):
    direction: str       # bullish / bearish / neutral / uncertain
    confidence: float    # 0.0-1.0 aggregate confidence
    timeframe: str       # extracted or inferred from query
    key_catalysts: list[str]
    key_risks: list[str]
    probability_up: float
    probability_down: float
    probability_sideways: float


class SimulationReport(BaseModel):
    executive_summary: str
    verdict: PredictionVerdict
    agent_consensus: dict[str, str]  # agent_role -> final stance
    key_debate_points: list[str]
    data_sources_used: list[str]
    caveats: list[str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class SimulationResult(BaseModel):
    simulation_id: str
    status: SimulationStatus
    request: SimulationRequest
    knowledge_graph: KnowledgeGraph | None = None
    agent_memories: list[AgentMemory] = []
    debate_transcript: list[RoundMessage] = []
    report: SimulationReport | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


class AskRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)
    as_agent: AgentRole | None = Field(
        default=None,
        description="Ask from the perspective of a specific agent, or None for ReportAgent",
    )


class AskResponse(BaseModel):
    simulation_id: str
    question: str
    responder: str
    answer: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
