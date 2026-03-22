"""Tests for OpenClaw WebSocket push client."""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.openclaw_client import OpenClawClient, push_p0_alert, push_compliance_block, push_drawdown_alert


class TestOpenClawClientDisabled:
    """When gateway URL is empty, all pushes silently no-op."""

    @pytest.mark.asyncio
    async def test_push_returns_false_when_no_url(self):
        client = OpenClawClient()
        with patch.object(type(client), "openai_api_key", create=True), \
             patch("src.openclaw_client.settings") as mock_settings:
            mock_settings.openclaw_gateway_url = ""
            mock_settings.openclaw_default_session = "main"
            result = await client.push("test message")
        assert result is False

    @pytest.mark.asyncio
    async def test_push_returns_false_when_websockets_unavailable(self):
        client = OpenClawClient()
        with patch("src.openclaw_client._WS_AVAILABLE", False), \
             patch("src.openclaw_client.settings") as mock_settings:
            mock_settings.openclaw_gateway_url = "ws://127.0.0.1:18789"
            mock_settings.openclaw_default_session = "main"
            result = await client.push("test message")
        assert result is False

    @pytest.mark.asyncio
    async def test_push_non_fatal_on_connection_error(self):
        """Connection failures should never raise — Finance Division must not stop."""
        from src import openclaw_client as oc_module

        client = OpenClawClient()
        with patch("src.openclaw_client._WS_AVAILABLE", True), \
             patch("src.openclaw_client.settings") as mock_settings:
            mock_settings.openclaw_gateway_url = "ws://127.0.0.1:18789"
            mock_settings.openclaw_default_session = "main"

            # websockets.connect raises connection refused
            with patch("websockets.connect", side_effect=ConnectionRefusedError("refused")):
                result = await client.push("test message")

        assert result is False  # Non-fatal — returns False, no exception


class TestOpenClawClientSuccess:
    """When gateway responds successfully."""

    @pytest.mark.asyncio
    async def test_push_returns_true_on_success(self):
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock(return_value=json.dumps({"id": "x", "result": "ok"}))
        mock_ws_cm = MagicMock()
        mock_ws_cm.__aenter__ = AsyncMock(return_value=mock_ws)
        mock_ws_cm.__aexit__ = AsyncMock(return_value=None)

        client = OpenClawClient()
        with patch("src.openclaw_client._WS_AVAILABLE", True), \
             patch("src.openclaw_client.settings") as mock_settings, \
             patch("websockets.connect", return_value=mock_ws_cm):
            mock_settings.openclaw_gateway_url = "ws://127.0.0.1:18789"
            mock_settings.openclaw_default_session = "main"
            result = await client.push("Hello from ORACLE")

        assert result is True
        mock_ws.send.assert_called_once()
        sent_payload = json.loads(mock_ws.send.call_args[0][0])
        assert sent_payload["method"] == "sessions.send"
        assert sent_payload["params"]["message"] == "Hello from ORACLE"
        assert sent_payload["params"]["sessionId"] == "main"

    @pytest.mark.asyncio
    async def test_push_uses_custom_session(self):
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock(return_value=json.dumps({"id": "x", "result": "ok"}))
        mock_ws_cm = MagicMock()
        mock_ws_cm.__aenter__ = AsyncMock(return_value=mock_ws)
        mock_ws_cm.__aexit__ = AsyncMock(return_value=None)

        client = OpenClawClient()
        with patch("src.openclaw_client._WS_AVAILABLE", True), \
             patch("src.openclaw_client.settings") as mock_settings, \
             patch("websockets.connect", return_value=mock_ws_cm):
            mock_settings.openclaw_gateway_url = "ws://127.0.0.1:18789"
            mock_settings.openclaw_default_session = "main"
            await client.push("msg", session="alerts")

        sent = json.loads(mock_ws.send.call_args[0][0])
        assert sent["params"]["sessionId"] == "alerts"

    @pytest.mark.asyncio
    async def test_push_returns_false_on_gateway_error_response(self):
        mock_ws = AsyncMock()
        mock_ws.send = AsyncMock()
        mock_ws.recv = AsyncMock(return_value=json.dumps({
            "id": "x",
            "error": {"code": -32601, "message": "session not found"},
        }))
        mock_ws_cm = MagicMock()
        mock_ws_cm.__aenter__ = AsyncMock(return_value=mock_ws)
        mock_ws_cm.__aexit__ = AsyncMock(return_value=None)

        client = OpenClawClient()
        with patch("src.openclaw_client._WS_AVAILABLE", True), \
             patch("src.openclaw_client.settings") as mock_settings, \
             patch("websockets.connect", return_value=mock_ws_cm):
            mock_settings.openclaw_gateway_url = "ws://127.0.0.1:18789"
            mock_settings.openclaw_default_session = "main"
            result = await client.push("test")

        assert result is False


class TestPushAlertFormatting:
    """Test that push_alert includes correct severity emoji and structure."""

    @pytest.mark.asyncio
    async def test_p0_alert_includes_action_required(self):
        captured = []

        async def mock_push(self, message, session=None):
            captured.append(message)
            return True

        client = OpenClawClient()
        with patch.object(OpenClawClient, "push", mock_push):
            await client.push_alert("P0", "DAX -2.5%", "DAX fell on ECB news", action_required=True)

        assert len(captured) == 1
        msg = captured[0]
        assert "🚨" in msg
        assert "P0" in msg
        assert "DAX -2.5%" in msg
        assert "Action required" in msg

    @pytest.mark.asyncio
    async def test_p1_alert_no_action_required(self):
        captured = []

        async def mock_push(self, message, session=None):
            captured.append(message)
            return True

        client = OpenClawClient()
        with patch.object(OpenClawClient, "push", mock_push):
            await client.push_alert("P1", "SPX -1.1%", "Minor move", action_required=False)

        msg = captured[0]
        assert "⚠️" in msg
        assert "Action required" not in msg


class TestConvenienceFunctions:
    """Test module-level convenience wrappers."""

    @pytest.mark.asyncio
    async def test_push_p0_alert_formats_direction(self):
        from src import openclaw_client

        captured = []
        original = openclaw_client.get_client()

        async def mock_push_alert(severity, title, body, action_required=False):
            captured.append({"severity": severity, "title": title, "action_required": action_required})
            return True

        with patch.object(original, "push_alert", mock_push_alert):
            await push_p0_alert("BTC-USD", -3.1, "BTC dumped on exchange news")

        assert captured[0]["severity"] == "P0"
        assert "▼" in captured[0]["title"]  # Negative move → downward arrow
        assert captured[0]["action_required"] is True

    @pytest.mark.asyncio
    async def test_push_p0_alert_positive_move(self):
        from src import openclaw_client

        captured = []
        original = openclaw_client.get_client()

        async def mock_push_alert(severity, title, body, action_required=False):
            captured.append({"title": title})
            return True

        with patch.object(original, "push_alert", mock_push_alert):
            await push_p0_alert("ETH-USD", 2.8, "ETH surged after upgrade")

        assert "▲" in captured[0]["title"]  # Positive move → upward arrow

    @pytest.mark.asyncio
    async def test_push_compliance_block_formats_violations(self):
        from src import openclaw_client

        captured = []
        original = openclaw_client.get_client()

        async def mock_push_alert(severity, title, body, action_required=False):
            captured.append({"severity": severity, "body": body})
            return True

        violations = [
            "BLACKOUT ACTIVE: Friday 13:45-16:00 CET",
            "KELLY VIOLATION: 0.50 > 0.33",
        ]
        with patch.object(original, "push_alert", mock_push_alert):
            await push_compliance_block("BTC-USD", violations)

        assert captured[0]["severity"] == "BLOCK"
        assert "BLACKOUT" in captured[0]["body"]

    @pytest.mark.asyncio
    async def test_push_drawdown_alert_halt_24h(self):
        from src import openclaw_client

        captured = []
        original = openclaw_client.get_client()

        async def mock_push_alert(severity, title, body, action_required=False):
            captured.append({"body": body, "action_required": action_required})
            return True

        with patch.object(original, "push_alert", mock_push_alert):
            await push_drawdown_alert("halt_24h", 22.5)

        assert "HALT 24H" in captured[0]["body"]
        assert captured[0]["action_required"] is True

    @pytest.mark.asyncio
    async def test_push_drawdown_alert_normal_no_action(self):
        """NORMAL level should not trigger a push at all (called with guard in quant.py)."""
        # This tests that only non-NORMAL levels call push_drawdown_alert
        # (the guard is in quant.py, not here, so we just verify the message format)
        from src import openclaw_client

        captured = []
        original = openclaw_client.get_client()

        async def mock_push_alert(severity, title, body, action_required=False):
            captured.append({"action_required": action_required})
            return True

        with patch.object(original, "push_alert", mock_push_alert):
            await push_drawdown_alert("warning", 12.0)

        assert captured[0]["action_required"] is False  # Warning = no action required


class TestMarketpulseUnit:
    """Unit tests for MARKETPULSE helper functions."""

    def test_coingecko_ids_map_to_oracle_symbols(self):
        from src.marketpulse import CRYPTO_IDS
        assert "bitcoin" in CRYPTO_IDS
        assert CRYPTO_IDS["bitcoin"] == "BTC-USD"
        assert "ethereum" in CRYPTO_IDS

    def test_yahoo_symbols_cover_dax_and_sp500(self):
        from src.marketpulse import YAHOO_SYMBOLS
        # Must cover DAX and S&P 500 at minimum
        assert "^GDAXI" in YAHOO_SYMBOLS
        assert "^GSPC" in YAHOO_SYMBOLS
        assert YAHOO_SYMBOLS["^GDAXI"] == "DAX"

    @pytest.mark.asyncio
    async def test_update_oracle_skips_alert_below_threshold(self):
        """Moves < 1% should not fire an alert."""
        from src import marketpulse

        # Seed a previous price
        marketpulse._prev_prices["TEST"] = 100.0

        snapshot_calls = []
        alert_calls = []

        async def mock_post(path, **kwargs):
            if "snapshot" in path:
                snapshot_calls.append(path)
            elif "alert" in path:
                alert_calls.append(path)
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            return resp

        mock_client = AsyncMock()
        mock_client.post = mock_post

        # 0.5% move — below threshold
        await marketpulse._update_oracle(mock_client, "TEST", 100.5, 0.5, "test")

        assert len(snapshot_calls) == 1
        assert len(alert_calls) == 0

    @pytest.mark.asyncio
    async def test_update_oracle_fires_alert_above_threshold(self):
        """Moves ≥ 1% should fire an alert."""
        from src import marketpulse

        marketpulse._prev_prices["TEST2"] = 100.0

        alert_calls = []

        async def mock_post(path, **kwargs):
            if "alert" in path:
                alert_calls.append(path)
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            return resp

        mock_client = AsyncMock()
        mock_client.post = mock_post

        # 2% move — above threshold
        await marketpulse._update_oracle(mock_client, "TEST2", 102.0, 2.0, "test")

        assert len(alert_calls) == 1
