"""
Finance Division Service — Project Francesca.

Five agents (COMPLIANCE, QUANT, ORACLE, BANKER, LEDGER) + three financial skills
(equity-research, prediction-market-coach, financial-dispatch) exposed over a
single FastAPI application on port 8008.

Node: plutos — Finance & ML compute node
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from typing import Any

import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException
from openai import AsyncOpenAI
from prometheus_fastapi_instrumentator import Instrumentator

from .agents import compliance as compliance_agent
from .agents import quant as quant_agent
from .agents import oracle as oracle_agent
from .agents import banker as banker_agent
from .agents import ledger as ledger_agent
from .skills import equity_research as skill_equity
from .skills import prediction_market_coach as skill_coach
from .skills import financial_dispatch as skill_dispatch
from .config import settings
from .models import (
    # Shared
    ComplianceVerdict,
    # COMPLIANCE
    ComplianceAuditEntry,
    ComplianceResult,
    ComplianceStatusResponse,
    TradeProposal,
    # QUANT
    QuantTradeRequest,
    QuantTradeResponse,
    QuantStatusResponse,
    DrawdownState,
    # ORACLE
    MarketAlert,
    MarketBriefing,
    MarketBriefingRequest,
    MarketSnapshot,
    OracleStatusResponse,
    # BANKER
    BBBankProductQuery,
    BBBankProductResponse,
    ClientScenarioRequest,
    ClientScenarioResponse,
    MiFIDSuitabilityRequest,
    MiFIDSuitabilityResult,
    # LEDGER
    NetWorthSnapshot,
    ReconciliationRequest,
    ReconciliationResult,
    TaxReport,
    TransactionCategorizationRequest,
    CategorizedTransaction,
    # Skills
    EquityResearchRequest,
    EquityResearchReport,
    TradeGradeRequest,
    TradeGrade,
    DispatchRequest,
    DispatchArticle,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None
_llm: AsyncOpenAI | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _redis, _llm

    # Redis (non-fatal if down — service continues in-memory)
    try:
        _redis = aioredis.Redis(
            host=settings.redis_host, port=settings.redis_port,
            db=settings.redis_db, decode_responses=True,
        )
        await _redis.ping()
        logger.info("Finance service: Redis connected")
    except Exception as exc:
        logger.warning("Finance service: Redis unavailable (%s) — in-memory fallback", exc)
        _redis = None

    # OpenAI-compatible LLM client
    _llm = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )
    logger.info(
        "Finance service LLM ready → %s (model: %s)",
        settings.openai_base_url, settings.default_model,
    )
    yield
    if _redis:
        await _redis.aclose()


app = FastAPI(
    title="Finance Division — Project Francesca",
    description=(
        "The core value-delivery engine of Project Francesca. "
        "Five agents (COMPLIANCE, QUANT, ORACLE, BANKER, LEDGER) "
        "and three on-demand financial skills. Node: plutos."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app)


def _llm_or_503() -> AsyncOpenAI:
    if _llm is None:
        raise HTTPException(status_code=503, detail="LLM client not ready")
    return _llm


# ============================================================================
# Health
# ============================================================================
@app.get("/health", tags=["ops"])
async def health() -> dict[str, Any]:
    redis_ok = False
    if _redis:
        try:
            await _redis.ping()
            redis_ok = True
        except Exception:
            pass
    return {
        "status": "healthy",
        "service": "finance-division",
        "redis": redis_ok,
        "compliance_healthy": True,
        "ruleset_version": settings.ruleset_version,
    }


# ============================================================================
# Finance Status Dashboard — "finance status" command from Flo
# ============================================================================
@app.get("/finance/status", tags=["dashboard"])
async def finance_status() -> dict[str, Any]:
    """
    Single-screen Finance Division digest — triggered by 'finance status'.
    Returns QUANT PnL, LEDGER reconciliation, model ages, COMPLIANCE health.
    """
    qs = quant_agent.get_status()
    cs = compliance_agent.get_status()
    os_ = oracle_agent.get_status()
    return {
        "QUANT": {
            "active": qs.trading_active,
            "pnl_today_eur": float(qs.pnl_today_eur),
            "drawdown_level": qs.drawdown_state.level.value,
            "drawdown_pct": qs.drawdown_state.current_drawdown_pct,
            "open_positions": qs.open_positions,
            "compliance_pass_rate": qs.compliance_pass_rate,
        },
        "COMPLIANCE": {
            "healthy": cs.healthy,
            "ruleset_version": cs.ruleset_version,
            "blackout_active": cs.blackout_active,
            "audit_entries": cs.audit_log_entries,
        },
        "ORACLE": {
            "healthy": os_.healthy,
            "alerts_active": os_.alerts_active,
            "last_briefing_at": os_.last_briefing_at.isoformat() if os_.last_briefing_at else None,
            "next_scope": os_.next_briefing_scope,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# COMPLIANCE endpoints
# ============================================================================
@app.post("/compliance/check", response_model=ComplianceResult, tags=["compliance"])
async def compliance_check(proposal: TradeProposal) -> ComplianceResult:
    """
    Manually invoke COMPLIANCE gate on a trade proposal.
    Normally called internally by QUANT — exposed here for transparency and testing.
    """
    dd_state = quant_agent.get_status().drawdown_state
    return await compliance_agent.check_trade(proposal, dd_state.level)


@app.get("/compliance/status", response_model=ComplianceStatusResponse, tags=["compliance"])
async def compliance_status() -> ComplianceStatusResponse:
    status = compliance_agent.get_status()
    # Inject live drawdown level from QUANT
    status.current_drawdown_level = quant_agent.get_status().drawdown_state.level
    return status


@app.get("/compliance/audit", response_model=list[ComplianceAuditEntry], tags=["compliance"])
async def compliance_audit(limit: int = 50) -> list[ComplianceAuditEntry]:
    """Return the most recent COMPLIANCE audit log entries."""
    return compliance_agent.get_audit_log(limit=limit)


# ============================================================================
# QUANT endpoints
# ============================================================================
@app.post("/quant/evaluate", response_model=QuantTradeResponse, tags=["quant"])
async def quant_evaluate(request: QuantTradeRequest) -> QuantTradeResponse:
    """
    Evaluate a proposed trade through the full QUANT → COMPLIANCE pipeline.
    Returns PASS/BLOCK with Kelly sizing and audit trail.
    Human approval required before actual order submission.
    """
    return await quant_agent.evaluate_trade(request)


@app.get("/quant/status", response_model=QuantStatusResponse, tags=["quant"])
async def quant_status() -> QuantStatusResponse:
    return quant_agent.get_status()


@app.post("/quant/outcome", tags=["quant"])
async def record_trade_outcome(
    proposal_id: str, pnl_eur: float
) -> dict[str, Any]:
    """Record the outcome of a human-executed trade. Updates drawdown state."""
    quant_agent.record_trade_outcome(proposal_id, Decimal(str(pnl_eur)))
    return {"recorded": True, "pnl_eur": pnl_eur, "new_status": quant_agent.get_status().dict()}


@app.post("/quant/equity", tags=["quant"])
async def update_equity(current_equity_eur: float) -> dict[str, Any]:
    """Update account equity (called by LEDGER after nightly reconciliation)."""
    quant_agent.update_equity(Decimal(str(current_equity_eur)))
    return {"updated": True, "equity_eur": current_equity_eur}


# ============================================================================
# ORACLE endpoints
# ============================================================================
@app.post("/oracle/briefing", response_model=MarketBriefing, tags=["oracle"])
async def oracle_briefing(request: MarketBriefingRequest) -> MarketBriefing:
    """Generate a market briefing (weekly German BBBank format, or DISPATCH variant)."""
    llm = _llm_or_503()
    return await oracle_agent.generate_briefing(request, llm, settings.default_model)


@app.post("/oracle/alert", response_model=MarketAlert | None, tags=["oracle"])
async def oracle_alert(
    symbol: str,
    move_pct: float,
    context: str = "",
    language: str = "en",
) -> MarketAlert | None:
    """Evaluate a price move and generate a P0/P1/P2 alert if warranted."""
    llm = _llm_or_503()
    return await oracle_agent.evaluate_market_move(
        symbol=symbol, move_pct=move_pct, context=context,
        language=language, client=llm, model=settings.default_model,
    )


@app.post("/oracle/snapshot", tags=["oracle"])
async def oracle_snapshot(
    symbol: str, price: float, change_pct_24h: float, source: str = "manual"
) -> dict[str, Any]:
    """Update a market snapshot (called by MARKETPULSE WebSocket feeds)."""
    oracle_agent.update_snapshot(symbol, price, change_pct_24h, source)
    return {"updated": True, "symbol": symbol}


@app.get("/oracle/snapshots", response_model=list[MarketSnapshot], tags=["oracle"])
async def oracle_snapshots() -> list[MarketSnapshot]:
    return oracle_agent.get_snapshots()


@app.get("/oracle/alerts", response_model=list[MarketAlert], tags=["oracle"])
async def oracle_alerts() -> list[MarketAlert]:
    return oracle_agent.get_active_alerts()


@app.get("/oracle/status", response_model=OracleStatusResponse, tags=["oracle"])
async def oracle_status() -> OracleStatusResponse:
    return oracle_agent.get_status()


# ============================================================================
# BANKER endpoints
# ============================================================================
@app.post("/banker/suitability", response_model=MiFIDSuitabilityResult, tags=["banker"])
async def banker_suitability(request: MiFIDSuitabilityRequest) -> MiFIDSuitabilityResult:
    """MiFID II suitability assessment for a client–product combination."""
    llm = _llm_or_503()
    return await banker_agent.assess_mifid_suitability(request, llm, settings.default_model)


@app.post("/banker/product", response_model=BBBankProductResponse, tags=["banker"])
async def banker_product(request: BBBankProductQuery) -> BBBankProductResponse:
    """Answer a BBBank product or advisory query."""
    llm = _llm_or_503()
    return await banker_agent.answer_product_query(request, llm, settings.default_model)


@app.post("/banker/scenario", response_model=ClientScenarioResponse, tags=["banker"])
async def banker_scenario(request: ClientScenarioRequest) -> ClientScenarioResponse:
    """Run a Praxisnachweis client advisory scenario for training."""
    llm = _llm_or_503()
    return await banker_agent.run_scenario(request, llm, settings.default_model)


# ============================================================================
# LEDGER endpoints
# ============================================================================
@app.post("/ledger/categorize", response_model=list[CategorizedTransaction], tags=["ledger"])
async def ledger_categorize(request: TransactionCategorizationRequest) -> list[CategorizedTransaction]:
    """Categorise transactions and flag German tax events."""
    llm = _llm_or_503()
    return await ledger_agent.categorize_transactions(request, llm, settings.default_model)


@app.post("/ledger/reconcile", response_model=ReconciliationResult, tags=["ledger"])
async def ledger_reconcile(request: ReconciliationRequest) -> ReconciliationResult:
    """Nightly reconciliation: internal positions vs exchange positions."""
    return ledger_agent.reconcile(request)


@app.post("/ledger/net-worth", response_model=NetWorthSnapshot, tags=["ledger"])
async def ledger_net_worth(
    liquid_eur: float, illiquid_eur: float, crypto_eur: float
) -> NetWorthSnapshot:
    """Record a net worth snapshot."""
    return ledger_agent.record_net_worth(
        Decimal(str(liquid_eur)), Decimal(str(illiquid_eur)), Decimal(str(crypto_eur))
    )


@app.get("/ledger/net-worth", response_model=list[NetWorthSnapshot], tags=["ledger"])
async def ledger_net_worth_history(limit: int = 30) -> list[NetWorthSnapshot]:
    return ledger_agent.get_net_worth_history(limit)


@app.get("/ledger/tax-report", response_model=TaxReport, tags=["ledger"])
async def ledger_tax_report(period: str = "current") -> TaxReport:
    """Generate German tax report for a given period."""
    return ledger_agent.generate_tax_report(period)


# ============================================================================
# Skill endpoints
# ============================================================================
@app.post("/skills/equity-research", response_model=EquityResearchReport, tags=["skills"])
async def run_equity_research(request: EquityResearchRequest) -> EquityResearchReport:
    """Generate an 8-section institutional equity research report (~5 minutes)."""
    llm = _llm_or_503()
    return await skill_equity.generate_report(request, llm, settings.default_model)


@app.post("/skills/prediction-market-coach", response_model=TradeGrade, tags=["skills"])
async def run_prediction_market_coach(request: TradeGradeRequest) -> TradeGrade:
    """Grade a prediction market trade A–F on process quality. Kelly audit + bias detection."""
    llm = _llm_or_503()
    return await skill_coach.grade_trade(request, llm, settings.default_model)


@app.post("/skills/financial-dispatch", response_model=DispatchArticle, tags=["skills"])
async def run_financial_dispatch(request: DispatchRequest) -> DispatchArticle:
    """Generate an FT/Reuters-style financial briefing article."""
    llm = _llm_or_503()
    return await skill_dispatch.generate_article(request, llm, settings.default_model)
