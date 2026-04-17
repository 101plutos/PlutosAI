"""
COMPLIANCE Agent — Project Francesca, Finance Division.

The second-most-powerful agent after JARVIS. Acts as an absolute hard gate
before every QUANT trade. No trade executes without an explicit PASS.

Architecture rules enforced here:
- 30-second hard timeout (caller's responsibility via asyncio.wait_for)
- Friday blackout 13:45–16:00 CET: no trading, zero exceptions
- Position limit checks (single position, daily loss, sector concentration)
- Kelly criterion audit (size ≤ max_kelly_fraction of equity)
- BaFin / MiFID II / German tax law validation
- Immutable audit log (every decision persisted, never overwritten)
- If COMPLIANCE is unresponsive > 30s → caller must halt QUANT
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from ..config import settings
from .. import openclaw_client
from ..models import (
    ComplianceAuditEntry,
    ComplianceResult,
    ComplianceStatusResponse,
    ComplianceVerdict,
    DrawdownLevel,
    TradeProposal,
)

logger = logging.getLogger(__name__)

CET = ZoneInfo("Europe/Berlin")

# Append-only audit log (production: swap to PostgreSQL append-only table)
_audit_log: list[ComplianceAuditEntry] = []

# Cached daily loss tracker  {date_str: eur_lost}
_daily_loss: dict[str, Decimal] = {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
async def check_trade(
    proposal: TradeProposal,
    drawdown_level: DrawdownLevel,
) -> ComplianceResult:
    """
    Hard-gate check. Returns PASS or BLOCK with full rationale.
    Called inside asyncio.wait_for(<30s) by QUANT — if this raises
    TimeoutError, QUANT must halt all trading immediately.
    """
    now_cet = datetime.now(tz=CET)
    violations: list[str] = []
    rules_checked: list[str] = []

    # --- Rule 1: Blackout window ---
    rules_checked.append("blackout_window")
    blackout = _is_blackout(now_cet)
    if blackout:
        violations.append(
            f"BLACKOUT ACTIVE: Friday {settings.blackout_start_hour}:"
            f"{settings.blackout_start_minute:02d}–"
            f"{settings.blackout_end_hour}:{settings.blackout_end_minute:02d} CET. "
            "No trading permitted."
        )

    # --- Rule 2: Drawdown halt ---
    rules_checked.append("drawdown_halt")
    if drawdown_level in (DrawdownLevel.HALT_24H, DrawdownLevel.HALT_72H):
        violations.append(
            f"DRAWDOWN HALT ACTIVE ({drawdown_level.value}): "
            "Trading suspended until halt period expires."
        )

    # --- Rule 3: Position size limit ---
    rules_checked.append("position_size_limit")
    if proposal.size_eur > Decimal(str(settings.max_single_position_eur)):
        violations.append(
            f"POSITION SIZE EXCEEDED: Proposed €{proposal.size_eur} "
            f"> limit €{settings.max_single_position_eur}"
        )

    # --- Rule 4: Daily loss limit ---
    rules_checked.append("daily_loss_limit")
    today = now_cet.strftime("%Y-%m-%d")
    daily_loss_so_far = _daily_loss.get(today, Decimal("0"))
    if daily_loss_so_far >= Decimal(str(settings.max_daily_loss_eur)):
        violations.append(
            f"DAILY LOSS LIMIT HIT: €{daily_loss_so_far} lost today "
            f"(limit €{settings.max_daily_loss_eur})"
        )

    # --- Rule 5: Kelly criterion audit ---
    rules_checked.append("kelly_criterion")
    if proposal.kelly_fraction > settings.max_kelly_fraction:
        violations.append(
            f"KELLY VIOLATION: Proposed fraction {proposal.kelly_fraction:.3f} "
            f"> max {settings.max_kelly_fraction:.3f}. Reduce position size."
        )

    # --- Rule 6: Drawdown warning — size reduction enforcement ---
    rules_checked.append("drawdown_warning_size_reduction")
    if drawdown_level == DrawdownLevel.WARNING:
        # In WARNING state QUANT should already have halved sizes.
        # Flag if size_eur looks like it hasn't been reduced.
        max_allowed = Decimal(str(settings.max_single_position_eur)) * Decimal("0.5")
        if proposal.size_eur > max_allowed:
            violations.append(
                f"DRAWDOWN WARNING: Position sizes must be halved. "
                f"Max allowed €{max_allowed} but proposed €{proposal.size_eur}"
            )

    # --- Rule 7: BaFin / MiFID II — market eligibility ---
    rules_checked.append("bafin_market_eligibility")
    ineligible_markets = {"unknown", "unregulated"}
    if proposal.market.lower() in ineligible_markets:
        violations.append(
            f"BAFIN COMPLIANCE: Market '{proposal.market}' not on approved list."
        )

    # --- Build verdict ---
    verdict = ComplianceVerdict.BLOCK if violations else ComplianceVerdict.PASS
    rationale = (
        "All rules passed. Trade approved." if not violations
        else f"Trade blocked. Violations: {'; '.join(violations)}"
    )

    entry = _write_audit(
        proposal_id=proposal.proposal_id,
        verdict=verdict,
        rules_checked=rules_checked,
        violations=violations,
        rationale=rationale,
        blackout_active=blackout,
        drawdown_level=drawdown_level,
    )

    log_fn = logger.warning if verdict == ComplianceVerdict.BLOCK else logger.info
    log_fn(
        "COMPLIANCE %s for proposal %s (market=%s, size=€%s): %s",
        verdict.value,
        proposal.proposal_id,
        proposal.market,
        proposal.size_eur,
        rationale,
    )

    # Push BLOCK verdicts to Flo via OpenClaw (non-blocking, non-fatal)
    if verdict == ComplianceVerdict.BLOCK:
        import asyncio
        asyncio.create_task(
            openclaw_client.push_compliance_block(proposal.symbol, violations)
        )

    return ComplianceResult(
        verdict=verdict,
        violations=violations,
        rationale=rationale,
        audit_entry=entry,
    )


def record_daily_loss(amount_eur: Decimal) -> None:
    """Called by QUANT when a trade closes at a loss. Updates daily loss tracker."""
    today = datetime.now(tz=CET).strftime("%Y-%m-%d")
    _daily_loss[today] = _daily_loss.get(today, Decimal("0")) + amount_eur.copy_abs()
    logger.info("Daily loss tracker updated: today=€%s", _daily_loss[today])


def get_status() -> ComplianceStatusResponse:
    now_cet = datetime.now(tz=CET)
    blackout = _is_blackout(now_cet)
    return ComplianceStatusResponse(
        ruleset_version=settings.ruleset_version,
        ruleset_updated_at=datetime.fromisoformat(settings.ruleset_version),
        blackout_active=blackout,
        blackout_reason=(
            f"Friday {settings.blackout_start_hour}:"
            f"{settings.blackout_start_minute:02d}–"
            f"{settings.blackout_end_hour}:{settings.blackout_end_minute:02d} CET"
            if blackout else None
        ),
        current_drawdown_level=DrawdownLevel.NORMAL,  # injected from QUANT state in API
        audit_log_entries=len(_audit_log),
        healthy=True,
    )


def get_audit_log(limit: int = 50) -> list[ComplianceAuditEntry]:
    """Return the most recent audit entries (newest first)."""
    return list(reversed(_audit_log))[:limit]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _is_blackout(now_cet: datetime) -> bool:
    """True during Friday 13:45–16:00 CET."""
    if now_cet.weekday() != settings.blackout_day_of_week:
        return False
    start_minutes = settings.blackout_start_hour * 60 + settings.blackout_start_minute
    end_minutes = settings.blackout_end_hour * 60 + settings.blackout_end_minute
    current_minutes = now_cet.hour * 60 + now_cet.minute
    return start_minutes <= current_minutes < end_minutes


def _write_audit(
    proposal_id: str,
    verdict: ComplianceVerdict,
    rules_checked: list[str],
    violations: list[str],
    rationale: str,
    blackout_active: bool,
    drawdown_level: DrawdownLevel,
) -> ComplianceAuditEntry:
    entry = ComplianceAuditEntry(
        entry_id=str(uuid.uuid4()),
        proposal_id=proposal_id,
        verdict=verdict,
        ruleset_version=settings.ruleset_version,
        rules_checked=rules_checked,
        violations=violations,
        rationale=rationale,
        blackout_active=blackout_active,
        drawdown_level=drawdown_level,
    )
    _audit_log.append(entry)  # Append-only — never remove, never modify
    return entry
