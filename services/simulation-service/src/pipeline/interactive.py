"""
Step 5 of MiroFish pipeline: Deep Interaction / Q&A.

Users can converse with the simulated agents or ReportAgent after
the simulation completes — asking follow-up questions against the
full debate context. Mirrors MiroFish's interactive exploration mode.
"""
from __future__ import annotations

import logging

from openai import AsyncOpenAI

from ..models import AgentRole, AskRequest, AskResponse, SimulationResult

logger = logging.getLogger(__name__)

_AGENT_PERSONAS: dict[AgentRole, str] = {
    AgentRole.BULL: (
        "You are the bullish portfolio manager from the simulation. You have strong conviction "
        "in upside scenarios. Answer from your persona — data-driven but optimistic."
    ),
    AgentRole.BEAR: (
        "You are the bearish hedge fund manager from the simulation. You are skeptical, "
        "focus on downside risks, and challenge consensus. Answer from your persona."
    ),
    AgentRole.ANALYST: (
        "You are the quantitative analyst from the simulation. Be precise, cite probabilities, "
        "and avoid expressing strong directional opinions. Stay neutral and data-focused."
    ),
    AgentRole.MACRO: (
        "You are the macro economist from the simulation. Think in regimes, scenarios, and "
        "macro flows. Connect monetary policy and geopolitics to asset prices."
    ),
    AgentRole.REPORT: (
        "You are the ReportAgent — an objective financial synthesizer. You have full knowledge "
        "of the simulation's debate and conclusions. Answer questions accurately and concisely, "
        "citing the debate evidence where relevant."
    ),
}


async def ask_simulation(
    simulation: SimulationResult,
    request: AskRequest,
    client: AsyncOpenAI,
    model: str,
) -> AskResponse:
    """
    Step 5: Interactive Q&A against the completed simulation.
    The user can address any agent persona or the ReportAgent directly.
    """
    responder_role = request.as_agent or AgentRole.REPORT
    persona = _AGENT_PERSONAS.get(responder_role, _AGENT_PERSONAS[AgentRole.REPORT])

    debate_summary = _build_debate_summary(simulation)
    report_summary = _build_report_summary(simulation)

    system_prompt = (
        f"{persona}\n\n"
        f"=== SIMULATION CONTEXT ===\n"
        f"Prediction Question: {simulation.request.prediction_query}\n\n"
        f"{report_summary}\n\n"
        f"=== KEY DEBATE EXCERPTS ===\n{debate_summary}"
    )

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.question},
        ],
        temperature=0.7,
        max_tokens=500,
    )

    answer = response.choices[0].message.content or "No response generated."

    logger.info(
        "Interactive Q&A: simulation=%s, responder=%s", simulation.simulation_id, responder_role
    )

    return AskResponse(
        simulation_id=simulation.simulation_id,
        question=request.question,
        responder=responder_role.value,
        answer=answer,
    )


def _build_debate_summary(simulation: SimulationResult) -> str:
    if not simulation.debate_transcript:
        return "(No debate transcript available)"
    # Show last round's messages as a representative sample
    max_round = max(m.round_number for m in simulation.debate_transcript)
    final_round = [m for m in simulation.debate_transcript if m.round_number == max_round]
    parts = [
        f"[{m.agent_role.upper()}]: {m.message[:300]}..." for m in final_round
    ]
    return "\n\n".join(parts)


def _build_report_summary(simulation: SimulationResult) -> str:
    if not simulation.report:
        return "(No report generated)"
    r = simulation.report
    v = r.verdict
    return (
        f"VERDICT: {v.direction.upper()} | Confidence: {v.confidence:.0%} | "
        f"Timeframe: {v.timeframe}\n"
        f"P(Up)={v.probability_up:.0%} | P(Down)={v.probability_down:.0%} | "
        f"P(Sideways)={v.probability_sideways:.0%}\n\n"
        f"EXECUTIVE SUMMARY:\n{r.executive_summary}"
    )
