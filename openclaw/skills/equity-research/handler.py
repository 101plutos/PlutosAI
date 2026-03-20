"""
OpenClaw skill: equity-research
8-section institutional equity research report. Heavy (5 min). Returns
summary + verdict to messaging channel, with full report as a document
if OpenClaw supports document delivery.
"""
from __future__ import annotations

import os
import re

import httpx

BASE_URL = os.getenv("PLUTOSAI_FINANCE_URL", "http://localhost:8008")
_CLIENT = httpx.AsyncClient(base_url=BASE_URL, timeout=350.0)


async def handle(message: str, context: dict) -> str:
    # Extract ticker from message: "research AAPL", "SAP.DE report", etc.
    ticker, company = _parse_request(message)
    if not ticker:
        return (
            "📊 *Equity Research*\n\n"
            "Tell me which stock: `equity research AAPL` or `SAP.DE report`\n"
            "I'll generate the full 8-section institutional report (~5 min)."
        )

    language = "de" if any(w in message.lower() for w in ["deutsch", "german"]) else "en"

    payload = {
        "ticker": ticker.upper(),
        "company_name": company or ticker.upper(),
        "language": language,
    }

    # Warn user about wait time
    yield f"⏳ Generating equity research for *{ticker.upper()}*… (~5 min)"

    try:
        r = await _CLIENT.post("/skills/equity-research", json=payload)
        r.raise_for_status()
        report = r.json()
    except Exception as exc:
        return f"⚠️ Research generation failed: {exc}"

    verdict_emoji = {
        "Buy": "🟢", "Strong Buy": "🟢",
        "Hold": "🟡", "Neutral": "🟡",
        "Sell": "🔴", "Underweight": "🔴",
        "Overweight": "🟢",
    }.get(report.get("verdict", "Hold"), "⚪")

    risks = "\n".join(f"  🔻 {r}" for r in report.get("key_risks", [])[:3])
    catalysts = "\n".join(f"  🚀 {c}" for c in report.get("key_catalysts", [])[:3])
    pt = report.get("price_target") or "Not specified"

    summary_section = report.get("sections", {}).get("Investment Summary & Rating", "")
    summary_snippet = summary_section[:400].replace("\n", " ") if summary_section else ""

    return (
        f"📊 *{report['company_name']} ({report['ticker']})*\n"
        f"Verdict: {verdict_emoji} *{report['verdict']}* | PT: {pt}\n\n"
        f"{summary_snippet}…\n\n"
        f"*Key Risks:*\n{risks}\n\n"
        f"*Catalysts:*\n{catalysts}\n\n"
        f"_Full 8-section report available on request._"
    )


def _parse_request(message: str) -> tuple[str | None, str | None]:
    """Extract ticker and optional company name from free-form message."""
    # Match standard tickers: AAPL, SAP.DE, BRK.B, 7203.T
    tickers = re.findall(r"\b([A-Z]{1,5}(?:\.[A-Z]{1,2})?)\b", message.upper())
    # Filter common words
    skip = {"AI", "DE", "US", "EU", "EN", "FT", "BTC", "ETH", "AND", "FOR", "THE"}
    tickers = [t for t in tickers if t not in skip]
    ticker = tickers[0] if tickers else None

    # Company name: text before or after ticker
    company = None
    if ticker:
        # Try to find quoted company name
        match = re.search(r'"([^"]+)"', message)
        if match:
            company = match.group(1)

    return ticker, company
