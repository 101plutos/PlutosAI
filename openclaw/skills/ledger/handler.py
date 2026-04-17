"""
OpenClaw skill: ledger
Tax reports, net worth, Sparerpauschbetrag tracking, reconciliation status.
"""
from __future__ import annotations

import os
from datetime import datetime

import httpx

BASE_URL = os.getenv("PLUTOSAI_FINANCE_URL", "http://localhost:8008")
_CLIENT = httpx.AsyncClient(base_url=BASE_URL, timeout=25.0)


async def handle(message: str, context: dict) -> str:
    msg_lower = message.lower()

    if any(k in msg_lower for k in ["reconcile", "abgleich", "reconciliation"]):
        return "🔄 Nightly reconciliation runs at 23:00 CET automatically. Request a manual run via Lobster: `lobster run ledger-nightly-reconcile`"
    if any(k in msg_lower for k in ["net worth", "networth", "vermögen", "netto"]):
        return await _net_worth()
    if any(k in msg_lower for k in ["sparerpauschbetrag", "sparer", "allowance"]):
        return await _sparerpauschbetrag()
    return await _tax_report()


async def _tax_report() -> str:
    year = datetime.utcnow().year
    period = f"{year}-full"
    try:
        r = await _CLIENT.get("/ledger/tax-report", params={"period": period})
        r.raise_for_status()
        d = r.json()
    except Exception as exc:
        return f"⚠️ Tax report unavailable: {exc}"

    def eur(v):
        return f"€{float(v):,.2f}"

    return (
        f"🇩🇪 *Steuerbericht {period}*\n\n"
        f"  Realisierte Gewinne:    {eur(d['realised_gains_eur'])}\n"
        f"  Realisierte Verluste:   {eur(d['realised_losses_eur'])}\n"
        f"  Verlustvortrag:         {eur(d['loss_carryforward_eur'])}\n\n"
        f"  *Krypto*\n"
        f"  Steuerpflichtig:        {eur(d['crypto_taxable_eur'])}\n"
        f"  Steuerfrei (Haltefrist):{eur(d['crypto_exempt_eur'])}\n\n"
        f"  *Abgeltungssteuer (25%):* {eur(d['abgeltungssteuer_eur'])}\n"
        f"  Steuerliche Ereignisse: {len(d['tax_events'])}"
    )


async def _net_worth() -> str:
    try:
        r = await _CLIENT.get("/ledger/net-worth", params={"limit": 1})
        r.raise_for_status()
        history = r.json()
    except Exception as exc:
        return f"⚠️ LEDGER unavailable: {exc}"

    if not history:
        return "No net worth snapshots yet."

    s = history[0]

    def eur(v):
        return f"€{float(v):,.2f}"

    rem = float(s["sparerpauschbetrag_remaining_eur"])
    sp_bar = "█" * int(10 * (1 - rem / 1000)) + "░" * int(10 * rem / 1000)

    return (
        f"💰 *Vermögensübersicht*\n\n"
        f"  Gesamt:      {eur(s['total_eur'])}\n"
        f"  Liquide:     {eur(s['liquid_eur'])}\n"
        f"  Illiquide:   {eur(s['illiquid_eur'])}\n"
        f"  Krypto:      {eur(s['crypto_eur'])}\n\n"
        f"  *Sparerpauschbetrag*\n"
        f"  [{sp_bar}] {eur(s['sparerpauschbetrag_used_eur'])} / €1,000\n"
        f"  Verbleibend: {eur(rem)}"
    )


async def _sparerpauschbetrag() -> str:
    try:
        r = await _CLIENT.get("/ledger/net-worth", params={"limit": 1})
        r.raise_for_status()
        history = r.json()
    except Exception as exc:
        return f"⚠️ LEDGER unavailable: {exc}"

    if not history:
        return "No data yet."

    s = history[0]
    used = float(s["sparerpauschbetrag_used_eur"])
    remaining = float(s["sparerpauschbetrag_remaining_eur"])
    pct = used / 10  # 1000 EUR total

    warning = ""
    if remaining < 200:
        warning = "\n⚠️ *Achtung:* Jahresfreibetrag fast ausgeschöpft!"
    elif remaining < 0.01:
        warning = "\n🔴 *Jahresfreibetrag vollständig genutzt — Abgeltungssteuer gilt!*"

    return (
        f"🧾 *Sparerpauschbetrag {datetime.utcnow().year}*\n\n"
        f"  Genutzt:     €{used:,.2f} ({pct:.0f}%)\n"
        f"  Verbleibend: €{remaining:,.2f}\n"
        f"  Limit:       €1,000 / Person"
        f"{warning}"
    )
