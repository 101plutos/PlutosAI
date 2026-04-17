"""
OpenClaw skill: oracle
Market intelligence at a message. Returns live snapshots, active alerts,
or generates a full market briefing in the user's language.
"""
from __future__ import annotations

import os
import re

import httpx

BASE_URL = os.getenv("PLUTOSAI_FINANCE_URL", "http://localhost:8008")
_CLIENT = httpx.AsyncClient(base_url=BASE_URL, timeout=85.0)

_SEVERITY_EMOJI = {"P0": "🚨", "P1": "⚠️", "P2": "ℹ️"}


async def handle(message: str, context: dict) -> str:
    msg_lower = message.lower()

    # Detect language preference
    language = "de" if any(w in msg_lower for w in ["deutsch", "auf deutsch", "german"]) else "en"

    # Route by keyword
    if any(k in msg_lower for k in ["morning brief", "morgenbericht", "morning"]):
        return await _briefing("morning", language)
    if any(k in msg_lower for k in ["european close", "europe close"]):
        return await _briefing("european_close", language)
    if any(k in msg_lower for k in ["us close", "us market"]):
        return await _briefing("us_close", language)
    if any(k in msg_lower for k in ["weekly", "wöchentlich", "week in review"]):
        return await _briefing("weekly", language)
    if any(k in msg_lower for k in ["brief", "bericht", "report", "marktbericht"]):
        return await _briefing("morning", language)
    if any(k in msg_lower for k in ["alert", "p0", "p1", "was läuft", "what's moving"]):
        return await _alerts()
    if any(k in msg_lower for k in ["snapshot", "price", "kurs", "dax", "btc", "s&p"]):
        return await _snapshots()

    # Default: alerts + snapshot
    alerts = await _alerts()
    snaps = await _snapshots()
    return f"{alerts}\n\n{snaps}"


async def _alerts() -> str:
    try:
        r = await _CLIENT.get("/oracle/alerts")
        r.raise_for_status()
        alerts = r.json()
    except Exception as exc:
        return f"⚠️ ORACLE unavailable: {exc}"

    if not alerts:
        return "🟢 *ORACLE*: No active alerts. Markets quiet."

    lines = [f"*ORACLE — {len(alerts)} ACTIVE ALERT(S)*", ""]
    for a in alerts:
        emoji = _SEVERITY_EMOJI.get(a["severity"], "📌")
        lines.append(
            f"{emoji} *{a['severity']}* — {a['trigger']}\n"
            f"   {a['narrative'][:140]}\n"
        )
    return "\n".join(lines)


async def _snapshots() -> str:
    try:
        r = await _CLIENT.get("/oracle/snapshots")
        r.raise_for_status()
        snaps = r.json()
    except Exception as exc:
        return f"⚠️ Snapshots unavailable: {exc}"

    if not snaps:
        return "📡 No market snapshots yet — MARKETPULSE feed not connected."

    lines = ["*Market Snapshot*", ""]
    for s in sorted(snaps, key=lambda x: abs(x["change_pct_24h"]), reverse=True):
        chg = s["change_pct_24h"]
        arrow = "▲" if chg >= 0 else "▼"
        lines.append(f"  {s['symbol']:<10}  {s['price']:>10,.2f}  {arrow} {abs(chg):.2f}%")
    return "```\n" + "\n".join(lines) + "\n```"


async def _briefing(scope: str, language: str) -> str:
    payload = {
        "language": language,
        "scope": scope,
        "include_sectors": ["DAX 40", "S&P 500", "BTC/ETH", "EUR/USD"],
        "style": "bbbank_internal" if language == "de" else "dispatch",
    }
    try:
        r = await _CLIENT.post("/oracle/briefing", json=payload)
        r.raise_for_status()
        briefing = r.json()
    except Exception as exc:
        return f"⚠️ Briefing generation failed: {exc}"

    # Format for messaging (keep it readable on mobile)
    return (
        f"📰 *{briefing['headline']}*\n\n"
        f"{_trim(briefing['body'], 1200)}\n\n"
        f"_Generated: {briefing['generated_at'][:16].replace('T', ' ')} UTC_"
    )


def _trim(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + "…"
