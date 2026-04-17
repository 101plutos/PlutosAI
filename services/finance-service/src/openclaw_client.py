"""
OpenClaw Gateway WebSocket client — Project Francesca.

Allows Finance Division agents to PUSH messages directly to Flo's preferred
messaging channel (Telegram, WhatsApp, Signal, Discord) via the OpenClaw
gateway at ws://127.0.0.1:18789.

Used for:
  - ORACLE P0/P1 market alerts (within 5 minutes of a material move)
  - COMPLIANCE BLOCK notifications on high-risk trade attempts
  - Nightly LEDGER reconciliation summary
  - QUANT drawdown level changes (WARNING → HALT)

Protocol: JSON-RPC over WebSocket (OpenClaw gateway format).
Call `message.send` with `to` (channel address) and `message` (text).

If the OpenClaw gateway is unavailable, push falls back silently — it
never blocks the primary Finance Division operation.
"""
from __future__ import annotations

import json
import logging
import uuid
from contextlib import asynccontextmanager

try:
    import websockets
    _WS_AVAILABLE = True
except ImportError:
    _WS_AVAILABLE = False

from .config import settings

logger = logging.getLogger(__name__)


class OpenClawClient:
    """
    Thin async client for the OpenClaw WebSocket gateway.
    Sends one message per connection — stateless, non-blocking.
    """

    def __init__(self) -> None:
        self._gateway_url = settings.openclaw_gateway_url
        self._default_session = settings.openclaw_default_session

    async def push(self, message: str, session: str | None = None) -> bool:
        """
        Push a message to the OpenClaw gateway for delivery to the user.

        Args:
            message: Text to deliver (Markdown OK — OpenClaw normalises per channel).
            session: OpenClaw session ID (defaults to settings.openclaw_default_session).

        Returns:
            True if delivered, False if gateway is unavailable (non-fatal).
        """
        if not _WS_AVAILABLE:
            logger.debug("websockets library not installed — OpenClaw push skipped")
            return False

        if not self._gateway_url:
            logger.debug("OPENCLAW_GATEWAY_URL not configured — push skipped")
            return False

        target_session = session or self._default_session
        request_id = str(uuid.uuid4())

        rpc_call = {
            "id": request_id,
            "method": "sessions.send",
            "params": {
                "sessionId": target_session,
                "message": message,
            },
        }

        try:
            async with websockets.connect(
                self._gateway_url,
                open_timeout=5,
                close_timeout=5,
            ) as ws:
                await ws.send(json.dumps(rpc_call))
                raw = await ws.recv()
                response = json.loads(raw)

                if response.get("error"):
                    logger.warning(
                        "OpenClaw gateway error: %s", response["error"]
                    )
                    return False

                logger.debug("OpenClaw push delivered (id=%s)", request_id)
                return True

        except Exception as exc:
            # Non-fatal — Finance Division operations must not fail due to push issues
            logger.debug("OpenClaw push failed (non-fatal): %s", exc)
            return False

    async def push_alert(
        self,
        severity: str,
        title: str,
        body: str,
        action_required: bool = False,
    ) -> bool:
        """Format and push a structured alert."""
        emoji_map = {"P0": "🚨", "P1": "⚠️", "P2": "ℹ️", "BLOCK": "🚫", "HALT": "🔴"}
        emoji = emoji_map.get(severity, "📌")
        action_note = "\n⚡ *Action required.*" if action_required else ""

        formatted = (
            f"{emoji} *{severity}: {title}*\n\n"
            f"{body}"
            f"{action_note}"
        )
        return await self.push(formatted)


# Singleton — shared across all agents in the process
_client: OpenClawClient | None = None


def get_client() -> OpenClawClient:
    global _client
    if _client is None:
        _client = OpenClawClient()
    return _client


async def push_p0_alert(symbol: str, move_pct: float, narrative: str) -> None:
    """Convenience wrapper — push a P0 market alert."""
    direction = "▲" if move_pct >= 0 else "▼"
    await get_client().push_alert(
        severity="P0",
        title=f"{symbol} {direction} {abs(move_pct):.1f}%",
        body=narrative,
        action_required=True,
    )


async def push_compliance_block(symbol: str, violations: list[str]) -> None:
    """Push a COMPLIANCE BLOCK notification — always delivered."""
    summary = "\n".join(f"  • {v[:80]}" for v in violations[:3])
    await get_client().push_alert(
        severity="BLOCK",
        title=f"Trade blocked: {symbol}",
        body=f"COMPLIANCE violations:\n{summary}",
        action_required=False,
    )


async def push_drawdown_alert(level: str, drawdown_pct: float) -> None:
    """Push a drawdown level change notification."""
    level_emoji = {"warning": "🟡", "halt_24h": "🔴", "halt_72h": "🆘"}.get(level, "📌")
    messages = {
        "warning": f"Drawdown {drawdown_pct:.1f}% — WARNING. Position sizes halved.",
        "halt_24h": f"Drawdown {drawdown_pct:.1f}% — HALT 24H. All trading suspended.",
        "halt_72h": f"Drawdown {drawdown_pct:.1f}% — HALT 72H. AEGIS incident review required.",
    }
    await get_client().push_alert(
        severity="HALT",
        title=f"QUANT {level_emoji} {level.upper()}",
        body=messages.get(level, f"Drawdown level: {level}"),
        action_required=(level in ("halt_24h", "halt_72h")),
    )
