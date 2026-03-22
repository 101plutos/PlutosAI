# PlutosAI — AI-Native Family Office Platform

A production-ready, AI-native family office and asset management platform.
The interface layer is **OpenClaw** — Flo talks to the Finance Division through
any messaging app (Telegram, WhatsApp, Signal, Discord) via OpenClaw's
multi-channel gateway.

---

## Architecture

```
Your phone (Telegram / WhatsApp / Signal / Discord)
          ↕
  OpenClaw Gateway  ws://127.0.0.1:18789
          ↕
  PlutosAI Skills   openclaw/skills/
          ↕
  Finance Division  finance-service:8008
  ├── COMPLIANCE    Hard gate — 30s timeout, immutable audit log
  ├── QUANT         Fractional Kelly, drawdown protocol
  ├── ORACLE        DAX/BTC/EUR monitoring, P0 alerts, briefings
  ├── BANKER        BBBank products, MiFID II, Praxisnachweis
  └── LEDGER        German tax, reconciliation, net worth

  Supporting Services
  ├── simulation-service:8007   MiroFish prediction engine (4-agent debate)
  ├── ai-service:8005           OpenAI integration, quantized models
  ├── blockchain-service:8006   Wallets, DeFi, NFTs
  ├── client-service:8001       KYC/onboarding
  └── gateway-service:8000      REST reverse proxy
```

### Technology Stack

| Layer | Tech |
|-------|------|
| Language | Python 3.11+ |
| Framework | FastAPI (async) |
| Database | PostgreSQL |
| Cache | Redis |
| Message Queue | NATS |
| LLM Client | OpenAI-compatible (swap for Ollama/local) |
| Interface | OpenClaw (multi-channel messaging gateway) |
| Monitoring | Prometheus + Grafana |
| Container | Docker + Kubernetes |

---

## Finance Division — Project Francesca

The core value-delivery engine. Five specialised agents, three on-demand skills,
and a live market data feed (MARKETPULSE).

### Agents

| Agent | Endpoint prefix | Role |
|-------|----------------|------|
| **COMPLIANCE** | `/compliance/*` | Hard gate before every trade. 30s timeout. Blackout window. Immutable audit log. |
| **QUANT** | `/quant/*` | Trade evaluation. Fractional Kelly (1/3 of f*). Drawdown protocol. |
| **ORACLE** | `/oracle/*` | 24/7 market intelligence. P0 alerts ≤5 min. Weekly German briefings. |
| **BANKER** | `/banker/*` | BBBank products. MiFID II suitability. Praxisnachweis role-play. |
| **LEDGER** | `/ledger/*` | Transaction categorisation. German tax. Nightly reconciliation. |

### Hard Rules (non-negotiable, hard-coded)

```
Blackout:        Friday 13:45–16:00 CET — absolute block, zero exceptions
Drawdown 10–20%: WARNING — halve all position sizes
Drawdown 20–30%: HALT_24H — stop all trading for 24 hours
Drawdown >30%:   HALT_72H — stop 72 hours + AEGIS incident review
Dead-man switch: COMPLIANCE unresponsive > 30s → auto HALT_24H
Max Kelly:       33% fractional Kelly (1/3 of full Kelly)
Auto-execute:    NEVER — human approval mandatory before any real order
```

### On-Demand Skills

| Skill | Endpoint | |
|-------|----------|-|
| equity-research | `POST /skills/equity-research` | 8-section Goldman/JPMorgan-style report |
| prediction-market-coach | `POST /skills/prediction-market-coach` | A–F trade grade, Kelly audit, bias detection |
| financial-dispatch | `POST /skills/financial-dispatch` | 800-word FT/Reuters briefing |

### MARKETPULSE (Live Price Feed)

Background task inside finance-service. Polls CoinGecko (crypto) and Yahoo Finance
(equities/FX) every 60 seconds, pushes snapshots to ORACLE. Evaluates moves — fires
P0 alerts automatically when threshold breached.

---

## OpenClaw Integration

Talk to PlutosAI through any messaging app. Full details: [`openclaw/README.md`](openclaw/README.md).

### Skills

| Skill | Trigger keywords | What it does |
|-------|-----------------|-------------|
| `finance` | "finance status", "net worth", "drawdown" | Full Finance Division dashboard |
| `oracle` | "morning brief", "DAX", "p0 alert", "was läuft" | Market briefings + alerts |
| `banker` | "bbbank", "VL ETF", "mifid", "praxisnachweis" | BBBank products + MiFID II |
| `ledger` | "tax report", "sparerpauschbetrag", "haltefrist" | German tax + reconciliation |
| `equity-research` | "equity research AAPL", "SAP.DE report" | 8-section institutional report |
| `prediction-coach` | "grade trade", "kelly check", "trade review" | A–F grade + bias detection |
| `simulate` | "simulate BTC", "predict ETH next month" | MiroFish 4-agent prediction |

### Scheduled Workflows

| Workflow | Cron (UTC) | |
|----------|------------|-|
| `oracle-morning-brief` | `30 5 * * 1-5` | Mon–Fri 06:30 CET morning briefing |
| `ledger-nightly-reconcile` | `0 22 * * *` | Daily 23:00 CET reconciliation + QUANT sync |

### Push Notifications

ORACLE pushes P0 alerts within 5 minutes of a material move. QUANT pushes drawdown
level changes. Delivered directly to your Telegram/WhatsApp/Signal via OpenClaw.

```bash
FIN_OPENCLAW_GATEWAY_URL=ws://127.0.0.1:18789
FIN_OPENCLAW_DEFAULT_SESSION=main
```

---

## Quick Start

### Prerequisites

- Python 3.11+, Docker & Docker Compose
- Node.js 22+ (for OpenClaw)

### 1. Start infrastructure

```bash
cd infrastructure/docker
cp .env.example .env    # add OPENAI_API_KEY
docker-compose up -d
```

### 2. Install OpenClaw

```bash
npm install -g openclaw
openclaw onboard
# Merge openclaw/config.template.yml into ~/.openclaw/config.yml
```

### 3. Register PlutosAI skills

```bash
for skill in finance oracle banker ledger equity-research prediction-coach simulate; do
  openclaw skills add workspace ~/PlutosAI/openclaw/skills/$skill
done
```

### 4. Services

| Service | URL |
|---------|-----|
| API Gateway | http://localhost:8000 |
| Finance Division | http://localhost:8008/docs |
| Simulation Engine | http://localhost:8007/docs |
| Grafana | http://localhost:3000 (admin/admin) |
| Prometheus | http://localhost:9090 |

---

## Project Structure

```
PlutosAI/
├── openclaw/                    # OpenClaw interface layer
│   ├── skills/                  # One skill package per agent
│   │   ├── finance/             # Finance Division dashboard
│   │   ├── oracle/              # Market briefings + P0 alerts
│   │   ├── banker/              # BBBank advisory + MiFID II
│   │   ├── ledger/              # German tax + reconciliation
│   │   ├── equity-research/     # 8-section institutional reports
│   │   ├── prediction-coach/    # Trade grading + bias detection
│   │   └── simulate/            # MiroFish prediction engine
│   ├── workflows/               # Lobster multi-step workflows
│   │   ├── quant-trade-pipeline.yml    # QUANT→COMPLIANCE→approval
│   │   ├── oracle-morning-brief.yml    # Daily briefing delivery
│   │   └── ledger-nightly-reconcile.yml
│   └── config.template.yml      # Merge into ~/.openclaw/config.yml
├── services/
│   ├── finance-service/         # Project Francesca (port 8008)
│   │   ├── src/agents/          # 5 agents
│   │   ├── src/skills/          # 3 on-demand skills
│   │   ├── src/marketpulse.py   # MARKETPULSE live feed
│   │   └── src/openclaw_client.py  # WebSocket push to OpenClaw
│   ├── simulation-service/      # MiroFish (port 8007)
│   ├── ai-service/              # OpenAI integration (port 8005)
│   ├── blockchain-service/      # Wallets, DeFi, NFTs (port 8006)
│   ├── client-service/          # KYC/onboarding (port 8001)
│   └── gateway-service/         # REST proxy (port 8000)
├── shared/                      # Domain models, auth, events
├── infrastructure/              # Docker Compose, Kubernetes
├── templates/                   # Regulatory policies, SOPs
└── docs/                        # Architecture, compliance, security
```

---

## Key Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FIN_OPENAI_API_KEY` | — | LLM API key (also `SIM_`, `AI_` prefixes) |
| `FIN_OPENAI_BASE_URL` | OpenAI | `http://localhost:11434/v1` for Ollama |
| `FIN_DEFAULT_MODEL` | `gpt-4o` | Default model |
| `FIN_MAX_SINGLE_POSITION_EUR` | `5000` | COMPLIANCE position limit |
| `FIN_MAX_DAILY_LOSS_EUR` | `500` | COMPLIANCE daily loss limit |
| `FIN_OPENCLAW_GATEWAY_URL` | `""` | OpenClaw WebSocket (push disabled if empty) |
| `OPENCLAW_GATEWAY_URL` | `""` | For docker-compose passthrough |

---

## Roadmap

### Phase 1 ✅
- Finance Division (5 agents + 3 skills + MARKETPULSE)
- OpenClaw integration (7 skills + 3 workflows + WebSocket push)
- MiroFish simulation engine
- Blockchain/DeFi service

### Phase 2 (In Progress)
- Exchange API integration (Binance, Kraken)
- Polymarket/Kalshi prediction market connectivity
- BBBank Open Banking / PSD2 sync
- LEDGER automated ELSTER tax export

### Phase 3 (Planned)
- Multi-entity support (GbR, joint accounts)
- Black-Litterman portfolio optimisation
- BaFin regulatory reporting automation

---

**Built for Project Francesca.**
