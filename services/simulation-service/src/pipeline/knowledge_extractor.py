"""
Step 1 of MiroFish pipeline: Knowledge Graph Construction.

Extracts financial entities and relationships from seed text,
building a lightweight GraphRAG structure for agent context injection.
"""
from __future__ import annotations

import json
import logging

from openai import AsyncOpenAI

from ..config import settings
from ..models import Entity, KnowledgeGraph

logger = logging.getLogger(__name__)

_EXTRACTION_SYSTEM = """\
You are a financial intelligence analyst. Given seed text containing market data,
news, or financial reports, extract a structured knowledge graph.

Return a JSON object with:
{
  "entities": [
    {"name": "<name>", "entity_type": "<asset|event|institution|person|indicator>", "relevance": <0.0-1.0>}
  ],
  "relationships": [
    {"source": "<entity>", "relation": "<relation>", "target": "<entity>"}
  ],
  "summary": "<2-3 sentence factual summary of the seed content>"
}

Focus on: assets (stocks, crypto, ETFs, indices), economic events (earnings, rate decisions,
geopolitical), institutions (ECB, Fed, companies), indicators (VIX, yield curve, CPI),
and key people (central bank governors, CEOs). Limit to the 20 most relevant entities.
"""


async def extract_knowledge_graph(
    seed_text: str,
    client: AsyncOpenAI,
    model: str,
) -> KnowledgeGraph:
    """
    Extract entities and relationships from seed text.
    Returns a KnowledgeGraph for agent context injection.
    """
    logger.info("Extracting knowledge graph from %d chars of seed text", len(seed_text))

    # Truncate seed if needed (model context safety)
    truncated = seed_text[:12_000] if len(seed_text) > 12_000 else seed_text

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _EXTRACTION_SYSTEM},
            {"role": "user", "content": f"Extract knowledge graph from:\n\n{truncated}"},
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    raw = response.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Failed to parse knowledge graph JSON, using fallback")
        data = {"entities": [], "relationships": [], "summary": seed_text[:200]}

    entities = [Entity(**e) for e in data.get("entities", [])]
    relationships = data.get("relationships", [])
    summary = data.get("summary", "")

    logger.info(
        "Knowledge graph: %d entities, %d relationships", len(entities), len(relationships)
    )
    return KnowledgeGraph(entities=entities, relationships=relationships, summary=summary)
