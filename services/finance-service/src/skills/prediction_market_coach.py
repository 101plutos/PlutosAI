"""
prediction-market-coach skill — Project Francesca.

Grades trades A–F on process (not outcome), audits Kelly compliance,
and detects behavioural biases. Used by: QUANT, STRATEGOS, TRAINER.

Grading rubric:
  A: Excellent process — well-researched edge, correct Kelly, no identifiable bias
  B: Good — minor sizing or reasoning gap
  C: Acceptable — some process flaws, luck component large
  D: Poor — significant bias or Kelly violation
  F: Unacceptable — gambling, no edge, major Kelly breach
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from openai import AsyncOpenAI

from ..config import settings
from ..models import TradeGrade, TradeGradeRequest

logger = logging.getLogger(__name__)

_COACH_SYSTEM = """\
You are a prediction market trading coach — rigorous, direct, and data-driven.
Grade this trade on PROCESS only, not outcome. A lucky win with bad process is still a D.

Grading rubric:
  A (9-10): Excellent — clear edge, correct Kelly, disciplined sizing, no bias
  B (7-8):  Good — minor gap in reasoning or slight over/under-sizing
  C (5-6):  Acceptable — process flaws, identifiable bias, sizing off
  D (3-4):  Poor — significant bias, material Kelly violation, weak edge thesis
  F (0-2):  Unacceptable — gambling, no edge, major Kelly breach or emotional trade

Known biases to detect:
  - overconfidence (edges > 60% without rigorous evidence)
  - recency_bias (weighting recent events too heavily)
  - outcome_bias (judging quality by result not process)
  - loss_aversion (closing winners too early, holding losers)
  - availability_bias (overweighting vivid recent events)
  - football_overconcentration (a known weakness — excessive focus on football markets)
  - anchoring (anchoring to entry price in exit decisions)

Kelly formula: f* = (bp - q) / b  → fractional = f* / 3

Return a structured coaching report. Be specific. Reference the trade details provided.
"""


async def grade_trade(
    request: TradeGradeRequest,
    client: AsyncOpenAI,
    model: str,
) -> TradeGrade:
    """Grade a prediction market trade A–F on process quality."""
    logger.info("prediction-market-coach: grading trade in %s", request.market_description[:40])

    # Compute optimal Kelly for comparison
    p = request.estimated_edge_at_entry
    q = 1.0 - p
    b = request.odds_at_entry
    full_kelly = max(0.0, (b * p - q) / b) if b > 0 else 0.0
    fractional_kelly = round(full_kelly / 3, 4)
    kelly_pct = round(fractional_kelly * 100, 2)

    sizing_verdict = _kelly_verdict(request.size_pct_of_bankroll, kelly_pct)

    user_prompt = (
        f"Market: {request.market_description}\n"
        f"Position: {request.your_position}\n"
        f"Outcome: {request.outcome}\n"
        f"Size: {request.size_pct_of_bankroll:.1f}% of bankroll\n"
        f"Estimated edge at entry: {request.estimated_edge_at_entry:.1%}\n"
        f"Odds at entry: {request.odds_at_entry:.2f}\n\n"
        f"Kelly analysis:\n"
        f"  Full Kelly: {full_kelly:.1%}\n"
        f"  Recommended fractional (1/3): {kelly_pct:.2f}%\n"
        f"  Actual size: {request.size_pct_of_bankroll:.2f}%\n"
        f"  Sizing verdict: {sizing_verdict}\n\n"
        "Grade this trade and provide detailed coaching feedback."
    )

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _COACH_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=700,
    )
    text = response.choices[0].message.content or ""

    grade = _extract_grade(text)
    process_score = _grade_to_score(grade)
    biases = _detect_biases(text)

    return TradeGrade(
        grade=grade,
        process_score=process_score,
        kelly_compliance=sizing_verdict,
        kelly_recommended_pct=kelly_pct,
        biases_detected=biases,
        strengths=_extract_bullet_section(text, "strength"),
        improvements=_extract_bullet_section(text, "improv"),
        coaching_note=text,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _kelly_verdict(actual_pct: float, kelly_pct: float) -> str:
    if kelly_pct == 0:
        return "no_edge" if actual_pct > 0 else "optimal"
    ratio = actual_pct / kelly_pct
    if ratio <= 0.5:
        return "under"
    elif ratio > 1.5 or actual_pct > settings.max_kelly_fraction * 100:
        return "over"
    return "optimal"


def _extract_grade(text: str) -> str:
    import re
    # Look for explicit grade pattern: "Grade: A" or "A+" etc.
    match = re.search(r"[Gg]rade[:\s]+([A-F][+-]?)", text)
    if match:
        return match.group(1)[0]  # Normalise to A/B/C/D/F
    # Fallback: look for standalone grade letter
    for grade in ["A", "B", "C", "D", "F"]:
        if f"grade {grade}" in text.lower() or f"\n{grade}\n" in text:
            return grade
    return "C"  # Default


def _grade_to_score(grade: str) -> float:
    return {"A": 9.0, "B": 7.5, "C": 5.5, "D": 3.5, "F": 1.0}.get(grade, 5.0)


def _detect_biases(text: str) -> list[str]:
    bias_keywords = {
        "overconfidence": ["overconfident", "overconfidence"],
        "recency_bias": ["recency", "recent events", "recent results"],
        "outcome_bias": ["outcome bias", "judging by result"],
        "loss_aversion": ["loss aversion", "holding losers", "cutting winners"],
        "availability_bias": ["availability", "salient", "vivid"],
        "football_overconcentration": ["football", "soccer market"],
        "anchoring": ["anchor", "anchored to"],
    }
    lower = text.lower()
    return [bias for bias, keywords in bias_keywords.items()
            if any(kw in lower for kw in keywords)]


def _extract_bullet_section(text: str, keyword: str) -> list[str]:
    lines = text.split("\n")
    in_section = False
    results = []
    for line in lines:
        if keyword.lower() in line.lower():
            in_section = True
            continue
        if in_section:
            stripped = line.strip().lstrip("•-*").strip()
            if stripped:
                results.append(stripped)
            elif results:
                break  # End of section
    return results[:5]
