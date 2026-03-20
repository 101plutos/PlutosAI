"""
ORACLE Agent — Project Francesca, Finance Division.

Market Intelligence Analyst. Monitors DAX 40, S&P 500, Nikkei 225,
BTC/ETH, commodities, FX rates 24/7. Produces German-language weekly
briefings and fires P0 alerts within 5 minutes of material market moves.

Outputs:
  - MarketBriefing (weekly German BBBank format, daily DISPATCH variants)
  - MarketAlert (P0/P1/P2 graded severity)
  - MarketSnapshot (current price/change per symbol)
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from openai import AsyncOpenAI

from ..config import settings
from ..models import (
    MarketAlert,
    MarketAlertSeverity,
    MarketBriefing,
    MarketBriefingRequest,
    MarketSnapshot,
    OracleStatusResponse,
)

logger = logging.getLogger(__name__)

_alerts: list[MarketAlert] = []
_last_briefing: MarketBriefing | None = None
_snapshots: dict[str, MarketSnapshot] = {}

# ---------------------------------------------------------------------------
# Briefing prompts
# ---------------------------------------------------------------------------
_BRIEFING_SYSTEM_DE = """\
Du bist ORACLE, ein Marktintelligenz-Analyst bei Project Francesca.
Schreibe einen professionellen Marktbericht im BBBank-Stil — klar, faktenbasiert,
auf Deutsch. Struktur: Headline → Kurzbeschreibung → Marktbewegungen → Makrotreiber
→ Zentralbankwatch → Ausblick. Keine Übertreibungen. Nur Fakten und Kausalitäten.
"""

_BRIEFING_SYSTEM_EN = """\
You are ORACLE, a market intelligence analyst for Project Francesca.
Write a professional market briefing in FT/Reuters style — factual, concise, authoritative.
Structure: Headline → Overview → Market Movers → Macro Drivers → Central Bank Watch → Outlook.
No hyperbole. Only facts and causal chains. Never use: 'plummeted', 'soared', 'massive',
'only time will tell', 'buckle up'.
"""

_ALERT_SYSTEM = """\
You are ORACLE. A significant market move has occurred. Write a brief (3-5 sentence)
P0 market alert: what happened, why it likely happened, immediate implications.
Be direct. No filler. German if language='de', English if language='en'.
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
async def generate_briefing(
    request: MarketBriefingRequest,
    client: AsyncOpenAI,
    model: str,
) -> MarketBriefing:
    """
    Produce a market briefing in the requested language and scope.
    Weekly German BBBank briefing scheduled Monday 06:00 CET.
    """
    logger.info("ORACLE generating %s briefing (lang=%s)", request.scope, request.language)

    system = _BRIEFING_SYSTEM_DE if request.language == "de" else _BRIEFING_SYSTEM_EN
    scope_label = {
        "morning": "Morning Briefing",
        "european_close": "European Close",
        "us_close": "US Close",
        "weekly": "Weekly Summary & Outlook",
    }.get(request.scope, request.scope)

    symbols_str = ", ".join(request.include_sectors)
    user_prompt = (
        f"Scope: {scope_label}\n"
        f"Monitored instruments: {symbols_str}\n"
        f"Current UTC time: {datetime.now(tz=timezone.utc).isoformat()}\n\n"
        f"Generate the full {scope_label}. Include specific directional moves where known."
    )

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=1200,
    )

    body = response.choices[0].message.content or ""
    headline = body.split("\n")[0].lstrip("#").strip()

    briefing = MarketBriefing(
        briefing_id=str(uuid.uuid4()),
        scope=request.scope,
        language=request.language,
        headline=headline,
        body=body,
        key_movers=_extract_movers(request.include_sectors),
        macro_drivers=_stub_macro_drivers(),
        central_bank_watch=_stub_cb_watch(),
    )
    global _last_briefing
    _last_briefing = briefing
    logger.info("ORACLE briefing generated: %s", headline[:80])
    return briefing


async def evaluate_market_move(
    symbol: str,
    move_pct: float,
    context: str,
    language: str,
    client: AsyncOpenAI,
    model: str,
) -> MarketAlert | None:
    """
    Evaluate if a price move warrants a P0/P1/P2 alert.
    P0 triggered at ≥ p0_move_threshold_pct (default 2%).
    Returns None if move is below P1 threshold (< 1%).
    """
    abs_move = abs(move_pct)
    if abs_move < 1.0:
        return None  # Below P1 threshold

    severity = (
        MarketAlertSeverity.P0 if abs_move >= settings.p0_move_threshold_pct
        else MarketAlertSeverity.P1
    )

    prompt = (
        f"Symbol: {symbol}\n"
        f"Move: {move_pct:+.2f}%\n"
        f"Context: {context}\n"
        f"Language: {language}\n\n"
        "Write a brief P0/P1 market alert."
    )

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _ALERT_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=200,
    )
    narrative = response.choices[0].message.content or ""

    alert = MarketAlert(
        alert_id=str(uuid.uuid4()),
        severity=severity,
        symbol=symbol,
        trigger=f"{symbol} {move_pct:+.2f}%",
        narrative=narrative,
        action_required=(severity == MarketAlertSeverity.P0),
    )
    _alerts.append(alert)
    logger.warning(
        "ORACLE %s ALERT: %s %+.2f%% — %s",
        severity.value, symbol, move_pct, narrative[:60],
    )
    return alert


def update_snapshot(symbol: str, price: float, change_pct_24h: float, source: str) -> None:
    """Update the in-memory market snapshot for a symbol."""
    _snapshots[symbol] = MarketSnapshot(
        symbol=symbol,
        price=price,
        change_pct_24h=change_pct_24h,
        source=source,
    )


def get_snapshots() -> list[MarketSnapshot]:
    return list(_snapshots.values())


def get_active_alerts() -> list[MarketAlert]:
    return [a for a in _alerts if a.action_required]


def get_status() -> OracleStatusResponse:
    next_scope = _next_briefing_scope()
    return OracleStatusResponse(
        monitored_symbols=settings.monitored_symbols,
        alerts_active=len(get_active_alerts()),
        last_briefing_at=_last_briefing.generated_at if _last_briefing else None,
        next_briefing_scope=next_scope,
        healthy=True,
    )


# ---------------------------------------------------------------------------
# Stubs — production: replace with OpenBB / Finnhub / FRED live data
# ---------------------------------------------------------------------------
def _extract_movers(symbols: list[str]) -> list[dict[str, Any]]:
    return [
        {"symbol": s, "change_pct": _snapshots.get(s, MarketSnapshot(
            symbol=s, price=0.0, change_pct_24h=0.0, source="stub",
            timestamp=datetime.now(tz=timezone.utc)
        )).change_pct_24h}
        for s in symbols
    ]


def _stub_macro_drivers() -> list[str]:
    return [
        "ECB rate trajectory",
        "US CPI print",
        "China PMI data",
        "Geopolitical risk premium",
    ]


def _stub_cb_watch() -> list[str]:
    return [
        "ECB: Next meeting TBD — market pricing 25bp cut",
        "Fed: Hawkish hold consensus",
        "BoJ: YCC tweak watch",
    ]


def _next_briefing_scope() -> str:
    hour = datetime.now(tz=timezone.utc).hour
    if hour < 7:
        return "morning"
    elif hour < 17:
        return "european_close"
    elif hour < 22:
        return "us_close"
    return "weekly"
