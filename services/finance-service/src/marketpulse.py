"""
MARKETPULSE — Live Price Feed for ORACLE.

Background task that runs inside finance-service. Polls public price APIs
every 60 seconds, pushes snapshots to ORACLE, and fires P0/P1 alerts when
a move exceeds the configured threshold.

Data sources (all free, no auth required for basic tiers):
  - CoinGecko API v3   → BTC, ETH, and other crypto
  - Yahoo Finance      → DAX, S&P 500, Nikkei, EUR/USD, Gold, Oil
    (via public chart endpoint, no API key needed)

Production upgrades:
  - Replace Yahoo with Finnhub (websocket) or OpenBB for institutional feeds
  - Add Polymarket/Kalshi odds polling for QUANT edge inputs
  - Add Bloomberg/Refinitiv for professional data

Alert behaviour:
  - Move ≥ p0_move_threshold_pct (default 2%): POST /oracle/alert → ORACLE fires P0 push
  - Move ≥ 1%:                                  POST /oracle/alert → P1 (no push)
  - All moves:                                   POST /oracle/snapshot (no alert)
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from .config import settings

logger = logging.getLogger(__name__)

# Time between full polling cycles (seconds)
POLL_INTERVAL = 60

# CoinGecko IDs → ORACLE symbol names
CRYPTO_IDS: dict[str, str] = {
    "bitcoin": "BTC-USD",
    "ethereum": "ETH-USD",
    "solana": "SOL-USD",
}

# Yahoo Finance quote symbols → ORACLE symbol names
# Uses the public /v8/finance/chart endpoint (no auth)
YAHOO_SYMBOLS: dict[str, str] = {
    "^GDAXI":  "DAX",       # DAX 40
    "^GSPC":   "SPX",       # S&P 500
    "^N225":   "NKY",       # Nikkei 225
    "EURUSD=X": "EURUSD",   # EUR/USD
    "GC=F":    "XAUUSD",    # Gold futures
    "CL=F":    "CL1",       # Crude Oil WTI
}

# ORACLE base URL (within the same process — internal HTTP call)
_ORACLE_BASE = f"http://localhost:{settings.port}"

# Track previous prices for move calculation
_prev_prices: dict[str, float] = {}


async def run_forever(base_url: str | None = None) -> None:
    """Main polling loop. Runs as an asyncio background task in FastAPI lifespan."""
    url = base_url or _ORACLE_BASE
    async with httpx.AsyncClient(base_url=url, timeout=20.0) as client:
        logger.info("MARKETPULSE started — polling every %ds", POLL_INTERVAL)
        while True:
            try:
                await _poll_cycle(client)
            except asyncio.CancelledError:
                logger.info("MARKETPULSE cancelled — shutting down")
                return
            except Exception as exc:
                logger.warning("MARKETPULSE poll error (retrying in %ds): %s", POLL_INTERVAL, exc)
            await asyncio.sleep(POLL_INTERVAL)


async def _poll_cycle(client: httpx.AsyncClient) -> None:
    """Single poll cycle — fetch all prices and update ORACLE."""
    tasks = [
        _poll_crypto(client),
        _poll_yahoo(client),
    ]
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.debug("MARKETPULSE cycle complete — %d symbols tracked", len(_prev_prices))


# ---------------------------------------------------------------------------
# CoinGecko polling
# ---------------------------------------------------------------------------
async def _poll_crypto(client: httpx.AsyncClient) -> None:
    ids = ",".join(CRYPTO_IDS.keys())
    try:
        resp = await _coingecko_get(
            f"https://api.coingecko.com/api/v3/simple/price"
            f"?ids={ids}&vs_currencies=usd&include_24hr_change=true"
        )
    except Exception as exc:
        logger.debug("CoinGecko unavailable: %s", exc)
        return

    for gecko_id, symbol in CRYPTO_IDS.items():
        data = resp.get(gecko_id, {})
        price = data.get("usd")
        change = data.get("usd_24h_change", 0.0)
        if price is None:
            continue
        await _update_oracle(client, symbol, float(price), float(change), "coingecko")


async def _coingecko_get(url: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.get(url, headers={"accept": "application/json"})
        r.raise_for_status()
        return r.json()


# ---------------------------------------------------------------------------
# Yahoo Finance polling (public endpoint, no API key)
# ---------------------------------------------------------------------------
async def _poll_yahoo(client: httpx.AsyncClient) -> None:
    for yahoo_sym, oracle_sym in YAHOO_SYMBOLS.items():
        try:
            price, change = await _yahoo_quote(yahoo_sym)
            await _update_oracle(client, oracle_sym, price, change, "yahoo_finance")
        except Exception as exc:
            logger.debug("Yahoo quote failed for %s: %s", yahoo_sym, exc)


async def _yahoo_quote(symbol: str) -> tuple[float, float]:
    """Fetch price and 24h change from Yahoo Finance public chart endpoint."""
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        f"?range=2d&interval=1d&includePrePost=false"
    )
    async with httpx.AsyncClient(
        timeout=10.0,
        headers={"User-Agent": "Mozilla/5.0 PlutosAI/MARKETPULSE"},
    ) as c:
        r = await c.get(url)
        r.raise_for_status()
        data = r.json()

    result = data["chart"]["result"][0]
    meta = result["meta"]
    price = float(meta.get("regularMarketPrice", meta.get("previousClose", 0)))
    prev_close = float(meta.get("previousClose", price))
    change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0.0
    return price, change_pct


# ---------------------------------------------------------------------------
# Common: update snapshot + fire alert if warranted
# ---------------------------------------------------------------------------
async def _update_oracle(
    client: httpx.AsyncClient,
    symbol: str,
    price: float,
    change_pct_24h: float,
    source: str,
) -> None:
    """Push snapshot to ORACLE. Fire alert if move is significant."""

    # Always push snapshot
    try:
        await client.post(
            "/oracle/snapshot",
            params={
                "symbol": symbol,
                "price": price,
                "change_pct_24h": change_pct_24h,
                "source": source,
            },
        )
    except Exception as exc:
        logger.debug("MARKETPULSE snapshot push failed for %s: %s", symbol, exc)
        return

    # Compute intra-cycle move (vs last known price) for fine-grained alerting
    prev = _prev_prices.get(symbol)
    _prev_prices[symbol] = price

    if prev is not None and prev > 0:
        intra_move_pct = (price - prev) / prev * 100
        abs_move = abs(intra_move_pct)

        if abs_move >= 1.0:
            context = (
                f"{symbol} moved {intra_move_pct:+.2f}% in the last {POLL_INTERVAL}s "
                f"(24h: {change_pct_24h:+.2f}%). Current: {price:,.2f}"
            )
            try:
                await client.post(
                    "/oracle/alert",
                    params={
                        "symbol": symbol,
                        "move_pct": intra_move_pct,
                        "context": context,
                        "language": "en",
                    },
                )
            except Exception as exc:
                logger.debug("MARKETPULSE alert push failed for %s: %s", symbol, exc)
