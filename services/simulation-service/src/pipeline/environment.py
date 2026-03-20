"""
Step 2 of MiroFish pipeline: Agent Environment Setup.

Generates financial agent personas with distinct beliefs and memory stances,
injecting the knowledge graph as shared world-state.
"""
from __future__ import annotations

import json
import logging

from openai import AsyncOpenAI

from ..models import AgentMemory, AgentRole, KnowledgeGraph

logger = logging.getLogger(__name__)

# Per-role system prompts — each agent has a distinct personality and analytical lens
_ROLE_PERSONAS: dict[AgentRole, str] = {
    AgentRole.BULL: (
        "You are a seasoned equity portfolio manager with a systematic long-bias. "
        "You seek asymmetric upside opportunities, trust in trend continuation, "
        "and weigh positive catalysts more heavily. You respect risk management "
        "but believe markets trend up over time. You speak with conviction."
    ),
    AgentRole.BEAR: (
        "You are a macro hedge fund manager who specialises in identifying overvaluation, "
        "systemic risks, and tail events. You are skeptical of consensus narratives, "
        "closely track credit spreads and liquidity conditions, and often spot downside "
        "risks others dismiss. You are blunt and data-driven."
    ),
    AgentRole.ANALYST: (
        "You are a quantitative strategist at a top-tier bank. You rely on technicals, "
        "factor models, and statistical evidence. You avoid opinion and anchor to data. "
        "You quantify probabilities and acknowledge uncertainty explicitly. "
        "You are precise and hedge your language carefully."
    ),
    AgentRole.MACRO: (
        "You are a former central bank economist turned macro strategist. You focus on "
        "monetary policy cycles, fiscal dynamics, inflation regimes, and geopolitical risk. "
        "You think in 6-18 month horizons and connect macro flows to asset price implications. "
        "You are measured and speak in scenarios."
    ),
}

_STANCE_SYSTEM = """\
You are a {role_description}

Given this financial knowledge graph and context, generate your initial analytical stance
for the prediction question asked.

Return a JSON object:
{
  "initial_stance": "<one paragraph describing your initial position on the prediction>",
  "key_beliefs": ["<belief 1>", "<belief 2>", "<belief 3>", "<belief 4>", "<belief 5>"]
}

Be specific to the entities in the knowledge graph. Stay true to your persona.
"""


async def setup_agent_environment(
    knowledge_graph: KnowledgeGraph,
    prediction_query: str,
    active_agents: list[AgentRole],
    client: AsyncOpenAI,
    model: str,
) -> list[AgentMemory]:
    """
    Step 2: Generate agent personas with initial stances based on the knowledge graph.
    Each agent gets a distinct personality + initial memory about the prediction question.
    """
    logger.info("Setting up environment for %d agents", len(active_agents))

    context = _build_context(knowledge_graph, prediction_query)
    memories: list[AgentMemory] = []

    for role in active_agents:
        if role == AgentRole.REPORT:
            continue  # Report agent has no initial stance — it synthesizes

        persona = _ROLE_PERSONAS.get(role, "You are a financial analyst.")
        system = _STANCE_SYSTEM.format(role_description=persona)

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": context},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )

        raw = response.choices[0].message.content or "{}"
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {
                "initial_stance": f"[Parse error] {raw[:200]}",
                "key_beliefs": [],
            }

        memories.append(
            AgentMemory(
                agent_role=role,
                initial_stance=data.get("initial_stance", ""),
                key_beliefs=data.get("key_beliefs", []),
            )
        )
        logger.debug("Agent %s initialized with stance: %s", role, data.get("initial_stance", "")[:80])

    return memories


def _build_context(knowledge_graph: KnowledgeGraph, prediction_query: str) -> str:
    entities_str = "\n".join(
        f"- {e.name} ({e.entity_type}, relevance={e.relevance:.2f})"
        for e in knowledge_graph.entities[:15]
    )
    rels_str = "\n".join(
        f"- {r.get('source')} → {r.get('relation')} → {r.get('target')}"
        for r in knowledge_graph.relationships[:10]
    )
    return (
        f"WORLD CONTEXT SUMMARY:\n{knowledge_graph.summary}\n\n"
        f"KEY ENTITIES:\n{entities_str}\n\n"
        f"RELATIONSHIPS:\n{rels_str}\n\n"
        f"PREDICTION QUESTION: {prediction_query}"
    )
