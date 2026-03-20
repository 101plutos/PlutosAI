import os
import time

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from shared.auth import verify_jwt  # Assuming shared auth module

app = FastAPI(title="PlutosAI Gateway Service")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Service URLs — injected via environment in docker-compose
_SERVICE_URLS = {
    "client":     os.getenv("CLIENT_SERVICE_URL", "http://localhost:8001"),
    "investment": os.getenv("INVESTMENT_SERVICE_URL", "http://localhost:8002"),
    "compliance": os.getenv("COMPLIANCE_SERVICE_URL", "http://localhost:8003"),
    "reporting":  os.getenv("REPORTING_SERVICE_URL", "http://localhost:8004"),
    "ai":         os.getenv("AI_SERVICE_URL", "http://localhost:8005"),
    "blockchain": os.getenv("BLOCKCHAIN_SERVICE_URL", "http://localhost:8006"),
    "simulation": os.getenv("SIMULATION_SERVICE_URL", "http://localhost:8007"),
}


# Profiling middleware
@app.middleware("http")
async def profile_request(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"Request to {request.url.path} took {process_time:.2f} seconds")
    return response


@app.get("/health")
@limiter.limit("5/minute")
def health(request: Request):
    return {"status": "healthy"}


async def _proxy(request: Request, service: str, path: str) -> Response:
    """Generic reverse proxy — forwards request to a downstream service."""
    base = _SERVICE_URLS.get(service)
    if not base:
        raise HTTPException(status_code=502, detail=f"Unknown service: {service}")

    url = f"{base}{path}"
    body = await request.body()
    headers = dict(request.headers)
    headers.pop("host", None)

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                params=dict(request.query_params),
            )
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail=f"Service '{service}' unreachable")

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers),
        media_type=resp.headers.get("content-type"),
    )


# ---------------------------------------------------------------------------
# Simulation Service routes — /simulate/* → simulation-service:8007
# ---------------------------------------------------------------------------
@app.api_route("/simulate", methods=["GET", "POST"])
@app.api_route("/simulate/{path:path}", methods=["GET", "POST", "DELETE"])
async def simulation_proxy(request: Request, path: str = "") -> Response:
    """Proxy all /simulate/* requests to the Simulation Service."""
    route_path = f"/simulate/{path}" if path else "/simulate"
    return await _proxy(request, "simulation", route_path)