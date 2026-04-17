"""
Finance Division models — Project Francesca.

Covers all five agents: COMPLIANCE, QUANT, ORACLE, BANKER, LEDGER.
And the three financial skills: equity-research, prediction-market-coach, financial-dispatch.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared enums
# ---------------------------------------------------------------------------
class ComplianceVerdict(str, Enum):
    PASS = "PASS"
    BLOCK = "BLOCK"


class DrawdownLevel(str, Enum):
    NORMAL = "normal"          # < 10%
    WARNING = "warning"        # 10-20%  → sizes halved
    HALT_24H = "halt_24h"      # 20-30%  → full 24h halt
    HALT_72H = "halt_72h"      # > 30%   → 72h halt + incident review


class MarketAlertSeverity(str, Enum):
    P0 = "P0"   # Immediate: >2% index move, major CB statement, geopolitical tier-1
    P1 = "P1"   # High: notable move, significant news
    P2 = "P2"   # Informational


class GermanTaxEvent(str, Enum):
    ABGELTUNGSSTEUER = "abgeltungssteuer"  # Capital gains tax 25%
    HALTEFRIST_APPROACHING = "haltefrist_approaching"  # Crypto 1-year window warning
    HALTEFRIST_REACHED = "haltefrist_reached"          # Crypto 1-year exemption active
    VERLUSTVERRECHNUNG = "verlustverrechnung"           # Loss offset opportunity
    SPARERPAUSCHBETRAG_WARNING = "sparerpauschbetrag_warning"  # Approaching €1k allowance


# ---------------------------------------------------------------------------
# COMPLIANCE models
# ---------------------------------------------------------------------------
class TradeProposal(BaseModel):
    """A trade proposed by QUANT that must pass COMPLIANCE before execution."""
    proposal_id: str
    symbol: str
    direction: str              # "long" | "short" | "close"
    size_eur: Decimal           # Proposed position size in EUR
    account_equity_eur: Decimal # Current total account equity
    kelly_fraction: float       # Computed fractional Kelly (should be ≤0.33)
    market: str                 # "polymarket" | "binance" | "coinbase" | "kraken"
    rationale: str
    proposed_at: datetime = Field(default_factory=datetime.utcnow)


class ComplianceAuditEntry(BaseModel):
    """Immutable audit record for every COMPLIANCE decision."""
    entry_id: str
    proposal_id: str
    verdict: ComplianceVerdict
    ruleset_version: str
    rules_checked: list[str]
    violations: list[str]       # Empty if PASS
    rationale: str
    checked_at: datetime = Field(default_factory=datetime.utcnow)
    blackout_active: bool = False
    drawdown_level: DrawdownLevel = DrawdownLevel.NORMAL


class ComplianceResult(BaseModel):
    verdict: ComplianceVerdict
    violations: list[str]
    rationale: str
    audit_entry: ComplianceAuditEntry
    timed_out: bool = False


class ComplianceStatusResponse(BaseModel):
    ruleset_version: str
    ruleset_updated_at: datetime
    blackout_active: bool
    blackout_reason: str | None = None
    current_drawdown_level: DrawdownLevel
    audit_log_entries: int
    healthy: bool


# ---------------------------------------------------------------------------
# QUANT models
# ---------------------------------------------------------------------------
class QuantTradeRequest(BaseModel):
    """User or agent requests QUANT to evaluate and execute a trade."""
    symbol: str
    direction: str = Field(..., pattern="^(long|short|close)$")
    size_eur: Decimal = Field(..., gt=0)
    market: str = Field(default="binance")
    rationale: str
    edge_estimate: float = Field(..., ge=0.0, le=1.0,
                                 description="Estimated edge (P(win) for binary outcomes)")
    odds: float = Field(default=1.0, ge=0.1,
                        description="Decimal odds (1.0 = even money)")


class DrawdownState(BaseModel):
    current_drawdown_pct: float = 0.0
    peak_equity_eur: Decimal = Decimal("0")
    current_equity_eur: Decimal = Decimal("0")
    level: DrawdownLevel = DrawdownLevel.NORMAL
    halt_until: datetime | None = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class QuantTradeResponse(BaseModel):
    request_id: str
    symbol: str
    compliance_verdict: ComplianceVerdict
    executed: bool
    kelly_fraction_used: float | None = None
    final_size_eur: Decimal | None = None
    drawdown_level: DrawdownLevel
    message: str
    audit_entry_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QuantStatusResponse(BaseModel):
    trading_active: bool
    drawdown_state: DrawdownState
    open_positions: int
    pnl_today_eur: Decimal
    compliance_pass_rate: float   # pct of proposals that passed this session
    last_trade_at: datetime | None


# ---------------------------------------------------------------------------
# ORACLE models
# ---------------------------------------------------------------------------
class MarketSnapshot(BaseModel):
    symbol: str
    price: float
    change_pct_24h: float
    currency: str = "USD"
    source: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MarketAlert(BaseModel):
    alert_id: str
    severity: MarketAlertSeverity
    symbol: str
    trigger: str               # e.g. "DAX -2.3% in 15 min"
    narrative: str             # Brief explanation
    action_required: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MarketBriefingRequest(BaseModel):
    """Request for ORACLE to produce a market briefing."""
    language: str = Field(default="de", description="'de' for German, 'en' for English")
    scope: str = Field(
        default="weekly",
        description="'morning'|'european_close'|'us_close'|'weekly'",
    )
    include_sectors: list[str] = Field(
        default=["DAX 40", "S&P 500", "BTC/ETH", "EUR/USD"],
    )
    style: str = Field(default="bbbank_internal", description="'bbbank_internal'|'dispatch'")


class MarketBriefing(BaseModel):
    briefing_id: str
    scope: str
    language: str
    headline: str
    body: str
    key_movers: list[dict[str, Any]]
    macro_drivers: list[str]
    central_bank_watch: list[str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class OracleStatusResponse(BaseModel):
    monitored_symbols: list[str]
    alerts_active: int
    last_briefing_at: datetime | None
    next_briefing_scope: str
    healthy: bool


# ---------------------------------------------------------------------------
# BANKER models
# ---------------------------------------------------------------------------
class MiFIDSuitabilityRequest(BaseModel):
    """MiFID II suitability assessment for a client–product scenario."""
    client_description: str = Field(
        ..., min_length=20,
        description="Brief client profile: age, income, experience, objectives, risk tolerance",
    )
    product: str = Field(..., description="BBBank product or investment product name")
    investment_amount_eur: Decimal | None = None
    investment_horizon_years: float | None = None


class MiFIDSuitabilityResult(BaseModel):
    product: str
    suitability: str          # "suitable" | "potentially_suitable" | "not_suitable"
    justification: str
    required_disclosures: list[str]
    recommendation: str
    assessed_at: datetime = Field(default_factory=datetime.utcnow)


class BBBankProductQuery(BaseModel):
    """Query about a BBBank product."""
    query: str = Field(..., min_length=10)
    client_context: str | None = None


class BBBankProductResponse(BaseModel):
    query: str
    products_discussed: list[str]
    response: str
    compliance_notes: list[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ClientScenarioRequest(BaseModel):
    """Praxisnachweis role-play scenario simulation."""
    scenario_description: str = Field(..., min_length=20)
    play_role: str = Field(
        default="advisor",
        description="'advisor' (BANKER coaches) | 'client' (BANKER plays client)",
    )
    product_focus: str | None = None


class ClientScenarioResponse(BaseModel):
    scenario_id: str
    scenario_description: str
    dialogue: list[dict[str, str]]   # [{"role": "advisor|client", "message": "..."}]
    coaching_notes: list[str]
    compliance_checkpoints: list[str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# LEDGER models
# ---------------------------------------------------------------------------
class Transaction(BaseModel):
    tx_id: str
    amount_eur: Decimal
    description: str
    category: str | None = None
    account: str                      # "main_bank" | "crypto_binance" | "polymarket" etc.
    timestamp: datetime
    is_taxable_event: bool = False
    tax_event_type: GermanTaxEvent | None = None


class TransactionCategorizationRequest(BaseModel):
    transactions: list[Transaction]
    context_hint: str | None = Field(
        default=None,
        description="Optional hint (e.g. 'these are crypto trades from last month')",
    )


class CategorizedTransaction(BaseModel):
    tx_id: str
    original_description: str
    category: str
    sub_category: str | None = None
    is_taxable_event: bool
    tax_event_type: GermanTaxEvent | None = None
    tax_amount_eur: Decimal | None = None
    notes: str | None = None


class ReconciliationRequest(BaseModel):
    """Nightly reconciliation: LEDGER internal vs exchange APIs."""
    date: str = Field(..., description="ISO date YYYY-MM-DD")
    internal_positions: dict[str, Decimal]   # symbol → quantity
    exchange_positions: dict[str, Decimal]   # symbol → quantity from exchange


class ReconciliationResult(BaseModel):
    date: str
    discrepancies: list[dict[str, Any]]     # [{symbol, internal, exchange, diff_eur}]
    all_matched: bool
    alert_triggered: bool                   # True if any diff > €1
    reconciled_at: datetime = Field(default_factory=datetime.utcnow)


class NetWorthSnapshot(BaseModel):
    snapshot_id: str
    liquid_eur: Decimal
    illiquid_eur: Decimal
    crypto_eur: Decimal
    total_eur: Decimal
    sparerpauschbetrag_used_eur: Decimal = Decimal("0")
    sparerpauschbetrag_remaining_eur: Decimal = Decimal("1000")
    as_of: datetime = Field(default_factory=datetime.utcnow)


class TaxReport(BaseModel):
    period: str              # e.g. "2025-Q4"
    abgeltungssteuer_eur: Decimal
    realised_gains_eur: Decimal
    realised_losses_eur: Decimal
    loss_carryforward_eur: Decimal
    crypto_taxable_eur: Decimal
    crypto_exempt_eur: Decimal   # Held > 1 year
    tax_events: list[CategorizedTransaction]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Skill request/response models
# ---------------------------------------------------------------------------

# equity-research
class EquityResearchRequest(BaseModel):
    ticker: str = Field(..., description="Ticker symbol, e.g. 'AAPL', 'SAP.DE'")
    company_name: str
    sector: str | None = None
    additional_context: str | None = None
    language: str = Field(default="en", description="'en' | 'de'")


class EquityResearchReport(BaseModel):
    ticker: str
    company_name: str
    sections: dict[str, str]  # section_name → content (8 sections)
    verdict: str              # "Buy" | "Hold" | "Sell" | "Underweight" | "Overweight"
    price_target: str | None = None
    key_risks: list[str]
    key_catalysts: list[str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# prediction-market-coach
class TradeGradeRequest(BaseModel):
    market_description: str = Field(..., description="What was the prediction market?")
    your_position: str = Field(..., description="What position did you take and why?")
    outcome: str = Field(..., description="Won/Lost and what happened?")
    size_pct_of_bankroll: float = Field(..., ge=0.0, le=100.0)
    estimated_edge_at_entry: float = Field(..., ge=0.0, le=1.0)
    odds_at_entry: float = Field(..., ge=0.01)


class TradeGrade(BaseModel):
    grade: str                    # A / B / C / D / F
    process_score: float          # 0-10 (process, not outcome)
    kelly_compliance: str         # "optimal" | "over" | "under"
    kelly_recommended_pct: float
    biases_detected: list[str]    # e.g. ["recency_bias", "overconfidence"]
    strengths: list[str]
    improvements: list[str]
    coaching_note: str
    graded_at: datetime = Field(default_factory=datetime.utcnow)


# financial-dispatch
class DispatchRequest(BaseModel):
    scope: str = Field(
        ...,
        description="'morning'|'european_close'|'us_close'|'weekly'",
    )
    seed_data: str = Field(
        ...,
        min_length=100,
        description="Raw market data / price moves / news items to turn into journalism",
    )
    language: str = Field(default="en")
    word_count_target: int = Field(default=800, ge=400, le=1500)


class DispatchArticle(BaseModel):
    article_id: str
    scope: str
    headline: str
    subheadline: str
    body: str
    word_count: int
    published_at: datetime = Field(default_factory=datetime.utcnow)
