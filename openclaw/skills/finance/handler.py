"""
OpenClaw skill: finance
Invoked when Flo types "finance status", "net worth", "quant evaluate", etc.
Routes to the PlutosAI finance-service REST API and formats the response
for delivery over Flo's preferred messaging channel (Telegram, WhatsApp, etc.).

Handler contract:
  async def handle(message: str, context: dict) -> str
"""
from __future__ import annotations

import json
import os
from typing import Any

import httpx

BASE_URL = os.getenv("PLUTOSAI_FINANCE_URL", "http://localhost:8008")
_CLIENT = httpx.AsyncClient(base_url=BASE_URL, timeout=40.0)


async def handle(message: str, context: dict) -> str:
    """Main dispatch — route to correct sub-action based on message content."""
    msg_lower = message.lower()

    # Route by keyword
    if any(k in msg_lower for k in ["trade eval", "quant eval", "evaluate"]):
        return await _trade_help()
    if any(k in msg_lower for k in ["audit", "compliance log", "block reason"]):
        return await _compliance_audit()
    if any(k in msg_lower for k in ["net worth", "networth", "vermögen"]):
        return await _net_worth()
    if any(k in msg_lower for k in ["drawdown", "halt", "trading halt"]):
        return await _quant_status()

    # Default: full dashboard
    return await _finance_dashboard()


# ---------------------------------------------------------------------------
# Finance Dashboard — "finance status"
# ---------------------------------------------------------------------------
async def _finance_dashboard() -> str:
    try:
        r = await _CLIENT.get("/finance/status")
        r.raise_for_status()
        d = r.json()
    except Exception as exc:
        return f"⚠️ Finance service unreachable: {exc}"

    quant = d["QUANT"]
    comp = d["COMPLIANCE"]
    oracle = d["ORACLE"]

    dd = quant["drawdown_level"]
    dd_emoji = {"normal": "🟢", "warning": "🟡", "halt_24h": "🔴", "halt_72h": "🆘"}.get(dd, "⚪")

    pnl = quant["pnl_today_eur"]
    pnl_str = f"+€{pnl:.2f}" if pnl >= 0 else f"-€{abs(pnl):.2f}"
    pnl_emoji = "📈" if pnl >= 0 else "📉"

    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━",
        "📊  *FINANCE DIVISION STATUS*",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"*QUANT* {dd_emoji}",
        f"  PnL today:   {pnl_emoji} {pnl_str}",
        f"  Drawdown:    {quant['drawdown_pct']:.1f}% ({dd.upper()})",
        f"  Positions:   {quant['open_positions']} open",
        f"  COMP pass:   {quant['compliance_pass_rate']:.0%}",
        "",
        f"*COMPLIANCE* {'✅' if not comp['blackout_active'] else '🚫'}",
        f"  Ruleset:     v{comp['ruleset_version']}",
        f"  Blackout:    {'ACTIVE 🚫' if comp['blackout_active'] else 'clear'}",
        f"  Audit log:   {comp['audit_entries']} entries",
        "",
        f"*ORACLE* {'🔴' if oracle['alerts_active'] > 0 else '🟢'}",
        f"  Alerts:      {oracle['alerts_active']} active",
        f"  Next scope:  {oracle['next_scope']}",
        "━━━━━━━━━━━━━━━━━━━━━━",
    ]
    if oracle["alerts_active"] > 0:
        lines.append("⚡ Run `oracle alerts` for P0 details")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# QUANT status detail
# ---------------------------------------------------------------------------
async def _quant_status() -> str:
    try:
        r = await _CLIENT.get("/quant/status")
        r.raise_for_status()
        d = r.json()
    except Exception as exc:
        return f"⚠️ QUANT unavailable: {exc}"

    dd = d["drawdown_state"]
    halt_until = dd.get("halt_until")
    halt_str = f"\n  Halt until:  {halt_until}" if halt_until else ""

    level_emoji = {"normal": "🟢", "warning": "🟡", "halt_24h": "🔴", "halt_72h": "🆘"}.get(
        dd["level"], "⚪"
    )

    return (
        f"*QUANT Drawdown State* {level_emoji}\n"
        f"  Level:       {dd['level'].upper()}\n"
        f"  Drawdown:    {dd['current_drawdown_pct']:.2f}%\n"
        f"  Peak equity: €{dd['peak_equity_eur']}\n"
        f"  Current:     €{dd['current_equity_eur']}"
        f"{halt_str}\n\n"
        f"  Trading:     {'🟢 ACTIVE' if d['trading_active'] else '🔴 HALTED'}\n"
        f"  Positions:   {d['open_positions']}\n"
        f"  PnL today:   €{d['pnl_today_eur']}"
    )


# ---------------------------------------------------------------------------
# Compliance audit log
# ---------------------------------------------------------------------------
async def _compliance_audit() -> str:
    try:
        r = await _CLIENT.get("/compliance/audit", params={"limit": 10})
        r.raise_for_status()
        entries = r.json()
    except Exception as exc:
        return f"⚠️ Audit log unavailable: {exc}"

    if not entries:
        return "📋 Compliance audit log is empty."

    lines = ["*Last 10 COMPLIANCE decisions:*", ""]
    for e in entries:
        verdict_emoji = "✅" if e["verdict"] == "PASS" else "🚫"
        ts = e["checked_at"][:16].replace("T", " ")
        lines.append(
            f"{verdict_emoji} `{ts}` — {e['proposal_id'][:8]}…\n"
            f"   {e['rationale'][:80]}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Net worth snapshot
# ---------------------------------------------------------------------------
async def _net_worth() -> str:
    try:
        r = await _CLIENT.get("/ledger/net-worth", params={"limit": 2})
        r.raise_for_status()
        history = r.json()
    except Exception as exc:
        return f"⚠️ LEDGER unavailable: {exc}"

    if not history:
        return "📊 No net worth snapshots yet. Post one with `ledger record`."

    snap = history[0]
    total = float(snap["total_eur"])
    used = float(snap["sparerpauschbetrag_used_eur"])
    remaining = float(snap["sparerpauschbetrag_remaining_eur"])

    lines = [
        "💰 *Net Worth Snapshot*",
        f"  Total:       €{total:,.2f}",
        f"  Liquid:      €{float(snap['liquid_eur']):,.2f}",
        f"  Illiquid:    €{float(snap['illiquid_eur']):,.2f}",
        f"  Crypto:      €{float(snap['crypto_eur']):,.2f}",
        "",
        "🇩🇪 *Sparerpauschbetrag*",
        f"  Used:        €{used:,.2f} / €1,000",
        f"  Remaining:   €{remaining:,.2f}",
    ]
    if remaining < 100:
        lines.append("⚠️ Approaching annual allowance limit!")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trade eval help (interactive prompt)
# ---------------------------------------------------------------------------
async def _trade_help() -> str:
    return (
        "📊 *QUANT Trade Evaluation*\n\n"
        "Send a trade for COMPLIANCE + Kelly sizing:\n\n"
        "```\nquant eval BTC-USD long 500 EUR\n"
        "  edge: 0.58  odds: 1.1  market: binance\n"
        "  rationale: Support held at 82k, momentum flipping\n```\n\n"
        "I'll run COMPLIANCE, compute fractional Kelly, and return verdict."
    )
