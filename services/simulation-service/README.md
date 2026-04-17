# Simulation Service — Financial Prediction Engine

> MiroFish-inspired multi-agent financial prediction simulation, ported to OpenClaw for Project Francesca.

## What It Does

Upload seed materials (market reports, news, financial signals) and a prediction question.
The engine runs a structured debate between **4 financial agent personas** and synthesizes
a structured prediction report — in 5 stages mirroring the MiroFish pipeline:

| Stage | MiroFish Original | This Port |
|-------|-------------------|-----------|
| 1 | Knowledge Graph Construction | Entity extraction from seed text → KnowledgeGraph |
| 2 | Agent Environment Setup | Financial agent personas: Bull / Bear / Analyst / Macro |
| 3 | Parallel Simulation | N-round structured debate (async, concurrent per round) |
| 4 | Report Generation | ReportAgent synthesizes verdict + probabilities |
| 5 | Deep Interaction | POST /ask — query any agent or ReportAgent |

## Agents

| Agent | Persona | Analytical Lens |
|-------|---------|-----------------|
| **BULL** | Long-bias portfolio manager | Momentum, upside catalysts, trend continuation |
| **BEAR** | Macro hedge fund manager | Tail risks, credit stress, overvaluation, contrarian |
| **ANALYST** | Quantitative strategist | Data-driven, factor models, probabilistic, neutral |
| **MACRO** | Central bank economist | Rate cycles, fiscal dynamics, geopolitical flows |
| **REPORT** | Senior analyst synthesizer | Aggregates all views into structured prediction |

## API

```
POST   /simulate           → Start a simulation (async, returns 202 + simulation_id)
GET    /simulate/{id}      → Poll status / get results
GET    /simulate           → List recent simulations
POST   /simulate/{id}/ask  → Interactive Q&A against completed simulation
DELETE /simulate/{id}      → Clean up
GET    /health             → Service health check
GET    /metrics            → Prometheus metrics
```

## Example Request

```json
POST /simulate
{
  "seed_text": "ECB raised rates 25bps. DAX fell 1.2% on weak PMI...",
  "prediction_query": "Will the DAX correct more than 5% in the next 30 days?",
  "rounds": 3,
  "active_agents": ["bull", "bear", "analyst", "macro"],
  "model": "gpt-4o"
}
```

## Example Response (GET /simulate/{id} when COMPLETED)

```json
{
  "simulation_id": "...",
  "status": "completed",
  "report": {
    "executive_summary": "The four-agent debate reached a mildly bearish consensus...",
    "verdict": {
      "direction": "bearish",
      "confidence": 0.62,
      "timeframe": "30 days",
      "probability_up": 0.28,
      "probability_down": 0.52,
      "probability_sideways": 0.20,
      "key_catalysts": ["ECB hawkishness", "weak PMI data"],
      "key_risks": ["Earnings beat consensus", "USD weakness"]
    },
    "agent_consensus": {
      "bull": "Sees support at 18,200 and expects a bounce.",
      "bear": "Weak PMI + rate headwinds justify further downside.",
      "analyst": "Historical PMI correlation suggests -3.5% median return.",
      "macro": "ECB terminal rate repricing is the dominant factor."
    }
  }
}
```

## Running Locally

```bash
cd services/simulation-service
pip install -e '.[dev]'

# Set your LLM endpoint (or point to local Ollama):
export SIM_OPENAI_API_KEY=your-key
export SIM_OPENAI_BASE_URL=https://api.openai.com/v1

uvicorn src.api:app --reload --host 0.0.0.0 --port 8005
```

Open API docs: http://localhost:8005/docs

## Configuration (env vars with `SIM_` prefix)

| Variable | Default | Description |
|----------|---------|-------------|
| `SIM_OPENAI_API_KEY` | `your-api-key` | LLM API key |
| `SIM_OPENAI_BASE_URL` | OpenAI | Swap to Ollama/PGX base URL |
| `SIM_DEFAULT_MODEL` | `gpt-4o` | Default LLM model |
| `SIM_REDIS_HOST` | `localhost` | Redis host (graceful fallback if down) |
| `SIM_PORT` | `8005` | Service port |

## Running Tests

```bash
pytest tests/ -v
```

## Integration with Project Francesca

This service is designed to feed **ORACLE** and **QUANT** agents:

- **ORACLE** can call `POST /simulate` with weekly macro seed text to generate directional forecasts
- **QUANT** can use simulation verdicts as soft signals for position sizing (not hard trade signals — COMPLIANCE still gates every trade)
- **SCRIBE** archives simulation reports for fine-tuning the DISPATCH editorial voice

The OpenAI-compatible client (`SIM_OPENAI_BASE_URL`) means this service can transparently
route to local Ollama 7B for cheap runs, or cloud frontier models for high-stakes forecasts —
matching Project Francesca's hybrid inference routing strategy.
