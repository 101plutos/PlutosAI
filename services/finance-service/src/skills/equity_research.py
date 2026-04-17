"""
equity-research skill — Project Francesca.

Generates 8-section institutional equity research reports in 5 minutes.
Style: Goldman Sachs / JPMorgan sell-side initiation of coverage.
Used by: ORACLE, BANKER, MUSE.

8 Sections:
  1. Investment Summary & Rating
  2. Company Overview
  3. Financial Analysis (P/E, EV/EBITDA, margins, FCF)
  4. Competitive Positioning
  5. Growth Catalysts
  6. Key Risks
  7. Valuation & Price Target
  8. ESG & Governance
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from openai import AsyncOpenAI

from ..models import EquityResearchReport, EquityResearchRequest

logger = logging.getLogger(__name__)

_SECTIONS = [
    "Investment Summary & Rating",
    "Company Overview",
    "Financial Analysis",
    "Competitive Positioning",
    "Growth Catalysts",
    "Key Risks",
    "Valuation & Price Target",
    "ESG & Governance",
]

_RESEARCH_SYSTEM = """\
You are a senior equity research analyst at a top-tier investment bank.
Generate a professional 8-section equity initiation report.

Style rules:
- Write in the style of Goldman Sachs / JPMorgan initiation notes
- Lead each section with the key insight, not the definition
- Use precise financial terminology
- Back every claim with logic or data (infer if actual data unavailable, flag clearly)
- Rating: Buy / Hold / Sell / Overweight / Underweight / Neutral
- Price target: give a 12-month base case

Respond in {language}. Mark each section with ## Section Title.
"""

_RISK_CATALYST_SYSTEM = """\
From the equity research report above, extract:
1. Top 3-5 key risks (bearish scenarios, threats to the investment thesis)
2. Top 3-5 key catalysts (events that could re-rate the stock positively)

Return as JSON: {"key_risks": [...], "key_catalysts": [...]}
"""


async def generate_report(
    request: EquityResearchRequest,
    client: AsyncOpenAI,
    model: str,
) -> EquityResearchReport:
    """Generate a full 8-section equity research report."""
    logger.info("equity-research: generating report for %s (%s)", request.ticker, request.company_name)

    lang = "German" if request.language == "de" else "English"
    system = _RESEARCH_SYSTEM.format(language=lang)

    context = f"Company: {request.company_name} (Ticker: {request.ticker})"
    if request.sector:
        context += f"\nSector: {request.sector}"
    if request.additional_context:
        context += f"\nAdditional context: {request.additional_context}"

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": (
                    f"{context}\n\n"
                    "Generate the full 8-section equity research report. "
                    "Sections:\n" + "\n".join(f"## {s}" for s in _SECTIONS)
                ),
            },
        ],
        temperature=0.3,
        max_tokens=3000,
    )
    full_report = response.choices[0].message.content or ""

    # Parse sections
    sections = _parse_sections(full_report)

    # Extract verdict and price target
    summary_section = sections.get("Investment Summary & Rating", "")
    verdict = _extract_verdict(summary_section)
    price_target = _extract_price_target(sections.get("Valuation & Price Target", ""))

    # Extract risks and catalysts via second LLM call
    risks, catalysts = await _extract_risks_catalysts(full_report, client, model)

    return EquityResearchReport(
        ticker=request.ticker,
        company_name=request.company_name,
        sections=sections,
        verdict=verdict,
        price_target=price_target,
        key_risks=risks,
        key_catalysts=catalysts,
    )


async def _extract_risks_catalysts(
    report_text: str,
    client: AsyncOpenAI,
    model: str,
) -> tuple[list[str], list[str]]:
    import json
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": report_text},
                {"role": "user", "content": _RISK_CATALYST_SYSTEM},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=400,
        )
        data = json.loads(response.choices[0].message.content or "{}")
        return data.get("key_risks", []), data.get("key_catalysts", [])
    except Exception:
        return [], []


def _parse_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current_section = "Preamble"
    current_content: list[str] = []

    for line in text.split("\n"):
        if line.startswith("## "):
            if current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = line.lstrip("#").strip()
            current_content = []
        else:
            current_content.append(line)

    if current_content:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def _extract_verdict(summary: str) -> str:
    for rating in ["Strong Buy", "Buy", "Overweight", "Hold", "Neutral",
                   "Underweight", "Sell", "Strong Sell"]:
        if rating.lower() in summary.lower():
            return rating
    return "Hold"


def _extract_price_target(valuation_section: str) -> str | None:
    import re
    match = re.search(r"(?:price target|PT|target price)[^\d]*(\$|€|£)?\s*(\d+[\.,]?\d*)",
                      valuation_section, re.IGNORECASE)
    if match:
        currency = match.group(1) or ""
        price = match.group(2)
        return f"{currency}{price}"
    return None
