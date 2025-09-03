"""Client Service API using FastAPI."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from shared.auth import User, jwt_manager, init_jwt_manager
from shared.domain.client import Client, ClientType, ClientStatus, Address, Contact
from shared.events import ClientCreated, ClientStatusChanged


# Configuration
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/plutosai"
JWT_SECRET_KEY = "your-secret-key-here"  # In production, use environment variable

# Initialize JWT manager
init_jwt_manager(JWT_SECRET_KEY)

# Database setup
engine = create_async_engine(DATABASE_URL, echo=True, pool_size=20, max_overflow=20)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        # Create tables if they don't exist
        pass

    # Start NATS subscription
    from shared.utils.nats_utils import connect_to_nats, subscribe_with_decompression
    nc = await connect_to_nats()
    async def handle_transaction_event(msg):
        # Process the decompressed message
        data = msg.data  # Already decompressed in subscribe_with_decompression
        app.logger.info(f"Received transaction event: {data}")
        # Add business logic here, e.g., update client status or notify

    await subscribe_with_decompression(nc, "blockchain.events.*", handle_transaction_event)

    yield

    # Shutdown
    await nc.close()
    await engine.dispose()

app = FastAPI(
    title="PlutosAI Client Service",
    version="0.1.0",
    lifespan=lifespan
)

from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()


# Pydantic models for API
class ClientCreateRequest(BaseModel):
    type: ClientType
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class ClientUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[ClientStatus] = None


class ClientResponse(BaseModel):
    id: str
    type: ClientType
    status: ClientStatus
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    created_at: str
    updated_at: str


# Dependencies
async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Extract and validate current user from JWT token."""
    try:
        return jwt_manager.decode_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


def require_permission(permission: str):
    """Dependency to check user permissions."""
    def dependency(user: User = Depends(get_current_user)):
        # In a real implementation, you'd check user.permissions
        # For now, just check if user exists
        return user
    return dependency


# Routes
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "client-service"}


@app.post("/clients", response_model=ClientResponse)
async def create_client(
    request: ClientCreateRequest,
    user: User = Depends(require_permission("create:client")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new client."""
    try:
        # Create domain entity
        contact = Contact(email=request.email, phone=request.phone)
        client = Client(
            type=request.type,
            first_name=request.first_name,
            last_name=request.last_name,
            contact=contact,
            created_by=user.user_id
        )

        # Save to database (would implement repository pattern here)
        # For now, just simulate

        # Publish domain events
        event = ClientCreated(
            aggregate_id=client.id,
            first_name=client.first_name or "",
            last_name=client.last_name or "",
            client_type=client.type.value
        )
        # Publish event to message queue (would implement event publisher here)

        # Return response
        return ClientResponse(
            id=client.id,
            type=client.type,
            status=client.status,
            first_name=client.first_name,
            last_name=client.last_name,
            email=client.contact.email,
            phone=client.contact.phone,
            created_at=client.created_at.isoformat(),
            updated_at=client.updated_at.isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create client: {str(e)}")


@app.get("/clients", response_model=List[ClientResponse])
async def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[ClientStatus] = None,
    user: User = Depends(require_permission("read:client")),
    db: AsyncSession = Depends(get_db)
):
    """List clients with pagination and filtering."""
    try:
        # In a real implementation, this would query the database
        # For now, return empty list
        return []

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list clients: {str(e)}")


@app.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: str,
    user: User = Depends(require_permission("read:client")),
    db: AsyncSession = Depends(get_db)
):
    """Get client by ID."""
    try:
        # In a real implementation, this would query the database
        # For now, raise not found
        raise HTTPException(status_code=404, detail="Client not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get client: {str(e)}")


@app.patch("/clients/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    request: ClientUpdateRequest,
    user: User = Depends(require_permission("update:client")),
    db: AsyncSession = Depends(get_db)
):
    """Update client."""
    try:
        # In a real implementation, this would load, update, and save the client
        # For now, raise not found
        raise HTTPException(status_code=404, detail="Client not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update client: {str(e)}")


@app.delete("/clients/{client_id}")
async def delete_client(
    client_id: str,
    user: User = Depends(require_permission("delete:client")),
    db: AsyncSession = Depends(get_db)
):
    """Delete client."""
    try:
        # In a real implementation, this would delete the client
        # For now, raise not found
        raise HTTPException(status_code=404, detail="Client not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete client: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
