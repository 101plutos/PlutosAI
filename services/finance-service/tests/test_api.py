"""Integration tests for Finance Division API endpoints."""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealth:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "finance-division"

    def test_health_includes_ruleset(self, client):
        response = client.get("/health")
        assert "ruleset_version" in response.json()


class TestFinanceStatusDashboard:
    def test_finance_status_returns_200(self, client):
        response = client.get("/finance/status")
        assert response.status_code == 200
        data = response.json()
        assert "QUANT" in data
        assert "COMPLIANCE" in data
        assert "ORACLE" in data

    def test_quant_section_has_required_fields(self, client):
        data = client.get("/finance/status").json()
        quant = data["QUANT"]
        assert "active" in quant
        assert "pnl_today_eur" in quant
        assert "drawdown_level" in quant

    def test_compliance_section_has_required_fields(self, client):
        data = client.get("/finance/status").json()
        comp = data["COMPLIANCE"]
        assert "ruleset_version" in comp
        assert "blackout_active" in comp
        assert "audit_entries" in comp


class TestComplianceEndpoints:
    def test_compliance_status_returns_200(self, client):
        response = client.get("/compliance/status")
        assert response.status_code == 200

    def test_compliance_audit_log_returns_list(self, client):
        response = client.get("/compliance/audit")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestQuantEndpoints:
    def test_quant_status_returns_200(self, client):
        response = client.get("/quant/status")
        assert response.status_code == 200
        data = response.json()
        assert "trading_active" in data
        assert "drawdown_state" in data

    def test_quant_evaluate_missing_fields_returns_422(self, client):
        response = client.post("/quant/evaluate", json={"symbol": "BTC"})
        assert response.status_code == 422


class TestOracleEndpoints:
    def test_oracle_snapshots_empty(self, client):
        response = client.get("/oracle/snapshots")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_oracle_alerts_returns_list(self, client):
        response = client.get("/oracle/alerts")
        assert response.status_code == 200

    def test_oracle_status_returns_200(self, client):
        response = client.get("/oracle/status")
        assert response.status_code == 200
        data = response.json()
        assert "monitored_symbols" in data
        assert "healthy" in data

    def test_oracle_snapshot_update(self, client):
        response = client.post(
            "/oracle/snapshot",
            params={"symbol": "DAX", "price": 18500.0, "change_pct_24h": -0.5, "source": "test"},
        )
        assert response.status_code == 200
        assert response.json()["updated"] is True

        # Should now appear in snapshots
        snaps = client.get("/oracle/snapshots").json()
        dax = next((s for s in snaps if s["symbol"] == "DAX"), None)
        assert dax is not None
        assert dax["price"] == 18500.0


class TestLedgerEndpoints:
    def test_ledger_net_worth_empty_history(self, client):
        response = client.get("/ledger/net-worth")
        assert response.status_code == 200

    def test_ledger_net_worth_post(self, client):
        response = client.post(
            "/ledger/net-worth",
            params={"liquid_eur": 5000.0, "illiquid_eur": 2000.0, "crypto_eur": 1000.0},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_eur"] == pytest.approx(8000.0)

    def test_ledger_reconcile_clean(self, client):
        response = client.post("/ledger/reconcile", json={
            "date": "2026-03-20",
            "internal_positions": {"BTC": "0.5"},
            "exchange_positions": {"BTC": "0.5"},
        })
        assert response.status_code == 200
        data = response.json()
        assert data["all_matched"] is True
        assert data["alert_triggered"] is False

    def test_ledger_reconcile_discrepancy(self, client):
        response = client.post("/ledger/reconcile", json={
            "date": "2026-03-20",
            "internal_positions": {"BTC": "0.5"},
            "exchange_positions": {"BTC": "0.6"},
        })
        assert response.status_code == 200
        data = response.json()
        assert data["all_matched"] is False
        assert data["alert_triggered"] is True

    def test_ledger_tax_report_returns_200(self, client):
        response = client.get("/ledger/tax-report", params={"period": "2026-Q1"})
        assert response.status_code == 200
