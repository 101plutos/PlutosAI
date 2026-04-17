# PlutosAI × OpenClaw Integration

> OpenClaw is the interface layer for Project Francesca. Talk to your Finance Division
> through any messaging app — Telegram, WhatsApp, Signal, Discord — via OpenClaw's
> multi-channel gateway.

## Architecture

```
Your phone (Telegram / WhatsApp / Signal / Discord)
          ↕
    OpenClaw Gateway  (ws://127.0.0.1:18789)
          ↕
    PlutosAI Skills   (this directory)
          ↕
  Finance Service API  (http://plutos:8008)
          ├── COMPLIANCE agent
          ├── QUANT agent
          ├── ORACLE agent
          ├── BANKER agent
          ├── LEDGER agent
          └── 3 on-demand skills
```

**OpenClaw handles:** Messaging, routing, session management, cron scheduling,
human approval gates (Lobster), delivery to your preferred channel.

**PlutosAI handles:** Trading logic, COMPLIANCE gate, market intelligence, tax,
BBBank advisory, and all financial computation.

---

## Skills

| Skill | Trigger keywords | What it does |
|-------|-----------------|-------------|
| **finance** | `finance status`, `net worth`, `drawdown` | Full Finance Division dashboard |
| **oracle** | `morning brief`, `market alerts`, `DAX`, `weekly` | Market briefings + P0 alerts |
| **banker** | `bbbank`, `VL ETF`, `mifid`, `praxisnachweis` | BBBank products + MiFID II |
| **ledger** | `tax report`, `sparerpauschbetrag`, `haltefrist` | German tax + reconciliation |
| **equity-research** | `equity research AAPL`, `SAP.DE report` | 8-section institutional report |
| **prediction-coach** | `grade trade`, `kelly check`, `trade review` | A-F grade + bias detection |

## Scheduled Workflows

| Workflow | Schedule | What it does |
|----------|----------|-------------|
| `oracle-morning-brief` | Mon–Fri 06:30 CET | Morning market briefing |
| `oracle-weekly-german` | Monday 06:00 CET | Weekly German BBBank-format briefing |
| `ledger-nightly-reconcile` | Daily 23:00 CET | Positions reconciliation + QUANT equity sync |
| `finance-daily-digest` | Mon–Fri 08:00 CET | Finance Division status dashboard |

## Push Notifications (finance-service → OpenClaw)

The finance-service pushes directly to OpenClaw for time-sensitive events:

| Event | Trigger | Severity |
|-------|---------|----------|
| P0 market alert | Index move ≥ 2% | 🚨 Immediate |
| P1 market alert | Index move ≥ 1% | ⚠️ High |
| Drawdown WARNING | Drawdown 10–20% | 🟡 Warning |
| Drawdown HALT_24H | Drawdown 20–30% | 🔴 Critical |
| Drawdown HALT_72H | Drawdown > 30% | 🆘 Emergency |
| COMPLIANCE BLOCK | High-risk trade | 🚫 Informational |

Configure the push connection:
```bash
# In your .env or docker-compose environment:
OPENCLAW_GATEWAY_URL=ws://127.0.0.1:18789
OPENCLAW_DEFAULT_SESSION=main
```

---

## Setup

### 1. Install OpenClaw

```bash
npm install -g openclaw
openclaw onboard
```

### 2. Register PlutosAI skills

Add to your OpenClaw `config.yml`:
```bash
cp openclaw/config.template.yml ~/.openclaw/config.yml.plutosai
# Then merge sections into your existing config.yml
```

Or use the OpenClaw CLI:
```bash
openclaw skills add workspace ~/PlutosAI/openclaw/skills/finance
openclaw skills add workspace ~/PlutosAI/openclaw/skills/oracle
openclaw skills add workspace ~/PlutosAI/openclaw/skills/banker
openclaw skills add workspace ~/PlutosAI/openclaw/skills/ledger
openclaw skills add workspace ~/PlutosAI/openclaw/skills/equity-research
openclaw skills add workspace ~/PlutosAI/openclaw/skills/prediction-coach
```

### 3. Configure the finance-service URL

```bash
export PLUTOSAI_FINANCE_URL=http://localhost:8008
# Or in docker-compose: http://finance-service:8008
```

### 4. Start the Lobster workflows

```bash
# Register workflows with OpenClaw scheduler
lobster register openclaw/workflows/oracle-morning-brief.yml
lobster register openclaw/workflows/ledger-nightly-reconcile.yml
```

### 5. Enable push notifications

```bash
# finance-service needs to know where OpenClaw gateway is:
export FIN_OPENCLAW_GATEWAY_URL=ws://127.0.0.1:18789
export FIN_OPENCLAW_DEFAULT_SESSION=main
```

---

## Usage Examples

### Via Telegram / WhatsApp / any channel

```
You: finance status
Bot: 📊 FINANCE DIVISION STATUS
     QUANT 🟢
       PnL today:   📈 +€47.20
       Drawdown:    1.2% (NORMAL)
     COMPLIANCE ✅
       Blackout: clear
     ORACLE 🟢
       No active alerts
```

```
You: morning brief
Bot: 📰 ECB Hold Pressures European Equities as Fed Divergence Widens
     ...800-word FT-style briefing...
```

```
You: grade trade
     market: Will Fed cut rates in May 2026?
     position: Yes at 70¢ — strong inflation progress
     outcome: Won
     size: 4%
     edge: 0.70
     odds: 1.43
Bot: 🏆 Trade Grade: B (process score 7.5/10)
     Kelly: 🔴 over — recommended 2.1% of bankroll...
```

```
You: equity research NVDA
Bot: ⏳ Generating equity research for NVDA... (~5 min)
     ...
     📊 NVIDIA (NVDA)
     Verdict: 🟢 Buy | PT: $185
     ...
```

### Via Lobster (multi-step workflows)

```bash
# Evaluate a trade with COMPLIANCE gate + human approval
lobster run quant-trade-pipeline \
  SYMBOL=BTC-USD DIRECTION=long SIZE_EUR=300 \
  EDGE=0.58 ODDS=1.0 MARKET=binance \
  RATIONALE="Support at 82k held, momentum turning"
```

---

## Directory Structure

```
openclaw/
├── skills/
│   ├── finance/           # Finance Division dashboard + QUANT eval
│   ├── oracle/            # Market briefings + P0 alerts
│   ├── banker/            # BBBank products + MiFID II
│   ├── ledger/            # Tax report + net worth
│   ├── equity-research/   # 8-section institutional reports
│   └── prediction-coach/  # Trade grading + bias detection
├── workflows/
│   ├── quant-trade-pipeline.yml       # Full trade lifecycle
│   ├── oracle-morning-brief.yml       # Daily/weekly briefing delivery
│   └── ledger-nightly-reconcile.yml   # Nightly reconciliation + QUANT sync
├── config.template.yml    # Merge into ~/.openclaw/config.yml
└── README.md              # This file
```
