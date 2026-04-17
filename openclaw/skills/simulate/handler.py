"""
OpenClaw skill: simulate
Routes to simulation-service (MiroFish engine) — BULL, BEAR, ANALYST, MACRO
debate a question across N rounds, REPORT synthesises consensus.

Supports both async polling (large sims) and single-ask mode.
"""
from __future__ import annotations

import asyncio
import os
import re

import httpx

BASE_URL = os.getenv("PLUTOSAI_SIMULATION_URL", "http://localhost:8007")
_CLIENT = httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)


async def handle(message: str, context: dict) -> str:
    msg_lower = message.lower()

    # Route: list recent simulations
    if any(k in msg_lower for k in ["list simulations", "recent sims", "simulation history"]):
        return await _list_simulations()

    # Route: query an existing simulation
    sim_id_match = re.search(r"\b(sim[-_]?[a-f0-9\-]{8,})\b", message, re.IGNORECASE)
    if sim_id_match and any(k in msg_lower for k in ["ask", "query", "what does", "tell me about"]):
        return await _ask_simulation(sim_id_match.group(1), message)

    # Default: start a new simulation
    question, rounds, ctx = _parse_request(message)
    if not question:
        return _help_text()
    return await _start_simulation(question, rounds, ctx)


async def _start_simulation(question: str, rounds: int, ctx: str) -> str:
    payload = {
        "question": question,
        "rounds": rounds,
        "context": ctx or "",
    }
    try:
        r = await _CLIENT.post("/simulate", json=payload)
        r.raise_for_status()
        d = r.json()
    except Exception as exc:
        return f"⚠️ Simulation service unavailable: {exc}"

    sim_id = d.get("simulation_id", "unknown")
    est = d.get("estimated_duration_seconds", 120)
    est_min = round(est / 60, 1)

    # Poll for completion (up to timeout)
    result = await _poll_until_complete(sim_id, timeout=540)
    if result is None:
        return (
            f"⏳ Simulation `{sim_id}` is running (~{est_min} min).\n\n"
            f"Check progress: `simulate status {sim_id}`\n"
            f"Ask the result: `simulate ask {sim_id} what is the probability?`"
        )
    return _format_result(result, sim_id)


async def _poll_until_complete(sim_id: str, timeout: int = 540) -> dict | None:
    """Poll simulation status until complete or timeout."""
    poll_client = httpx.AsyncClient(base_url=BASE_URL, timeout=15.0)
    elapsed = 0
    interval = 8  # seconds between polls

    try:
        while elapsed < timeout:
            await asyncio.sleep(interval)
            elapsed += interval
            try:
                r = await poll_client.get(f"/simulate/{sim_id}")
                r.raise_for_status()
                d = r.json()
                if d.get("status") == "completed":
                    return d
                if d.get("status") == "failed":
                    return None
            except Exception:
                pass
    finally:
        await poll_client.aclose()
    return None


async def _ask_simulation(sim_id: str, message: str) -> str:
    """Ask a follow-up question to a completed simulation."""
    # Strip the sim ID and trigger words to get the actual question
    question = re.sub(
        r"\b(sim[-_]?[a-f0-9\-]{8,}|ask|query|tell me)\b", "", message, flags=re.IGNORECASE
    ).strip() or "Summarise the key findings and probabilities."

    try:
        r = await _CLIENT.post(f"/simulate/{sim_id}/ask", json={"question": question})
        r.raise_for_status()
        d = r.json()
    except Exception as exc:
        return f"⚠️ Could not query simulation {sim_id}: {exc}"

    return f"💬 *Simulation {sim_id[:8]}…*\n\n{d.get('answer', str(d))}"


async def _list_simulations() -> str:
    try:
        r = await _CLIENT.get("/simulate")
        r.raise_for_status()
        sims = r.json()
    except Exception as exc:
        return f"⚠️ Simulation service unavailable: {exc}"

    if not sims:
        return "No simulations yet. Start one: `simulate BTC bull run scenario`"

    lines = ["*Recent Simulations:*", ""]
    for s in sims[:5]:
        status_emoji = {"completed": "✅", "running": "⏳", "failed": "❌"}.get(
            s.get("status", ""), "❓"
        )
        lines.append(
            f"{status_emoji} `{s['simulation_id'][:12]}…` — {s.get('question', '')[:50]}"
        )
    return "\n".join(lines)


def _format_result(result: dict, sim_id: str) -> str:
    """Format a completed simulation result for messaging delivery."""
    report = result.get("report", {})
    question = result.get("question", "")
    consensus = report.get("consensus_probability")
    direction = report.get("direction", "uncertain")
    summary = report.get("summary", "")
    key_factors = report.get("key_factors", [])
    risks = report.get("key_risks", [])

    dir_emoji = {"bullish": "📈", "bearish": "📉", "neutral": "⚖️", "uncertain": "❓"}.get(
        direction, "❓"
    )
    prob_str = f"{consensus:.0%}" if consensus is not None else "N/A"

    factors = "\n".join(f"  • {f}" for f in (key_factors or [])[:3])
    risk_lines = "\n".join(f"  ⚠️ {r}" for r in (risks or [])[:3])

    lines = [
        f"🤖 *MiroFish Prediction* (ID: `{sim_id[:12]}…`)",
        f"Q: _{question[:100]}_",
        "",
        f"Consensus: {dir_emoji} *{direction.title()}* — Probability: *{prob_str}*",
        "",
    ]
    if summary:
        lines.append(f"{summary[:400]}")
        lines.append("")
    if factors:
        lines.append(f"*Key Factors:*\n{factors}")
        lines.append("")
    if risk_lines:
        lines.append(f"*Key Risks:*\n{risk_lines}")

    # Agent breakdown if available
    agent_views = result.get("agent_views", {})
    if agent_views:
        lines.append("")
        lines.append("*Agent Views:*")
        for agent, view in agent_views.items():
            lines.append(f"  {agent}: {str(view)[:80]}")

    return "\n".join(lines)


def _parse_request(message: str) -> tuple[str, int, str]:
    """Extract question, rounds, and context from free-form message."""
    # Rounds: "3 rounds", "rounds: 4"
    rounds_match = re.search(r"(\d)\s*rounds?", message, re.IGNORECASE)
    rounds = int(rounds_match.group(1)) if rounds_match else 3
    rounds = max(1, min(rounds, 5))

    # Context: after "context:" or "given:"
    ctx_match = re.search(r"(?:context|given|background)[:\s]+(.+?)(?:\n|$)", message, re.IGNORECASE)
    ctx = ctx_match.group(1).strip() if ctx_match else ""

    # Question: strip trigger words and meta-fields
    question = re.sub(r"\b(\d\s*rounds?|context:.+|given:.+)\b", "", message, flags=re.IGNORECASE)
    question = re.sub(
        r"^(simulate|predict|forecast|what happens if|scenario analysis)\s*",
        "", question.strip(), flags=re.IGNORECASE,
    ).strip()

    return question, rounds, ctx


def _help_text() -> str:
    return (
        "🤖 *MiroFish Simulation*\n\n"
        "BULL, BEAR, ANALYST, and MACRO debate your question across multiple rounds.\n\n"
        "**Examples:**\n"
        "```\nsimulate Will BTC reach $150k by end of 2026?\n```\n"
        "```\npredict ECB cuts rates 3 times in 2026\n  context: CPI at 2.1%, GDP slowing\n```\n"
        "```\nscenario analysis DAX if Fed goes hawkish in Q2\n  3 rounds\n```\n\n"
        "Check status: `simulate status <sim-id>`\n"
        "Ask follow-up: `simulate ask <sim-id> what's the bull case target?`\n"
        "List recent: `list simulations`"
    )
