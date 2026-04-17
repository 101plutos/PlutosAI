"""
Step 4 of MiroFish pipeline: Report Generation.

The ReportAgent synthesizes the full debate transcript and knowledge graph
into a structured financial prediction report — analogous to MiroFish's ReportAgent
that "deeply interacts with the post-simulation environment."
"""
from __future__ import annotations

import json
import logging

from openai import AsyncOpenAI

from ..models import (
    AgentRole,
    KnowledgeGraph,
    PredictionVerdict,
    RoundMessage,
    SimulationReport,
)

logger = logging.getLogger(__name__)

_REPORT_SYSTEM = """\
You are a Senior Financial Report Analyst. Your job is to synthesize a multi-agent debate
into a structured, actionable prediction report — in the style of Goldman Sachs or JPMorgan
research. Be objective, precise, and quantify uncertainty.

Given: knowledge graph context, agent debate transcript, and the prediction question.

Return a JSON object:
{
  "executive_summary": "<3-5 sentences: what was debated, what was concluded, key uncertainties>",
  "verdict": {
    "direction": "<bullish|bearish|neutral|uncertain>",
    "confidence": <0.0-1.0 aggregate>,
    "timeframe": "<extracted or inferred timeframe, e.g. '30 days', '3 months'>",
    "key_catalysts": ["<catalyst 1>", "<catalyst 2>", "<catalyst 3>"],
    "key_risks": ["<risk 1>", "<risk 2>", "<risk 3>"],
    "probability_up": <0.0-1.0>,
    "probability_down": <0.0-1.0>,
    "probability_sideways": <0.0-1.0>
  },
  "agent_consensus": {
    "bull": "<final stance of bull agent in one sentence>",
    "bear": "<final stance of bear agent in one sentence>",
    "analyst": "<final stance of analyst agent in one sentence>",
    "macro": "<final stance of macro agent in one sentence>"
  },
  "key_debate_points": [
    "<most important argument from the debate>",
    "<second most important>",
    "<third most important>"
  ],
  "data_sources_used": ["<entity/source referenced in debate>"],
  "caveats": [
    "This is a simulation — not financial advice.",
    "<specific caveat about data limitations>",
    "<specific caveat about model assumptions>"
  ]
}

Ensure probability_up + probability_down + probability_sideways = 1.0.
"""


async def generate_report(
    knowledge_graph: KnowledgeGraph,
    transcript: list[RoundMessage],
    prediction_query: str,
    client: AsyncOpenAI,
    model: str,
) -> SimulationReport:
    """
    Step 4: ReportAgent synthesizes the debate into a structured prediction report.
    """
    logger.info("Generating report from %d debate messages", len(transcript))

    context = _build_report_context(knowledge_graph, transcript, prediction_query)

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _REPORT_SYSTEM},
            {"role": "user", "content": context},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=1500,
    )

    raw = response.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Failed to parse report JSON")
        data = _fallback_report(prediction_query)

    # Normalise probabilities
    verdict_data = data.get("verdict", {})
    up = float(verdict_data.get("probability_up", 0.33))
    down = float(verdict_data.get("probability_down", 0.33))
    side = float(verdict_data.get("probability_sideways", 0.34))
    total = up + down + side
    if total > 0 and abs(total - 1.0) > 0.01:
        up, down, side = up / total, down / total, side / total

    verdict = PredictionVerdict(
        direction=verdict_data.get("direction", "uncertain"),
        confidence=float(verdict_data.get("confidence", 0.5)),
        timeframe=verdict_data.get("timeframe", "unspecified"),
        key_catalysts=verdict_data.get("key_catalysts", []),
        key_risks=verdict_data.get("key_risks", []),
        probability_up=round(up, 3),
        probability_down=round(down, 3),
        probability_sideways=round(side, 3),
    )

    # Only include agent roles that actually participated
    agent_roles = {AgentRole.BULL, AgentRole.BEAR, AgentRole.ANALYST, AgentRole.MACRO}
    participated = {msg.agent_role for msg in transcript}
    agent_consensus_raw = data.get("agent_consensus", {})
    agent_consensus = {
        role.value: agent_consensus_raw.get(role.value, "Did not participate")
        for role in agent_roles
        if role in participated
    }

    return SimulationReport(
        executive_summary=data.get("executive_summary", ""),
        verdict=verdict,
        agent_consensus=agent_consensus,
        key_debate_points=data.get("key_debate_points", []),
        data_sources_used=data.get("data_sources_used", []),
        caveats=data.get("caveats", ["This is a simulation — not financial advice."]),
    )


def _build_report_context(
    knowledge_graph: KnowledgeGraph,
    transcript: list[RoundMessage],
    prediction_query: str,
) -> str:
    entities_str = ", ".join(e.name for e in knowledge_graph.entities[:10])
    debate_str = "\n\n".join(
        f"[Round {m.round_number} | {m.agent_role.upper()} | confidence={m.confidence:.2f}]\n{m.message}"
        for m in transcript
    )
    return (
        f"PREDICTION QUESTION: {prediction_query}\n\n"
        f"KEY ENTITIES IN CONTEXT: {entities_str}\n\n"
        f"WORLD SUMMARY: {knowledge_graph.summary}\n\n"
        f"=== FULL DEBATE TRANSCRIPT ===\n\n{debate_str}"
    )


def _fallback_report(prediction_query: str) -> dict:
    return {
        "executive_summary": f"Report generation encountered an error for query: {prediction_query}",
        "verdict": {
            "direction": "uncertain",
            "confidence": 0.0,
            "timeframe": "unknown",
            "key_catalysts": [],
            "key_risks": ["Report generation failed"],
            "probability_up": 0.33,
            "probability_down": 0.33,
            "probability_sideways": 0.34,
        },
        "agent_consensus": {},
        "key_debate_points": [],
        "data_sources_used": [],
        "caveats": ["Report generation failed — simulation data may be incomplete."],
    }
