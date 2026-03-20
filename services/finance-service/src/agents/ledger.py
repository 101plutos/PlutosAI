"""
LEDGER Agent — Project Francesca, Finance Division.

Personal Finance Controller. Handles:
  - Daily transaction categorisation across all accounts
  - Net worth tracking (liquid, illiquid, crypto)
  - German tax event flagging (Abgeltungssteuer, Haltefrist, Verlustverrechnung)
  - Nightly reconciliation: internal positions vs exchange APIs
  - Annual Sparerpauschbetrag (€1,000 allowance) tracking

Nightly reconciliation runs at 23:00 CET.
Any discrepancy > €1 triggers an alert to Flo.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from openai import AsyncOpenAI

from ..config import settings
from ..models import (
    CategorizedTransaction,
    GermanTaxEvent,
    NetWorthSnapshot,
    ReconciliationRequest,
    ReconciliationResult,
    TaxReport,
    Transaction,
    TransactionCategorizationRequest,
)

logger = logging.getLogger(__name__)

# In-memory store (production: PostgreSQL)
_net_worth_history: list[NetWorthSnapshot] = []
_categorized_txs: list[CategorizedTransaction] = []
_sparerpauschbetrag_used: Decimal = Decimal("0")

_CATEGORIZATION_SYSTEM = """\
You are LEDGER, a German personal finance controller. Categorise each transaction
and identify German tax events. Return a JSON array with one object per transaction:

{
  "tx_id": "<id>",
  "category": "<Housing|Food|Transport|Entertainment|Investment|Trading|Salary|Tax|Other>",
  "sub_category": "<optional sub-category>",
  "is_taxable_event": <true|false>,
  "tax_event_type": "<abgeltungssteuer|haltefrist_approaching|haltefrist_reached|verlustverrechnung|sparerpauschbetrag_warning|null>",
  "tax_amount_eur": <number or null>,
  "notes": "<brief note if tax event>"
}

German tax rules:
- Abgeltungssteuer: 25% flat tax on capital gains, dividends, interest exceeding Sparerpauschbetrag
- Haltefrist: Crypto held > 365 days is tax-free (flag as haltefrist_reached)
- Crypto held < 365 days and sold at profit: abgeltungssteuer applies
- Sparerpauschbetrag: €1,000/year exemption per individual
- Verlustverrechnung: Capital losses can offset gains of same type
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
async def categorize_transactions(
    request: TransactionCategorizationRequest,
    client: AsyncOpenAI,
    model: str,
) -> list[CategorizedTransaction]:
    """Categorise transactions and flag German tax events."""
    logger.info("LEDGER categorising %d transactions", len(request.transactions))

    txs_json = "\n".join(
        f'{{"tx_id":"{t.tx_id}","amount_eur":{t.amount_eur},"description":"{t.description}",'
        f'"account":"{t.account}","timestamp":"{t.timestamp.isoformat()}"}}'
        for t in request.transactions
    )
    hint = f"\nContext: {request.context_hint}" if request.context_hint else ""

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _CATEGORIZATION_SYSTEM},
            {
                "role": "user",
                "content": f"Categorise these transactions:{hint}\n\n{txs_json}",
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
        max_tokens=1500,
    )

    import json
    raw = response.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
        items = data if isinstance(data, list) else data.get("transactions", [data])
    except json.JSONDecodeError:
        logger.error("LEDGER: failed to parse categorization JSON")
        items = []

    results: list[CategorizedTransaction] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        tax_event_raw = item.get("tax_event_type")
        tax_event = None
        if tax_event_raw and tax_event_raw != "null":
            try:
                tax_event = GermanTaxEvent(tax_event_raw)
            except ValueError:
                pass

        tax_amount = item.get("tax_amount_eur")
        cat = CategorizedTransaction(
            tx_id=item.get("tx_id", "unknown"),
            original_description=next(
                (t.description for t in request.transactions if t.tx_id == item.get("tx_id")), ""
            ),
            category=item.get("category", "Other"),
            sub_category=item.get("sub_category"),
            is_taxable_event=bool(item.get("is_taxable_event", False)),
            tax_event_type=tax_event,
            tax_amount_eur=Decimal(str(tax_amount)) if tax_amount else None,
            notes=item.get("notes"),
        )
        results.append(cat)

        # Track Sparerpauschbetrag usage
        if tax_event == GermanTaxEvent.ABGELTUNGSSTEUER and tax_amount:
            _sparerpauschbetrag_used += Decimal(str(tax_amount)) / Decimal(str(settings.abgeltungssteuer_rate))

    _categorized_txs.extend(results)
    logger.info("LEDGER: categorised %d transactions (%d taxable events)",
                len(results), sum(1 for r in results if r.is_taxable_event))
    return results


def reconcile(request: ReconciliationRequest) -> ReconciliationResult:
    """
    Nightly reconciliation: compare internal ledger vs live exchange positions.
    Alert on any discrepancy > €1.
    """
    logger.info("LEDGER nightly reconciliation for %s", request.date)

    all_symbols = set(request.internal_positions) | set(request.exchange_positions)
    discrepancies = []

    for symbol in all_symbols:
        internal = request.internal_positions.get(symbol, Decimal("0"))
        exchange = request.exchange_positions.get(symbol, Decimal("0"))
        diff = (exchange - internal).copy_abs()
        # Using 1 EUR as materiality threshold (proxy — production: multiply by market price)
        if diff > Decimal("0.001"):  # quantity diff threshold
            discrepancies.append({
                "symbol": symbol,
                "internal": float(internal),
                "exchange": float(exchange),
                "difference": float(exchange - internal),
            })

    alert_triggered = len(discrepancies) > 0
    if alert_triggered:
        logger.warning(
            "LEDGER reconciliation DISCREPANCY on %s: %d symbol(s) differ — %s",
            request.date, len(discrepancies), discrepancies,
        )
    else:
        logger.info("LEDGER reconciliation CLEAN for %s", request.date)

    return ReconciliationResult(
        date=request.date,
        discrepancies=discrepancies,
        all_matched=not alert_triggered,
        alert_triggered=alert_triggered,
    )


def record_net_worth(
    liquid_eur: Decimal,
    illiquid_eur: Decimal,
    crypto_eur: Decimal,
) -> NetWorthSnapshot:
    """Record a net worth snapshot."""
    remaining = Decimal(str(settings.sparerpauschbetrag_eur)) - _sparerpauschbetrag_used
    snapshot = NetWorthSnapshot(
        snapshot_id=str(uuid.uuid4()),
        liquid_eur=liquid_eur,
        illiquid_eur=illiquid_eur,
        crypto_eur=crypto_eur,
        total_eur=liquid_eur + illiquid_eur + crypto_eur,
        sparerpauschbetrag_used_eur=_sparerpauschbetrag_used,
        sparerpauschbetrag_remaining_eur=max(Decimal("0"), remaining),
    )
    _net_worth_history.append(snapshot)
    logger.info("LEDGER net worth snapshot: total=€%s", snapshot.total_eur)
    return snapshot


def generate_tax_report(period: str) -> TaxReport:
    """Generate a German tax summary for a given period."""
    taxable = [t for t in _categorized_txs if t.is_taxable_event]
    gains = sum(
        (t.tax_amount_eur or Decimal("0")) / Decimal(str(settings.abgeltungssteuer_rate))
        for t in taxable
        if t.tax_event_type == GermanTaxEvent.ABGELTUNGSSTEUER
        and (t.tax_amount_eur or Decimal("0")) > 0
    )
    losses = sum(
        (t.tax_amount_eur or Decimal("0")).copy_abs()
        for t in taxable
        if t.tax_event_type == GermanTaxEvent.VERLUSTVERRECHNUNG
    )
    crypto_taxable = sum(
        (t.tax_amount_eur or Decimal("0")) / Decimal(str(settings.abgeltungssteuer_rate))
        for t in taxable
        if t.tax_event_type == GermanTaxEvent.ABGELTUNGSSTEUER
        and t.sub_category == "crypto"
    )
    crypto_exempt = sum(
        (t.tax_amount_eur or Decimal("0"))
        for t in taxable
        if t.tax_event_type == GermanTaxEvent.HALTEFRIST_REACHED
    )
    abgeltungssteuer = sum(
        t.tax_amount_eur or Decimal("0")
        for t in taxable
        if t.tax_event_type == GermanTaxEvent.ABGELTUNGSSTEUER
    )

    return TaxReport(
        period=period,
        abgeltungssteuer_eur=abgeltungssteuer,
        realised_gains_eur=gains,
        realised_losses_eur=losses,
        loss_carryforward_eur=max(Decimal("0"), losses - gains),
        crypto_taxable_eur=crypto_taxable,
        crypto_exempt_eur=crypto_exempt,
        tax_events=taxable,
    )


def get_net_worth_history(limit: int = 30) -> list[NetWorthSnapshot]:
    return list(reversed(_net_worth_history))[:limit]
