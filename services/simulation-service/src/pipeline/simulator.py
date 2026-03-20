"""
Step 3 of MiroFish pipeline: Simulation Execution.

Runs N rounds of structured debate between financial agents.
Each round: agents respond to each other's arguments, update stances,
and dynamically converge or diverge — mimicking real market analyst debate.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from openai import AsyncOpenAI

from ..models import AgentMemory, AgentRole, KnowledgeGraph, RoundMessage

logger = logging.getLogger(__name__)

_DEBATE_SYSTEM = """\
You are a {persona_description}

WORLD CONTEXT:
{world_context}

YOUR INITIAL STANCE:
{initial_stance}

YOUR CORE BELIEFS:
{beliefs}

DEBATE HISTORY SO FAR:
{history}

Now write your contribution to round {round_num} of the debate.
Respond to the strongest opposing argument above. Update your stance if the evidence warrants it.
Be specific — reference entities, data points, and your analytical framework.

End with a confidence score from 0.0 (completely uncertain) to 1.0 (very high conviction)
in the format: [CONFIDENCE: X.XX]
"""

_PERSONAS: dict[AgentRole, str] = {
    AgentRole.BULL: "long-bias portfolio manager (bullish, momentum-focused)",
    AgentRole.BEAR: "macro hedge fund manager (skeptical, risk-focused, contrarian)",
    AgentRole.ANALYST: "quantitative strategist (data-driven, neutral, probabilistic)",
    AgentRole.MACRO: "macro economist (regime-focused, 6-18 month horizon, scenario-based)",
}

_CONFIDENCE_FALLBACK = 0.5


async def run_simulation(
    knowledge_graph: KnowledgeGraph,
    agent_memories: list[AgentMemory],
    prediction_query: str,
    rounds: int,
    client: AsyncOpenAI,
    model: str,
) -> list[RoundMessage]:
    """
    Run N rounds of multi-agent debate.
    Returns the full debate transcript as a list of RoundMessages.
    """
    logger.info("Starting simulation: %d rounds, %d agents", rounds, len(agent_memories))

    world_context = (
        f"{knowledge_graph.summary}\n\nPrediction Question: {prediction_query}"
    )
    transcript: list[RoundMessage] = []

    for round_num in range(1, rounds + 1):
        logger.info("Running round %d/%d", round_num, rounds)

        history_text = _format_history(transcript)
        # Run all agents concurrently within each round
        tasks = [
            _run_agent_turn(
                memory=memory,
                round_num=round_num,
                world_context=world_context,
                history_text=history_text,
                client=client,
                model=model,
            )
            for memory in agent_memories
        ]
        round_messages = await asyncio.gather(*tasks)
        transcript.extend(round_messages)

    logger.info("Simulation complete: %d total messages", len(transcript))
    return transcript


async def _run_agent_turn(
    memory: AgentMemory,
    round_num: int,
    world_context: str,
    history_text: str,
    client: AsyncOpenAI,
    model: str,
) -> RoundMessage:
    persona = _PERSONAS.get(memory.agent_role, "financial analyst")
    beliefs_str = "\n".join(f"- {b}" for b in memory.key_beliefs)

    system_prompt = _DEBATE_SYSTEM.format(
        persona_description=persona,
        world_context=world_context,
        initial_stance=memory.initial_stance,
        beliefs=beliefs_str,
        history=history_text or "(This is the opening round — no prior debate.)",
        round_num=round_num,
    )

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Round {round_num}: Make your case."},
            ],
            temperature=0.8,
            max_tokens=600,
        )
        content = response.choices[0].message.content or ""
    except Exception as exc:
        logger.error("Agent %s failed in round %d: %s", memory.agent_role, round_num, exc)
        content = f"[Agent error: {exc}]"

    confidence = _extract_confidence(content)
    # Strip the confidence tag from the message body
    clean_message = content.split("[CONFIDENCE:")[0].strip()

    return RoundMessage(
        round_number=round_num,
        agent_role=memory.agent_role,
        message=clean_message,
        confidence=confidence,
        timestamp=datetime.utcnow(),
    )


def _format_history(transcript: list[RoundMessage]) -> str:
    if not transcript:
        return ""
    parts = []
    for msg in transcript[-12:]:  # Keep last 12 messages in context window
        parts.append(
            f"[Round {msg.round_number} | {msg.agent_role.upper()}] "
            f"(confidence={msg.confidence:.2f})\n{msg.message}"
        )
    return "\n\n---\n\n".join(parts)


def _extract_confidence(text: str) -> float:
    try:
        if "[CONFIDENCE:" in text:
            tag = text.split("[CONFIDENCE:")[1].split("]")[0].strip()
            return max(0.0, min(1.0, float(tag)))
    except (IndexError, ValueError):
        pass
    return _CONFIDENCE_FALLBACK
