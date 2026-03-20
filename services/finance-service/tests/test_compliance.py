"""Tests for COMPLIANCE agent — the hard gate."""
from __future__ import annotations

import asyncio
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest

from src.agents import compliance as compliance_agent
from src.models import (
    ComplianceVerdict,
    DrawdownLevel,
    TradeProposal,
)


def _make_proposal(**kwargs) -> TradeProposal:
    defaults = dict(
        proposal_id="test-001",
        symbol="BTC-USD",
        direction="long",
        size_eur=Decimal("500"),
        account_equity_eur=Decimal("10000"),
        kelly_fraction=0.05,
        market="binance",
        rationale="Test trade",
    )
    defaults.update(kwargs)
    return TradeProposal(**defaults)


class TestBlackoutWindow:
    """Friday 13:45–16:00 CET must always block trades."""

    @pytest.mark.asyncio
    async def test_friday_blackout_blocks_trade(self):
        # Simulate Friday 14:30 CET
        friday_1430 = datetime(2026, 3, 20, 13, 30, tzinfo=None)  # 14:30 Berlin = 13:30 UTC
        with patch("src.agents.compliance.datetime") as mock_dt:
            from zoneinfo import ZoneInfo
            mock_dt.now.return_value = datetime(2026, 3, 20, 14, 30,
                                                 tzinfo=ZoneInfo("Europe/Berlin"))
            result = await compliance_agent.check_trade(
                _make_proposal(), DrawdownLevel.NORMAL
            )
        assert result.verdict == ComplianceVerdict.BLOCK
        assert any("BLACKOUT" in v for v in result.violations)

    @pytest.mark.asyncio
    async def test_monday_no_blackout(self):
        with patch("src.agents.compliance._is_blackout", return_value=False):
            result = await compliance_agent.check_trade(
                _make_proposal(), DrawdownLevel.NORMAL
            )
        assert result.verdict == ComplianceVerdict.PASS
        assert result.violations == []


class TestPositionLimits:
    @pytest.mark.asyncio
    async def test_oversized_position_blocked(self):
        with patch("src.agents.compliance._is_blackout", return_value=False):
            result = await compliance_agent.check_trade(
                _make_proposal(size_eur=Decimal("99999")),
                DrawdownLevel.NORMAL,
            )
        assert result.verdict == ComplianceVerdict.BLOCK
        assert any("POSITION SIZE" in v for v in result.violations)

    @pytest.mark.asyncio
    async def test_normal_size_passes(self):
        with patch("src.agents.compliance._is_blackout", return_value=False):
            result = await compliance_agent.check_trade(
                _make_proposal(size_eur=Decimal("100")),
                DrawdownLevel.NORMAL,
            )
        assert result.verdict == ComplianceVerdict.PASS


class TestKellyViolation:
    @pytest.mark.asyncio
    async def test_kelly_over_max_blocked(self):
        with patch("src.agents.compliance._is_blackout", return_value=False):
            result = await compliance_agent.check_trade(
                _make_proposal(kelly_fraction=0.99),  # Way over 0.33
                DrawdownLevel.NORMAL,
            )
        assert result.verdict == ComplianceVerdict.BLOCK
        assert any("KELLY" in v for v in result.violations)

    @pytest.mark.asyncio
    async def test_kelly_within_limit_passes(self):
        with patch("src.agents.compliance._is_blackout", return_value=False):
            result = await compliance_agent.check_trade(
                _make_proposal(kelly_fraction=0.10),
                DrawdownLevel.NORMAL,
            )
        assert result.verdict == ComplianceVerdict.PASS


class TestDrawdownHalt:
    @pytest.mark.asyncio
    async def test_halt_24h_blocks_all_trades(self):
        with patch("src.agents.compliance._is_blackout", return_value=False):
            result = await compliance_agent.check_trade(
                _make_proposal(), DrawdownLevel.HALT_24H
            )
        assert result.verdict == ComplianceVerdict.BLOCK
        assert any("DRAWDOWN HALT" in v for v in result.violations)

    @pytest.mark.asyncio
    async def test_halt_72h_blocks_all_trades(self):
        with patch("src.agents.compliance._is_blackout", return_value=False):
            result = await compliance_agent.check_trade(
                _make_proposal(), DrawdownLevel.HALT_72H
            )
        assert result.verdict == ComplianceVerdict.BLOCK


class TestAuditLog:
    def test_audit_log_grows_on_each_check(self):
        initial = len(compliance_agent.get_audit_log(limit=1000))

        async def run():
            with patch("src.agents.compliance._is_blackout", return_value=False):
                await compliance_agent.check_trade(_make_proposal(), DrawdownLevel.NORMAL)

        asyncio.run(run())
        after = len(compliance_agent.get_audit_log(limit=1000))
        assert after == initial + 1

    def test_audit_log_limit_respected(self):
        entries = compliance_agent.get_audit_log(limit=5)
        assert len(entries) <= 5


class TestIsBlackout:
    def test_friday_within_window(self):
        from zoneinfo import ZoneInfo
        # Friday at 14:00 CET — should be in blackout
        dt = datetime(2026, 3, 20, 14, 0, tzinfo=ZoneInfo("Europe/Berlin"))
        assert compliance_agent._is_blackout(dt) is True

    def test_friday_before_window(self):
        from zoneinfo import ZoneInfo
        # Friday at 13:00 CET — before blackout
        dt = datetime(2026, 3, 20, 13, 0, tzinfo=ZoneInfo("Europe/Berlin"))
        assert compliance_agent._is_blackout(dt) is False

    def test_friday_after_window(self):
        from zoneinfo import ZoneInfo
        # Friday at 16:30 CET — after blackout
        dt = datetime(2026, 3, 20, 16, 30, tzinfo=ZoneInfo("Europe/Berlin"))
        assert compliance_agent._is_blackout(dt) is False

    def test_thursday_no_blackout(self):
        from zoneinfo import ZoneInfo
        # Thursday at 15:00 CET — not Friday
        dt = datetime(2026, 3, 19, 15, 0, tzinfo=ZoneInfo("Europe/Berlin"))
        assert compliance_agent._is_blackout(dt) is False
