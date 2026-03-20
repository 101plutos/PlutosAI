"""
BANKER Agent — Project Francesca, Finance Division.

Retail Banking Advisor. Covers BBBank eG product suite (mortgages via
Schwäbisch Hall, VL ETF, Girokonto, etc.), MiFID II suitability assessments,
client scenario simulation (Praxisnachweis role-play), and objection handling.

All client-facing advice drafts are reviewed by COMPLIANCE before delivery.
No autonomous client communication — HERALD handles transmission.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from openai import AsyncOpenAI

from ..models import (
    BBBankProductQuery,
    BBBankProductResponse,
    ClientScenarioRequest,
    ClientScenarioResponse,
    MiFIDSuitabilityRequest,
    MiFIDSuitabilityResult,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# BBBank product knowledge base (local — never transmitted to cloud APIs)
# Production: load from local vector DB via SCRIBE
# ---------------------------------------------------------------------------
_BBBANK_PRODUCTS = """
BBBank eG Product Suite (German cooperative bank):

GIROKONTO:
  - Free current account for members
  - VISA debit card, online banking, mobile banking (BBBank App)
  - No monthly fee for active members
  - Instant SEPA transfers

TAGESGELD / FESTGELD:
  - Competitive savings rates (updated regularly)
  - Covered by German deposit insurance (Einlagensicherung) up to €100,000
  - Festgeld: fixed terms 1–60 months

VL-BAUSPARVERTRAG (via Schwäbisch Hall):
  - Vermögenswirksame Leistungen (VL) — employer savings benefit
  - 6-year savings phase + mortgage readiness
  - State bonus: up to €512/year (Wohnungsbauprämie) for eligible earners

VL-ETF SPARPLAN:
  - VL-eligible ETF savings plan (usually iShares Core MSCI World UCITS ETF)
  - €40/month default VL contribution (employer + employee)
  - Suitable for members with investment horizon ≥ 5 years
  - MiFID II suitability: moderate risk minimum

BAUFINANZIERUNG (via Schwäbisch Hall):
  - Annuity mortgages (Annuitätendarlehen)
  - Repayment rates: 1–5%
  - Fixed interest periods: 5, 10, 15, 20 years
  - Special repayment right: 5% p.a. additional repayment without penalty

PRIVATKREDIT:
  - Personal loans: €3,000–€60,000
  - Terms: 12–84 months
  - No early repayment fee for consumer loans (EU Consumer Credit Directive)

DEPOT (WERTPAPIERDEPOT):
  - Custody account for ETFs, funds, stocks, bonds
  - Integrated with VL savings plans
  - Online order execution via comdirect integration

MIFID II PRODUCT CATEGORIES:
  Girokonto/Tagesgeld: No MiFID scope (banking products)
  VL-ETF: MiFID II applies — suitability required
  Depot/Wertpapiere: MiFID II applies — full suitability assessment
  Baufinanzierung: Mortgage Credit Directive applies (not MiFID II)
"""

_MIFID_SYSTEM = """\
You are BANKER, a MiFID II compliance specialist at BBBank eG.
Perform a suitability assessment for the proposed investment product and client profile.

BBBank product knowledge:
{product_kb}

Assess:
1. Knowledge and experience of the client
2. Financial situation (income, savings, obligations)
3. Investment objectives (growth, income, capital preservation)
4. Risk tolerance and capacity for loss
5. Investment horizon

Return a structured assessment: suitability verdict, justification,
required disclosures, and your recommendation. Be specific to German regulatory requirements.
"""

_PRODUCT_SYSTEM = """\
You are BANKER, a retail banking advisor at BBBank eG (German cooperative bank).
You have deep knowledge of the BBBank product suite and German banking regulation.
Answer the query accurately and helpfully. Flag any MiFID II or consumer protection
considerations. Never promise rates — state they are subject to change.
Respond in the same language as the query.

BBBank product knowledge:
{product_kb}
"""

_SCENARIO_SYSTEM = """\
You are BANKER, a retail banking advisor training tool for BBBank eG.
Run a realistic client conversation scenario for Praxisnachweis (practical competency) training.

You will simulate a structured advisory dialogue. Include:
- Realistic client objections
- Regulatory disclosure moments (Beratungsprotokoll, MiFID II)
- Product suitability checkpoints
- Objection handling techniques

After the dialogue, provide coaching notes on what was done well and what to improve.
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
async def assess_mifid_suitability(
    request: MiFIDSuitabilityRequest,
    client: AsyncOpenAI,
    model: str,
) -> MiFIDSuitabilityResult:
    """MiFID II suitability assessment for a client–product combination."""
    logger.info("BANKER MiFID II suitability for: %s", request.product)

    system = _MIFID_SYSTEM.format(product_kb=_BBBANK_PRODUCTS)
    user_msg = (
        f"Client Profile: {request.client_description}\n"
        f"Product: {request.product}\n"
        f"Investment Amount: €{request.investment_amount_eur or 'not specified'}\n"
        f"Investment Horizon: {request.investment_horizon_years or 'not specified'} years\n\n"
        "Perform MiFID II suitability assessment."
    )

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.3,
        max_tokens=800,
    )
    text = response.choices[0].message.content or ""

    # Parse suitability verdict from response
    suitability = _extract_suitability(text)
    recommendation = _extract_recommendation(text)

    return MiFIDSuitabilityResult(
        product=request.product,
        suitability=suitability,
        justification=text,
        required_disclosures=_standard_disclosures(request.product),
        recommendation=recommendation,
    )


async def answer_product_query(
    request: BBBankProductQuery,
    client: AsyncOpenAI,
    model: str,
) -> BBBankProductResponse:
    """Answer a BBBank product or advisory query."""
    logger.info("BANKER product query: %s", request.query[:60])

    system = _PRODUCT_SYSTEM.format(product_kb=_BBBANK_PRODUCTS)
    user_msg = request.query
    if request.client_context:
        user_msg = f"Client context: {request.client_context}\n\nQuery: {request.query}"

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.4,
        max_tokens=600,
    )
    text = response.choices[0].message.content or ""

    return BBBankProductResponse(
        query=request.query,
        products_discussed=_extract_products_mentioned(text),
        response=text,
        compliance_notes=_standard_compliance_notes(),
    )


async def run_scenario(
    request: ClientScenarioRequest,
    client: AsyncOpenAI,
    model: str,
) -> ClientScenarioResponse:
    """Run a Praxisnachweis client scenario role-play."""
    logger.info("BANKER scenario: %s", request.scenario_description[:60])

    user_msg = (
        f"Scenario: {request.scenario_description}\n"
        f"Role: {'BANKER plays client, user plays advisor' if request.play_role == 'client' else 'BANKER coaches the advisory session'}\n"
        + (f"Product focus: {request.product_focus}" if request.product_focus else "")
    )

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SCENARIO_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.6,
        max_tokens=1200,
    )
    text = response.choices[0].message.content or ""

    # Split into dialogue and coaching notes at a separator
    parts = text.split("---COACHING---") if "---COACHING---" in text else [text, ""]
    dialogue_text = parts[0].strip()
    coaching_text = parts[1].strip() if len(parts) > 1 else ""

    dialogue = _parse_dialogue(dialogue_text)
    coaching_notes = [l.strip() for l in coaching_text.split("\n") if l.strip()] or [coaching_text]

    return ClientScenarioResponse(
        scenario_id=str(uuid.uuid4()),
        scenario_description=request.scenario_description,
        dialogue=dialogue,
        coaching_notes=coaching_notes,
        compliance_checkpoints=_compliance_checkpoints(request.product_focus),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _extract_suitability(text: str) -> str:
    lower = text.lower()
    if "not suitable" in lower or "nicht geeignet" in lower or "ungeeignet" in lower:
        return "not_suitable"
    if "potentially" in lower or "bedingt" in lower:
        return "potentially_suitable"
    return "suitable"


def _extract_recommendation(text: str) -> str:
    lines = [l.strip() for l in text.split("\n") if "recommend" in l.lower() or "empfehl" in l.lower()]
    return lines[0] if lines else "See full assessment above."


def _standard_disclosures(product: str) -> list[str]:
    base = ["Past performance does not guarantee future results."]
    if "ETF" in product or "depot" in product.lower():
        base += [
            "Capital at risk. Investment value can fall as well as rise.",
            "MiFID II: Beratungsprotokoll must be provided before investment.",
            "PRIIPs KID (Key Information Document) must be provided for packaged products.",
        ]
    if "bau" in product.lower() or "mortgage" in product.lower():
        base += [
            "Mortgage Credit Directive applies — ESIS document required.",
            "Repayment capacity assessment required under §505 BGB.",
        ]
    return base


def _standard_compliance_notes() -> list[str]:
    return [
        "This response is for advisory training purposes.",
        "All product rates and terms subject to current BBBank pricing.",
        "MiFID II suitability check required before investment recommendation.",
    ]


def _extract_products_mentioned(text: str) -> list[str]:
    keywords = [
        "Girokonto", "Tagesgeld", "Festgeld", "VL-ETF", "VL-Bausparvertrag",
        "Baufinanzierung", "Privatkredit", "Depot", "Sparplan",
    ]
    return [k for k in keywords if k.lower() in text.lower()]


def _compliance_checkpoints(product_focus: str | None) -> list[str]:
    checkpoints = [
        "Legitimationsprüfung (KYC) completed?",
        "Beratungsprotokoll prepared?",
        "MiFID II suitability confirmed?",
        "Client investment objectives documented?",
    ]
    if product_focus and ("ETF" in product_focus or "Depot" in product_focus):
        checkpoints.append("PRIIPs KID provided?")
        checkpoints.append("Risk category explained to client?")
    return checkpoints


def _parse_dialogue(text: str) -> list[dict[str, str]]:
    lines = text.split("\n")
    dialogue = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("Berater:") or line.startswith("Advisor:"):
            dialogue.append({"role": "advisor", "message": line.split(":", 1)[1].strip()})
        elif line.startswith("Kunde:") or line.startswith("Client:"):
            dialogue.append({"role": "client", "message": line.split(":", 1)[1].strip()})
        else:
            # Append to last entry if continuation
            if dialogue:
                dialogue[-1]["message"] += " " + line
    return dialogue if dialogue else [{"role": "advisor", "message": text}]
