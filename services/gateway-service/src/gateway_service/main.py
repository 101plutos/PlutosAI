from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time

from shared.auth import verify_jwt  # Assuming shared auth module

app = FastAPI(title="PlutosAI Gateway Service")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Profiling middleware
@app.middleware("http")
async def profile_request(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"Request to {request.url.path} took {process_time:.2f} seconds")
    return response

# Example route with rate limiting
@app.get("/health")
@limiter.limit("5/minute")
def health(request: Request):
    return {"status": "healthy"}

# TODO: Add routes proxying to other services with auth verification