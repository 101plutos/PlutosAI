"""
QUANT Agent — Project Francesca, Finance Division.

Quantitative trading agent. Enforces the drawdown protocol, computes
fractional Kelly sizing, and routes every trade through COMPLIANCE before
any execution decision is recorded.

Hard rules (cannot be overridden):
  10–20% drawdown  → halve all position sizes, alert user
  20–30% drawdown  → halt all trading 24 hours
  > 30% drawdown   → halt all trading 72 hours + incident review via AEGIS
  COMPLIANCE timeout > 30s → halt immediately, no degraded mode

Markets supported: polymarket, binance, coinbase, kraken (crypto/options)
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN
from zoneinfo import ZoneInfo

from ..config import settings
from ..models import (
    DrawdownLevel,
    DrawdownState,
    QuantStatusResponse,
    QuantTradeRequest,
    QuantTradeResponse,
    ComplianceVerdict,
    TradeProposal,
)
from . import compliance as compliance_agent

logger = logging.getLogger(__name__)
CET = ZoneInfo("Europe/Berlin")

# ---------------------------------------------------------------------------
# Mutable state (production: persist in Redis / DB)
# ---------------------------------------------------------------------------
_state = DrawdownState(
    current_drawdown_pct=0.0,
    peak_equity_eur=Decimal("10000"),   # Starting equity — update via update_equity()
    current_equity_eur=Decimal("10000"),
    level=DrawdownLevel.NORMAL,
)
_open_positions: dict[str, dict] = {}   # proposal_id → position info
_pnl_today: Decimal = Decimal("0")
_trade_history: list[QuantTradeResponse] = []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
async def evaluate_trade(request: QuantTradeRequest) -> QuantTradeResponse:
    """
    Main entry point. Evaluates a trade request:
    1. Check drawdown state
    2. Compute Kelly fraction
    3. Adjust size per drawdown protocol
    4. Route through COMPLIANCE (30s hard timeout)
    5. Record result (never execute autonomously — human approves actual orders)
    """
    request_id = str(uuid.uuid4())
    logger.info(
        "QUANT evaluating trade: %s %s @ %s (size=€%s)",
        request.direction, request.symbol, request.market, request.size_eur,
    )

    # Step 1: Drawdown halt check
    if _state.level in (DrawdownLevel.HALT_24H, DrawdownLevel.HALT_72H):
        if _state.halt_until and datetime.now(tz=timezone.utc) < _state.halt_until:
            return _blocked_response(
                request_id=request_id,
                request=request,
                reason=f"Trading halted ({_state.level.value}) until {_state.halt_until.isoformat()}",
            )
        else:
            # Halt period expired — revert to NORMAL
            _state.level = DrawdownLevel.NORMAL
            _state.halt_until = None
            logger.info("Drawdown halt period expired — resuming NORMAL")

    # Step 2: Compute fractional Kelly
    kelly = _compute_kelly(
        edge=request.edge_estimate,
        odds=request.odds,
    )

    # Step 3: Apply drawdown size reduction
    effective_size = request.size_eur
    if _state.level == DrawdownLevel.WARNING:
        effective_size = (effective_size * Decimal("0.5")).quantize(
            Decimal("0.01"), rounding=ROUND_DOWN
        )
        logger.warning("WARNING state: position size halved to €%s", effective_size)

    # Step 4: Build proposal and run through COMPLIANCE
    proposal = TradeProposal(
        proposal_id=request_id,
        symbol=request.symbol,
        direction=request.direction,
        size_eur=effective_size,
        account_equity_eur=_state.current_equity_eur,
        kelly_fraction=kelly,
        market=request.market,
        rationale=request.rationale,
    )

    try:
        compliance_result = await asyncio.wait_for(
            compliance_agent.check_trade(proposal, _state.level),
            timeout=settings.compliance_timeout_seconds,
        )
    except asyncio.TimeoutError:
        logger.critical(
            "COMPLIANCE TIMEOUT after %ds — halting ALL QUANT trading",
            settings.compliance_timeout_seconds,
        )
        # Dead-man's switch: compliance unresponsive → hard stop
        _state.level = DrawdownLevel.HALT_24H
        _state.halt_until = datetime.now(tz=timezone.utc) + timedelta(hours=24)
        return QuantTradeResponse(
            request_id=request_id,
            symbol=request.symbol,
            compliance_verdict=ComplianceVerdict.BLOCK,
            executed=False,
            drawdown_level=_state.level,
            message="COMPLIANCE timeout. Trading halted per dead-man's switch.",
            timestamp=datetime.now(tz=timezone.utc),
        )

    # Step 5: Build response
    response = QuantTradeResponse(
        request_id=request_id,
        symbol=request.symbol,
        compliance_verdict=compliance_result.verdict,
        executed=False,   # Always False — human approves actual execution
        kelly_fraction_used=kelly if compliance_result.verdict == ComplianceVerdict.PASS else None,
        final_size_eur=effective_size if compliance_result.verdict == ComplianceVerdict.PASS else None,
        drawdown_level=_state.level,
        message=(
            f"COMPLIANCE {compliance_result.verdict.value}. {compliance_result.rationale} "
            "Human approval required before order submission."
            if compliance_result.verdict == ComplianceVerdict.PASS
            else f"Trade blocked: {compliance_result.rationale}"
        ),
        audit_entry_id=compliance_result.audit_entry.entry_id,
        timestamp=datetime.now(tz=timezone.utc),
    )

    _trade_history.append(response)
    logger.info(
        "QUANT result for %s: %s (Kelly=%.3f, size=€%s)",
        request.symbol,
        compliance_result.verdict.value,
        kelly,
        effective_size,
    )
    return response


def record_trade_outcome(proposal_id: str, pnl_eur: Decimal) -> None:
    """
    Record outcome of a trade. Called after human-approved execution completes.
    Updates equity, drawdown state, and daily P&L.
    """
    global _pnl_today

    _pnl_today += pnl_eur
    _state.current_equity_eur += pnl_eur
    _state.last_updated = datetime.now(tz=timezone.utc)

    # Update peak equity
    if _state.current_equity_eur > _state.peak_equity_eur:
        _state.peak_equity_eur = _state.current_equity_eur

    # Recompute drawdown
    if _state.peak_equity_eur > 0:
        drawdown = float(
            (_state.peak_equity_eur - _state.current_equity_eur)
            / _state.peak_equity_eur
            * 100
        )
        _state.current_drawdown_pct = round(drawdown, 2)
    else:
        drawdown = 0.0

    # Record loss for daily limit
    if pnl_eur < 0:
        compliance_agent.record_daily_loss(pnl_eur.copy_abs())

    # Apply drawdown protocol
    prev_level = _state.level
    now = datetime.now(tz=timezone.utc)

    if drawdown > settings.drawdown_halt_72h_pct:
        _state.level = DrawdownLevel.HALT_72H
        _state.halt_until = now + timedelta(hours=72)
        logger.critical(
            "DRAWDOWN >30%% (%.1f%%) — HALT 72H. Review via AEGIS required.", drawdown
        )
    elif drawdown > settings.drawdown_halt_24h_pct:
        _state.level = DrawdownLevel.HALT_24H
        _state.halt_until = now + timedelta(hours=24)
        logger.error(
            "DRAWDOWN >20%% (%.1f%%) — HALT 24H. Full review required.", drawdown
        )
    elif drawdown > settings.drawdown_warning_pct:
        _state.level = DrawdownLevel.WARNING
        logger.warning(
            "DRAWDOWN >10%% (%.1f%%) — WARNING. Position sizes halved.", drawdown
        )
    else:
        _state.level = DrawdownLevel.NORMAL

    if _state.level != prev_level:
        logger.warning(
            "Drawdown level changed: %s → %s (drawdown=%.1f%%)",
            prev_level.value, _state.level.value, drawdown,
        )


def update_equity(current_equity_eur: Decimal) -> None:
    """Update account equity (e.g. from LEDGER nightly reconciliation)."""
    _state.current_equity_eur = current_equity_eur
    if current_equity_eur > _state.peak_equity_eur:
        _state.peak_equity_eur = current_equity_eur
    _state.last_updated = datetime.now(tz=timezone.utc)


def get_status() -> QuantStatusResponse:
    total = len(_trade_history)
    passed = sum(
        1 for t in _trade_history
        if t.compliance_verdict == ComplianceVerdict.PASS
    )
    last_trade = _trade_history[-1].timestamp if _trade_history else None
    return QuantStatusResponse(
        trading_active=_state.level == DrawdownLevel.NORMAL,
        drawdown_state=_state,
        open_positions=len(_open_positions),
        pnl_today_eur=_pnl_today,
        compliance_pass_rate=round(passed / total, 3) if total else 0.0,
        last_trade_at=last_trade,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _compute_kelly(edge: float, odds: float) -> float:
    """
    Fractional Kelly criterion (25–33% of full Kelly).
    f* = (bp - q) / b  where b=odds, p=P(win), q=P(lose)
    Returns capped at max_kelly_fraction.
    """
    p = edge
    q = 1.0 - edge
    b = odds
    if b <= 0 or p <= 0:
        return 0.0
    full_kelly = (b * p - q) / b
    full_kelly = max(0.0, full_kelly)
    # Default fractional Kelly: 1/3 of full Kelly
    fractional = full_kelly / 3.0
    return round(min(fractional, settings.max_kelly_fraction), 4)


def _blocked_response(request_id: str, request: QuantTradeRequest, reason: str) -> QuantTradeResponse:
    return QuantTradeResponse(
        request_id=request_id,
        symbol=request.symbol,
        compliance_verdict=ComplianceVerdict.BLOCK,
        executed=False,
        drawdown_level=_state.level,
        message=reason,
        timestamp=datetime.now(tz=timezone.utc),
    )
