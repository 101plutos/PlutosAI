"""
OpenClaw skill: banker
BBBank advisory, MiFID II suitability, and Praxisnachweis role-play
routed to BANKER agent via finance-service REST API.
"""
from __future__ import annotations

import os
import httpx

BASE_URL = os.getenv("PLUTOSAI_FINANCE_URL", "http://localhost:8008")
_CLIENT = httpx.AsyncClient(base_url=BASE_URL, timeout=55.0)


async def handle(message: str, context: dict) -> str:
    msg_lower = message.lower()

    if any(k in msg_lower for k in ["suitability", "mifid", "geeignet", "eignung"]):
        return await _suitability(message)
    if any(k in msg_lower for k in ["scenario", "praxisnachweis", "beratung", "role play"]):
        return await _scenario(message)
    return await _product_query(message)


async def _product_query(message: str) -> str:
    payload = {"query": message}
    try:
        r = await _CLIENT.post("/banker/product", json=payload)
        r.raise_for_status()
        d = r.json()
    except Exception as exc:
        return f"⚠️ BANKER unavailable: {exc}"

    products = ", ".join(d["products_discussed"]) if d["products_discussed"] else "general"
    notes = "\n".join(f"  ⚖️ {n}" for n in d["compliance_notes"])
    return (
        f"🏦 *BANKER* (Products: {products})\n\n"
        f"{d['response']}\n\n"
        f"{notes}"
    )


async def _suitability(message: str) -> str:
    # Extract product mention from message
    product = _extract_product(message) or "general investment product"
    payload = {
        "client_description": message,
        "product": product,
    }
    try:
        r = await _CLIENT.post("/banker/suitability", json=payload)
        r.raise_for_status()
        d = r.json()
    except Exception as exc:
        return f"⚠️ Suitability check failed: {exc}"

    verdict_emoji = {
        "suitable": "✅",
        "potentially_suitable": "🟡",
        "not_suitable": "🚫",
    }.get(d["suitability"], "❓")

    disclosures = "\n".join(f"  • {disc}" for disc in d["required_disclosures"][:3])
    return (
        f"⚖️ *MiFID II Suitability: {d['product']}*\n\n"
        f"Verdict: {verdict_emoji} {d['suitability'].replace('_', ' ').title()}\n\n"
        f"{d['justification'][:500]}\n\n"
        f"*Required Disclosures:*\n{disclosures}\n\n"
        f"💡 {d['recommendation']}"
    )


async def _scenario(message: str) -> str:
    payload = {"scenario_description": message}
    try:
        r = await _CLIENT.post("/banker/scenario", json=payload)
        r.raise_for_status()
        d = r.json()
    except Exception as exc:
        return f"⚠️ Scenario generation failed: {exc}"

    dialogue_lines = []
    for turn in d["dialogue"][:6]:  # Trim for messaging
        role_label = "🧑 Advisor" if turn["role"] == "advisor" else "👤 Client"
        dialogue_lines.append(f"*{role_label}:* {turn['message']}")

    coaching = "\n".join(f"  • {n}" for n in d["coaching_notes"][:3])
    return (
        f"🎭 *Praxisnachweis Scenario*\n\n"
        + "\n\n".join(dialogue_lines)
        + f"\n\n*Coaching Notes:*\n{coaching}"
    )


def _extract_product(message: str) -> str | None:
    products = [
        "VL-ETF", "VL-Bausparvertrag", "Baufinanzierung", "Tagesgeld",
        "Festgeld", "Depot", "Privatkredit", "Girokonto", "Sparplan",
    ]
    for p in products:
        if p.lower() in message.lower():
            return p
    return None
