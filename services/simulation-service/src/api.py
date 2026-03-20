"""
Simulation Service — MiroFish port for OpenClaw / Project Francesca.

FastAPI application exposing the 5-stage financial prediction simulation pipeline:
  1. Knowledge Graph Construction  (extract entities from seed text)
  2. Agent Environment Setup        (generate financial agent personas)
  3. Simulation Execution           (N-round debate: Bull vs Bear vs Analyst vs Macro)
  4. Report Generation              (ReportAgent synthesizes structured prediction)
  5. Interactive Q&A                (post-simulation agent interrogation)

Port 8005 — registered in gateway as /simulate/*
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException, Request
from openai import AsyncOpenAI
from prometheus_fastapi_instrumentator import Instrumentator

from .config import settings
from .models import (
    AskRequest,
    AskResponse,
    SimulationRequest,
    SimulationResult,
    SimulationStatus,
)
from .pipeline.environment import setup_agent_environment
from .pipeline.interactive import ask_simulation
from .pipeline.knowledge_extractor import extract_knowledge_graph
from .pipeline.reporter import generate_report
from .pipeline.simulator import run_simulation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory store for this lower-scale implementation.
# In production swap to Redis persistence or a DB-backed store.
# ---------------------------------------------------------------------------
_simulations: dict[str, SimulationResult] = {}
_redis: aioredis.Redis | None = None
_openai_client: AsyncOpenAI | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _redis, _openai_client
    # Connect Redis (non-fatal if unavailable — fall back to in-memory only)
    try:
        _redis = aioredis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True,
        )
        await _redis.ping()
        logger.info("Redis connected at %s:%d", settings.redis_host, settings.redis_port)
    except Exception as exc:
        logger.warning("Redis unavailable (%s) — using in-memory store only", exc)
        _redis = None

    # Build OpenAI client (OpenAI-compatible — works with local Ollama, PGX Nemotron, etc.)
    _openai_client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )
    logger.info("LLM client ready → %s (model: %s)", settings.openai_base_url, settings.default_model)

    yield

    if _redis:
        await _redis.aclose()


app = FastAPI(
    title="Simulation Service — Financial Prediction Engine",
    description=(
        "MiroFish-inspired multi-agent financial prediction simulation for OpenClaw. "
        "Upload seed materials, describe your prediction question, receive a structured "
        "market forecast backed by a Bull/Bear/Analyst/Macro agent debate."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health", tags=["ops"])
async def health() -> dict[str, Any]:
    redis_ok = False
    if _redis:
        try:
            await _redis.ping()
            redis_ok = True
        except Exception:
            pass
    return {
        "status": "healthy",
        "service": "simulation-service",
        "redis": redis_ok,
        "active_simulations": len(_simulations),
    }


# ---------------------------------------------------------------------------
# POST /simulate — Start a new simulation
# ---------------------------------------------------------------------------
@app.post("/simulate", response_model=SimulationResult, status_code=202, tags=["simulation"])
async def start_simulation(request: SimulationRequest) -> SimulationResult:
    """
    Start a new financial prediction simulation.

    The pipeline runs asynchronously in the background:
    1. Extract knowledge graph from seed_text
    2. Setup agent personas
    3. Run N-round debate
    4. Generate prediction report

    Poll GET /simulate/{id} for status and final results.
    """
    simulation_id = str(uuid.uuid4())
    result = SimulationResult(
        simulation_id=simulation_id,
        status=SimulationStatus.PENDING,
        request=request,
    )
    _simulations[simulation_id] = result

    # Fire and forget — background task
    asyncio.create_task(_run_pipeline(simulation_id, request))

    logger.info("Simulation %s queued", simulation_id)
    return result


# ---------------------------------------------------------------------------
# GET /simulate/{id} — Poll for results
# ---------------------------------------------------------------------------
@app.get("/simulate/{simulation_id}", response_model=SimulationResult, tags=["simulation"])
async def get_simulation(simulation_id: str) -> SimulationResult:
    """Poll for simulation status and results."""
    sim = _simulations.get(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail=f"Simulation '{simulation_id}' not found")
    return sim


# ---------------------------------------------------------------------------
# GET /simulate — List recent simulations
# ---------------------------------------------------------------------------
@app.get("/simulate", response_model=list[SimulationResult], tags=["simulation"])
async def list_simulations(limit: int = 20) -> list[SimulationResult]:
    """List recent simulations (newest first)."""
    all_sims = sorted(
        _simulations.values(), key=lambda s: s.created_at, reverse=True
    )
    return all_sims[:limit]


# ---------------------------------------------------------------------------
# POST /simulate/{id}/ask — Interactive Q&A (Step 5)
# ---------------------------------------------------------------------------
@app.post("/simulate/{simulation_id}/ask", response_model=AskResponse, tags=["interactive"])
async def ask(simulation_id: str, request: AskRequest) -> AskResponse:
    """
    Ask a follow-up question to a completed simulation.

    You can address a specific agent persona (bull/bear/analyst/macro)
    or leave as_agent=null to query the ReportAgent.

    Mirrors MiroFish's 'deep interaction' mode.
    """
    sim = _simulations.get(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail=f"Simulation '{simulation_id}' not found")
    if sim.status != SimulationStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Simulation is {sim.status.value} — wait for COMPLETED before asking",
        )
    if _openai_client is None:
        raise HTTPException(status_code=503, detail="LLM client not ready")

    return await ask_simulation(
        simulation=sim,
        request=request,
        client=_openai_client,
        model=sim.request.model,
    )


# ---------------------------------------------------------------------------
# DELETE /simulate/{id} — Clean up
# ---------------------------------------------------------------------------
@app.delete("/simulate/{simulation_id}", status_code=204, tags=["simulation"])
async def delete_simulation(simulation_id: str) -> None:
    """Remove a simulation from the store."""
    if simulation_id not in _simulations:
        raise HTTPException(status_code=404, detail=f"Simulation '{simulation_id}' not found")
    del _simulations[simulation_id]


# ---------------------------------------------------------------------------
# Background pipeline runner
# ---------------------------------------------------------------------------
async def _run_pipeline(simulation_id: str, request: SimulationRequest) -> None:
    """Execute the full 5-stage MiroFish pipeline for one simulation."""
    sim = _simulations[simulation_id]
    client = _openai_client
    if client is None:
        sim.status = SimulationStatus.FAILED
        sim.error = "LLM client not initialised"
        return

    try:
        sim.status = SimulationStatus.RUNNING

        # Stage 1: Knowledge Graph
        logger.info("[%s] Stage 1: Knowledge extraction", simulation_id)
        kg = await extract_knowledge_graph(
            seed_text=request.seed_text,
            client=client,
            model=request.model,
        )
        sim.knowledge_graph = kg

        # Stage 2: Agent Environment Setup
        logger.info("[%s] Stage 2: Agent environment setup", simulation_id)
        memories = await setup_agent_environment(
            knowledge_graph=kg,
            prediction_query=request.prediction_query,
            active_agents=request.active_agents,
            client=client,
            model=request.model,
        )
        sim.agent_memories = memories

        # Stage 3: Simulation Execution
        logger.info("[%s] Stage 3: Running simulation (%d rounds)", simulation_id, request.rounds)
        transcript = await run_simulation(
            knowledge_graph=kg,
            agent_memories=memories,
            prediction_query=request.prediction_query,
            rounds=request.rounds,
            client=client,
            model=request.model,
        )
        sim.debate_transcript = transcript

        # Stage 4: Report Generation
        logger.info("[%s] Stage 4: Generating report", simulation_id)
        report = await generate_report(
            knowledge_graph=kg,
            transcript=transcript,
            prediction_query=request.prediction_query,
            client=client,
            model=request.model,
        )
        sim.report = report

        sim.status = SimulationStatus.COMPLETED
        sim.completed_at = datetime.now(tz=timezone.utc)
        logger.info("[%s] Simulation COMPLETED", simulation_id)

    except Exception as exc:
        logger.exception("[%s] Simulation FAILED: %s", simulation_id, exc)
        sim.status = SimulationStatus.FAILED
        sim.error = str(exc)
