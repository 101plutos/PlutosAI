"""Tests for QUANT agent — Kelly sizing, drawdown protocol, compliance pipeline."""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from src.agents import quant as quant_agent
from src.models import (
    ComplianceVerdict,
    DrawdownLevel,
    QuantTradeRequest,
)


def _make_request(**kwargs) -> QuantTradeRequest:
    defaults = dict(
        symbol="BTC-USD",
        direction="long",
        size_eur=Decimal("200"),
        market="binance",
        rationale="Test signal",
        edge_estimate=0.55,
        odds=1.0,
    )
    defaults.update(kwargs)
    return QuantTradeRequest(**defaults)


class TestKellyComputation:
    def test_positive_edge_returns_positive_kelly(self):
        k = quant_agent._compute_kelly(edge=0.55, odds=1.0)
        assert k > 0

    def test_zero_edge_returns_zero(self):
        k = quant_agent._compute_kelly(edge=0.5, odds=1.0)
        # At 50% edge with even money, Kelly = 0
        assert k == 0.0

    def test_negative_edge_returns_zero(self):
        k = quant_agent._compute_kelly(edge=0.4, odds=1.0)
        assert k == 0.0

    def test_kelly_capped_at_max(self):
        # Very high edge should still be capped
        k = quant_agent._compute_kelly(edge=0.99, odds=10.0)
        from src.config import settings
        assert k <= settings.max_kelly_fraction

    def test_fractional_kelly_is_one_third_of_full(self):
        # p=0.6, b=1.0 → full Kelly = (1*0.6 - 0.4)/1 = 0.2
        # fractional = 0.2/3 ≈ 0.0667
        k = quant_agent._compute_kelly(edge=0.6, odds=1.0)
        expected = round(0.2 / 3, 4)
        assert abs(k - expected) < 0.001


class TestDrawdownProtocol:
    def test_record_small_loss_stays_normal(self):
        # Reset state via update_equity
        quant_agent.update_equity(Decimal("10000"))
        quant_agent.record_trade_outcome("x", Decimal("-50"))  # 0.5% loss
        assert quant_agent._state.level == DrawdownLevel.NORMAL

    def test_record_large_loss_triggers_warning(self):
        quant_agent.update_equity(Decimal("10000"))
        quant_agent._state.peak_equity_eur = Decimal("10000")
        quant_agent.record_trade_outcome("x", Decimal("-1100"))  # 11% loss → WARNING
        assert quant_agent._state.level == DrawdownLevel.WARNING

    def test_record_25pct_loss_triggers_halt_24h(self):
        quant_agent.update_equity(Decimal("10000"))
        quant_agent._state.peak_equity_eur = Decimal("10000")
        quant_agent.record_trade_outcome("x", Decimal("-2500"))  # 25% → HALT_24H
        assert quant_agent._state.level == DrawdownLevel.HALT_24H
        assert quant_agent._state.halt_until is not None

    def test_record_35pct_loss_triggers_halt_72h(self):
        quant_agent.update_equity(Decimal("10000"))
        quant_agent._state.peak_equity_eur = Decimal("10000")
        quant_agent.record_trade_outcome("x", Decimal("-3500"))  # 35% → HALT_72H
        assert quant_agent._state.level == DrawdownLevel.HALT_72H


class TestEvaluateTrade:
    @pytest.mark.asyncio
    async def test_compliance_pass_returns_pass_verdict(self):
        from src.models import ComplianceResult, ComplianceAuditEntry
        quant_agent.update_equity(Decimal("10000"))
        quant_agent._state.level = DrawdownLevel.NORMAL
        quant_agent._state.halt_until = None

        mock_result = ComplianceResult(
            verdict=ComplianceVerdict.PASS,
            violations=[],
            rationale="All rules passed.",
            audit_entry=ComplianceAuditEntry(
                entry_id="audit-001",
                proposal_id="p-001",
                verdict=ComplianceVerdict.PASS,
                ruleset_version="2026-03-20",
                rules_checked=["blackout_window"],
                violations=[],
                rationale="Passed",
            ),
        )
        with patch("src.agents.quant.compliance_agent.check_trade",
                   new=AsyncMock(return_value=mock_result)):
            response = await quant_agent.evaluate_trade(_make_request())

        assert response.compliance_verdict == ComplianceVerdict.PASS
        assert response.executed is False  # Never auto-executed

    @pytest.mark.asyncio
    async def test_compliance_timeout_halts_trading(self):
        import asyncio
        quant_agent.update_equity(Decimal("10000"))
        quant_agent._state.level = DrawdownLevel.NORMAL
        quant_agent._state.halt_until = None

        async def slow_check(*args, **kwargs):
            await asyncio.sleep(999)

        with patch("src.agents.quant.compliance_agent.check_trade", new=slow_check):
            with patch("src.agents.quant.settings") as mock_settings:
                mock_settings.compliance_timeout_seconds = 0.01
                mock_settings.max_kelly_fraction = 0.33
                mock_settings.drawdown_warning_pct = 10.0
                mock_settings.drawdown_halt_24h_pct = 20.0
                mock_settings.drawdown_halt_72h_pct = 30.0
                mock_settings.max_single_position_eur = 5000.0
                response = await quant_agent.evaluate_trade(_make_request())

        assert response.compliance_verdict == ComplianceVerdict.BLOCK
        assert "timeout" in response.message.lower()


class TestUpdateEquity:
    def test_equity_updates_peak(self):
        quant_agent.update_equity(Decimal("20000"))
        assert quant_agent._state.current_equity_eur == Decimal("20000")
        assert quant_agent._state.peak_equity_eur == Decimal("20000")

    def test_lower_equity_does_not_update_peak(self):
        quant_agent.update_equity(Decimal("20000"))
        quant_agent.update_equity(Decimal("15000"))
        assert quant_agent._state.peak_equity_eur == Decimal("20000")
        assert quant_agent._state.current_equity_eur == Decimal("15000")
