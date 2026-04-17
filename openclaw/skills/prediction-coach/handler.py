"""
OpenClaw skill: prediction-coach
Grade a prediction market trade, audit Kelly compliance, detect biases.
Parses structured or free-form input from the user's message.
"""
from __future__ import annotations

import os
import re

import httpx

BASE_URL = os.getenv("PLUTOSAI_FINANCE_URL", "http://localhost:8008")
_CLIENT = httpx.AsyncClient(base_url=BASE_URL, timeout=55.0)


async def handle(message: str, context: dict) -> str:
    # Try to extract structured fields from the message
    fields = _parse_trade_message(message)

    if not fields.get("market") or not fields.get("position"):
        return _help_text()

    try:
        r = await _CLIENT.post("/skills/prediction-market-coach", json=fields)
        r.raise_for_status()
        grade = r.json()
    except Exception as exc:
        return f"⚠️ Trade coach unavailable: {exc}"

    grade_emoji = {"A": "🏆", "B": "✅", "C": "🟡", "D": "⚠️", "F": "🔴"}.get(
        grade["grade"], "❓"
    )
    kelly_emoji = {"optimal": "✅", "over": "🔴", "under": "🟡", "no_edge": "🚫"}.get(
        grade["kelly_compliance"], "❓"
    )

    biases = ", ".join(grade["biases_detected"]) if grade["biases_detected"] else "none detected"
    strengths = "\n".join(f"  ✅ {s}" for s in grade["strengths"][:3])
    improvements = "\n".join(f"  🔧 {i}" for i in grade["improvements"][:3])

    return (
        f"{grade_emoji} *Trade Grade: {grade['grade']}* (process score {grade['process_score']:.1f}/10)\n\n"
        f"*Kelly:* {kelly_emoji} {grade['kelly_compliance'].replace('_', ' ').title()}\n"
        f"  Recommended: {grade['kelly_recommended_pct']:.2f}% of bankroll\n\n"
        f"*Biases:* {biases}\n\n"
        + (f"*Strengths:*\n{strengths}\n\n" if strengths else "")
        + (f"*Improvements:*\n{improvements}\n\n" if improvements else "")
        + f"_{grade['coaching_note'][:300]}_"
    )


def _parse_trade_message(message: str) -> dict:
    """Extract trade fields from free-form message. Users can write naturally."""
    fields = {}

    # Market (everything before "position:" or first line)
    market_match = re.search(r"market[:\s]+(.+?)(?:\n|position:|$)", message, re.IGNORECASE)
    if market_match:
        fields["market"] = market_match.group(1).strip()
    else:
        # First meaningful line is the market description
        lines = [l.strip() for l in message.split("\n") if l.strip()]
        if lines:
            fields["market"] = lines[0]

    # Position
    pos_match = re.search(r"position[:\s]+(.+?)(?:\n|outcome:|$)", message, re.IGNORECASE)
    if pos_match:
        fields["position"] = pos_match.group(1).strip()

    # Outcome
    outcome_match = re.search(r"outcome[:\s]+(.+?)(?:\n|size:|$)", message, re.IGNORECASE)
    if outcome_match:
        fields["outcome"] = outcome_match.group(1).strip()
    else:
        for keyword in ["won", "lost", "win", "loss"]:
            if keyword in message.lower():
                fields["outcome"] = keyword
                break

    # Size %
    size_match = re.search(r"size[:\s]+([\d.]+)\s*%", message, re.IGNORECASE)
    if size_match:
        fields["size_pct_of_bankroll"] = float(size_match.group(1))

    # Edge
    edge_match = re.search(r"edge[:\s]+(0?\.\d+|[\d.]+%)", message, re.IGNORECASE)
    if edge_match:
        val = edge_match.group(1).rstrip("%")
        edge = float(val)
        if edge > 1:
            edge /= 100
        fields["estimated_edge_at_entry"] = edge

    # Odds
    odds_match = re.search(r"odds[:\s]+([\d.]+)", message, re.IGNORECASE)
    if odds_match:
        fields["odds_at_entry"] = float(odds_match.group(1))
    else:
        fields["odds_at_entry"] = 1.0

    # Defaults
    if "size_pct_of_bankroll" not in fields:
        fields["size_pct_of_bankroll"] = 2.0
    if "estimated_edge_at_entry" not in fields:
        fields["estimated_edge_at_entry"] = 0.52
    if "your_position" not in fields and "position" in fields:
        fields["your_position"] = fields.pop("position")
    if "market_description" not in fields and "market" in fields:
        fields["market_description"] = fields.pop("market")

    return fields


def _help_text() -> str:
    return (
        "🎯 *Prediction Market Coach*\n\n"
        "Send your trade for grading:\n\n"
        "```\nmarket: Will the ECB cut rates in June 2026?\n"
        "position: Yes at 65¢, because ECB inflation projections trending down\n"
        "outcome: Lost — ECB held rates, hawkish statement\n"
        "size: 3%\n"
        "edge: 0.58\n"
        "odds: 1.54\n```\n\n"
        "I'll grade on process (A-F), audit your Kelly sizing, and detect biases."
    )
