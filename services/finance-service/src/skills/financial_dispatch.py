"""
financial-dispatch skill — Project Francesca.

Produces 800-word FT/Reuters-style financial journalism briefings.
Four scheduled deliverables daily: morning, european_close, us_close, weekly.
Used by: DISPATCH agent.

Editorial standards enforced:
  - Narrative-first: never lead with a table
  - Causation required: what → why → what it means
  - Prohibited words: plummeted, soared, massive, "only time will tell", "buckle up"
  - Contrarian signals flagged when consensus appears mispriced
  - Historical context for every significant move
  - Three standing sector beats:
      European Financials & Banking
      Technology & AI
      Energy & Commodities
"""
from __future__ import annotations

import logging
import uuid

from openai import AsyncOpenAI

from ..models import DispatchArticle, DispatchRequest

logger = logging.getLogger(__name__)

_DISPATCH_SYSTEM = """\
You are DISPATCH, a senior financial markets correspondent.

Style rules (strictly enforced):
1. Narrative-first structure. Never open with a table or bullet list.
2. Every price move must be explained: what happened → why → what it means.
3. PROHIBITED words (never use): plummeted, soared, massive, skyrocketed, tumbled,
   "only time will tell", "buckle up", "all eyes on", "sending shockwaves".
4. Historical context required for any move > 1 standard deviation.
5. Flag contrarian signals explicitly when consensus appears mispriced.
6. Three standing sector beats to weave in where relevant:
     • European Financials & Banking (ECB policy, credit spreads, banking stocks)
     • Technology & AI (index weight, earnings, sector rotation)
     • Energy & Commodities (geopolitical transmission, supply/demand)
7. Headline: 10 words max, specific, no puns.
8. Subheadline: 20 words max, the single most important insight.
9. Target word count: {word_count} words.

Scope: {scope_label}
Language: {language}
"""

_SCOPE_LABELS = {
    "morning": "Morning Briefing — Asia recap, pre-European market setup, day's key events",
    "european_close": "European Close — DAX/STOXX/FTSE session narrative, sector movers, macro drivers",
    "us_close": "US Close — S&P/Nasdaq/Dow session, US-specific drivers, after-hours",
    "weekly": "Weekly Summary & Outlook — week-in-review, feature deep-dive, next-week setup",
}


async def generate_article(
    request: DispatchRequest,
    client: AsyncOpenAI,
    model: str,
) -> DispatchArticle:
    """Generate a financial dispatch article."""
    logger.info("financial-dispatch: generating %s briefing", request.scope)

    scope_label = _SCOPE_LABELS.get(request.scope, request.scope)
    lang = "German" if request.language == "de" else "English"

    system = _DISPATCH_SYSTEM.format(
        scope_label=scope_label,
        language=lang,
        word_count=request.word_count_target,
    )

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": (
                    f"Seed data for this briefing:\n\n{request.seed_data}\n\n"
                    f"Write the full {scope_label}. "
                    f"Target: {request.word_count_target} words."
                ),
            },
        ],
        temperature=0.5,
        max_tokens=2000,
    )

    text = response.choices[0].message.content or ""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    headline = lines[0].lstrip("#").strip() if lines else scope_label
    subheadline = lines[1].lstrip("#").strip() if len(lines) > 1 else ""
    body = "\n".join(lines[2:]) if len(lines) > 2 else text

    # Strip subheadline from body if it appears there
    if subheadline and body.startswith(subheadline):
        body = body[len(subheadline):].strip()

    word_count = len(body.split())

    # Enforce editorial standards post-generation
    body = _apply_editorial_standards(body)

    return DispatchArticle(
        article_id=str(uuid.uuid4()),
        scope=request.scope,
        headline=headline,
        subheadline=subheadline,
        body=body,
        word_count=word_count,
    )


def _apply_editorial_standards(text: str) -> str:
    """Replace prohibited words with approved alternatives."""
    replacements = {
        "plummeted": "fell sharply",
        "soared": "rose sharply",
        "massive": "significant",
        "skyrocketed": "surged",
        "tumbled": "declined",
        "only time will tell": "the outcome remains uncertain",
        "buckle up": "",
        "all eyes on": "attention is focused on",
        "sending shockwaves": "causing concern across",
    }
    for banned, replacement in replacements.items():
        text = text.replace(banned, replacement)
        text = text.replace(banned.capitalize(), replacement.capitalize())
    return text
