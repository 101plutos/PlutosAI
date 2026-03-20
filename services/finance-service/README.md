# Finance Division — Project Francesca

> The core value-delivery engine. Five specialised agents and three on-demand financial skills.
> Node: **plutos** — Port **8008**

---

## Agents

| Agent | Endpoint prefix | Role |
|-------|----------------|------|
| **COMPLIANCE** | `/compliance/*` | Hard gate before every trade. 30s timeout. Immutable audit log. |
| **QUANT** | `/quant/*` | Trade evaluation. Fractional Kelly. Drawdown protocol. |
| **ORACLE** | `/oracle/*` | Market intelligence. German briefings. P0 alerts. |
| **BANKER** | `/banker/*` | BBBank products. MiFID II suitability. Praxisnachweis role-play. |
| **LEDGER** | `/ledger/*` | Transaction categorisation. German tax events. Nightly reconciliation. |

## Skills (on-demand)

| Skill | Endpoint | Output |
|-------|----------|--------|
| **equity-research** | `POST /skills/equity-research` | 8-section institutional report |
| **prediction-market-coach** | `POST /skills/prediction-market-coach` | A–F trade grade, Kelly audit, bias detection |
| **financial-dispatch** | `POST /skills/financial-dispatch` | 800-word FT/Reuters-style briefing |

---

## Critical Rules (hard-coded, never overridden)

### COMPLIANCE Gate
Every QUANT trade must pass COMPLIANCE within **30 seconds** or trading halts.

Checks performed:
1. **Blackout window** — Friday 13:45–16:00 CET: absolute block
2. **Drawdown halt** — HALT_24H or HALT_72H: block all trades
3. **Position size limit** — configurable via `FIN_MAX_SINGLE_POSITION_EUR`
4. **Daily loss limit** — configurable via `FIN_MAX_DAILY_LOSS_EUR`
5. **Kelly criterion** — position size ≤ 33% fractional Kelly
6. **Drawdown warning** — WARNING state enforces 50% size reduction
7. **BaFin market eligibility** — only approved exchanges

### Drawdown Protocol

| Drawdown | Automatic action |
|----------|-----------------|
| 10–20% | WARNING: halve position sizes |
| 20–30% | HALT_24H: stop all trading 24h |
| >30% | HALT_72H: stop all trading 72h + AEGIS incident review |

### COMPLIANCE Dead-Man's Switch
If COMPLIANCE doesn't respond in `FIN_COMPLIANCE_TIMEOUT_SECONDS` (default 30s),
QUANT automatically enters HALT_24H mode. No degraded operation permitted.

---

## API Quick Reference

```
# Finance Division Dashboard
GET  /finance/status          → One-screen digest (QUANT PnL, COMPLIANCE health, ORACLE alerts)

# COMPLIANCE
POST /compliance/check        → Manual gate check on a trade proposal
GET  /compliance/status       → Ruleset version, blackout state, drawdown level
GET  /compliance/audit        → Immutable audit log (newest first)

# QUANT
POST /quant/evaluate          → Evaluate trade through COMPLIANCE (returns PASS/BLOCK)
GET  /quant/status            → Drawdown state, open positions, PnL today
POST /quant/outcome           → Record trade result (updates drawdown)
POST /quant/equity            → Update account equity (from LEDGER reconciliation)

# ORACLE
POST /oracle/briefing         → Generate market briefing (German BBBank / DISPATCH style)
POST /oracle/alert            → Evaluate price move → P0/P1/P2 alert
POST /oracle/snapshot         → Update market snapshot (from MARKETPULSE WebSocket)
GET  /oracle/snapshots        → Current price snapshots
GET  /oracle/alerts           → Active P0/P1 alerts

# BANKER
POST /banker/suitability      → MiFID II suitability assessment
POST /banker/product          → BBBank product query / advisory
POST /banker/scenario         → Praxisnachweis client scenario role-play

# LEDGER
POST /ledger/categorize       → Categorise transactions + German tax event flags
POST /ledger/reconcile        → Nightly reconciliation (internal vs exchange)
POST /ledger/net-worth        → Record net worth snapshot
GET  /ledger/net-worth        → Net worth history
GET  /ledger/tax-report       → German tax summary (Abgeltungssteuer, Haltefrist, etc.)

# Skills
POST /skills/equity-research           → 8-section institutional equity report
POST /skills/prediction-market-coach  → A–F trade grade + Kelly audit + bias detection
POST /skills/financial-dispatch        → FT/Reuters-style briefing article

# Ops
GET  /health                  → Health check
GET  /metrics                 → Prometheus metrics
```

---

## Running Locally

```bash
cd services/finance-service
pip install -e '.[dev]'

export FIN_OPENAI_API_KEY=your-key
# Point to Ollama for local inference:
# export FIN_OPENAI_BASE_URL=http://localhost:11434/v1

uvicorn src.api:app --reload --host 0.0.0.0 --port 8008
```

API docs: http://localhost:8008/docs

## Configuration (`FIN_` prefix)

| Variable | Default | Description |
|----------|---------|-------------|
| `FIN_OPENAI_API_KEY` | `your-api-key` | LLM API key |
| `FIN_OPENAI_BASE_URL` | OpenAI | Swap to Ollama/PGX |
| `FIN_DEFAULT_MODEL` | `gpt-4o` | Default LLM |
| `FIN_MAX_SINGLE_POSITION_EUR` | `5000` | COMPLIANCE position limit |
| `FIN_MAX_DAILY_LOSS_EUR` | `500` | COMPLIANCE daily loss limit |
| `FIN_COMPLIANCE_TIMEOUT_SECONDS` | `30` | Dead-man's switch timeout |
| `FIN_MAX_KELLY_FRACTION` | `0.33` | Maximum fractional Kelly |

## Tests

```bash
pytest tests/ -v
```
