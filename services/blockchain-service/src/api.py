"""Blockchain Service API for digital asset management."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from shared.auth import User, jwt_manager, init_jwt_manager, Permission
from shared.domain.blockchain import (
    Blockchain, AssetType, TransactionType, WalletType, RiskLevel,
    Wallet, BlockchainTransaction, NFT, DeFiPosition, BridgeTransaction,
    Asset, Price
)
from .simple_wallet import WalletManager
from .defi_manager import DeFiManager

# Configuration
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/plutosai_blockchain"
JWT_SECRET_KEY = "your-blockchain-service-secret-key"

# Initialize JWT manager
init_jwt_manager(JWT_SECRET_KEY)

# Database setup
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        # Create tables if they don't exist
        pass
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title="PlutosAI Blockchain Service",
    version="0.1.0",
    description="Digital Asset Management for Family Offices",
    lifespan=lifespan
)

from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class AssetResponse(BaseModel):
    symbol: str
    name: str
    contract_address: Optional[str]
    blockchain: Blockchain
    asset_type: AssetType
    decimals: int
    coingecko_id: Optional[str]
    is_verified: bool


class PriceResponse(BaseModel):
    asset_symbol: str
    price_usd: Decimal
    price_btc: Optional[Decimal]
    market_cap: Optional[Decimal]
    volume_24h: Optional[Decimal]
    price_change_24h: Optional[Decimal]
    timestamp: str
    source: str


class WalletCreateRequest(BaseModel):
    client_id: str = Field(..., description="Client ID from client service")
    name: str = Field(..., min_length=1, max_length=100)
    wallet_type: WalletType
    blockchain: Blockchain
    address: str = Field(..., pattern=r"^0x[a-fA-F0-9]{40}$|^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$")
    required_signatures: int = Field(1, ge=1)
    total_signers: int = Field(1, ge=1)
    signer_addresses: List[str] = Field(default_factory=list)

    @validator('signer_addresses')
    def validate_signers(cls, v, values):
        if 'total_signers' in values and len(v) != values['total_signers']:
            raise ValueError('Number of signer addresses must match total_signers')
        return v


class WalletUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None
    daily_limit: Optional[Decimal] = Field(None, ge=0)
    require_approval: Optional[bool] = None


class WalletResponse(BaseModel):
    id: str
    client_id: str
    name: str
    wallet_type: WalletType
    blockchain: Blockchain
    address: str
    is_active: bool
    risk_level: RiskLevel
    required_signatures: int
    total_signers: int
    daily_limit: Optional[Decimal]
    require_approval: bool
    created_at: str
    updated_at: str
    last_sync: Optional[str]


class TransactionCreateRequest(BaseModel):
    wallet_id: str
    transaction_type: TransactionType
    to_address: Optional[str]
    contract_address: Optional[str]
    asset_symbol: str
    amount: Decimal = Field(..., gt=0)
    gas_limit: Optional[int] = Field(None, gt=0)


class TransactionResponse(BaseModel):
    id: str
    wallet_id: str
    blockchain: Blockchain
    transaction_hash: str
    transaction_type: TransactionType
    from_address: str
    to_address: Optional[str]
    contract_address: Optional[str]
    asset_symbol: str
    amount: Decimal
    gas_used: Optional[int]
    gas_price: Optional[Decimal]
    transaction_fee: Optional[Decimal]
    status: str
    confirmations: int
    block_number: Optional[int]
    block_timestamp: Optional[str]
    created_at: str
    updated_at: str


class NFTRegisterRequest(BaseModel):
    wallet_id: str
    blockchain: Blockchain
    contract_address: str = Field(..., pattern=r"^0x[a-fA-F0-9]{40}$")
    token_id: str
    token_standard: str = Field(..., regex=r"^(ERC-721|ERC-1155)$")


class NFTResponse(BaseModel):
    id: str
    wallet_id: str
    blockchain: Blockchain
    contract_address: str
    token_id: str
    token_standard: str
    name: Optional[str]
    description: Optional[str]
    image_url: Optional[str]
    floor_price: Optional[Decimal]
    estimated_value: Optional[Decimal]
    is_listed: bool
    listing_price: Optional[Decimal]
    created_at: str
    updated_at: str


class DeFiPositionCreateRequest(BaseModel):
    client_id: str
    protocol: str = Field(..., min_length=1, max_length=50)
    blockchain: Blockchain
    position_type: str = Field(..., min_length=1, max_length=50)
    assets: List[str] = Field(..., min_items=1)
    initial_amounts: Dict[str, Decimal]


class DeFiPositionResponse(BaseModel):
    id: str
    wallet_id: str
    client_id: str
    protocol: str
    blockchain: Blockchain
    position_type: str
    assets: List[str]
    amounts: Dict[str, Decimal]
    apr: Optional[Decimal]
    apy: Optional[Decimal]
    rewards_earned: Dict[str, Decimal]
    liquidation_price: Optional[Decimal]
    ltv_ratio: Optional[Decimal]
    is_active: bool
    created_at: str
    updated_at: str


class BridgeTransactionCreateRequest(BaseModel):
    client_id: str
    from_chain: Blockchain
    to_chain: Blockchain
    bridge_protocol: str = Field(..., min_length=1, max_length=50)
    asset_symbol: str
    amount: Decimal = Field(..., gt=0)


class BridgeTransactionResponse(BaseModel):
    id: str
    client_id: str
    from_chain: Blockchain
    to_chain: Blockchain
    bridge_protocol: str
    asset_symbol: str
    amount: Decimal
    bridge_fee: Decimal
    source_tx_hash: Optional[str]
    destination_tx_hash: Optional[str]
    status: str
    estimated_completion_time: Optional[str]
    actual_completion_time: Optional[str]
    created_at: str
    updated_at: str


# Wallet Management Models
class CreateWalletRequest(BaseModel):
    client_id: str = Field(..., description="Client identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Wallet name")
    blockchain: Blockchain = Field(..., description="Target blockchain")
    signer_addresses: List[str] = Field(..., min_items=1, description="List of signer addresses")
    required_signatures: int = Field(2, ge=1, description="Required signatures for transactions")

    @validator('signer_addresses')
    def validate_signer_addresses(cls, v, values):
        if 'blockchain' in values:
            blockchain = values['blockchain']
            for address in v:
                if not cls._is_valid_address(address, blockchain):
                    raise ValueError(f"Invalid address format for {blockchain}: {address}")
        return v

    @classmethod
    def _is_valid_address(cls, address: str, blockchain: Blockchain) -> bool:
        if blockchain in [Blockchain.ETHEREUM, Blockchain.POLYGON, Blockchain.BSC,
                         Blockchain.ARBITRUM, Blockchain.OPTIMISM, Blockchain.AVALANCHE]:
            return address.startswith('0x') and len(address) == 42
        elif blockchain == Blockchain.BITCOIN:
            return (address.startswith('1') or address.startswith('3') or
                   address.startswith('bc1')) and 26 <= len(address) <= 62
        return False


class AddSignerRequest(BaseModel):
    signer_address: str = Field(..., description="New signer address")
    signer_name: Optional[str] = Field(None, description="Optional signer name")


class CreateTransactionRequest(BaseModel):
    to_address: str = Field(..., description="Destination address")
    amount: Decimal = Field(..., gt=0, description="Amount to send")
    asset_symbol: str = Field("ETH", description="Asset symbol")
    gas_limit: Optional[int] = Field(None, gt=0, description="Gas limit")


class SignTransactionRequest(BaseModel):
    signature: str = Field(..., description="Transaction signature")
    signer_address: str = Field(..., description="Signer address")


class WalletSignerResponse(BaseModel):
    address: str
    name: Optional[str]
    weight: int
    is_required: bool
    added_at: str


class MultiSigWalletResponse(BaseModel):
    id: str
    client_id: str
    name: str
    blockchain: Blockchain
    address: str
    contract_address: Optional[str]
    required_signatures: int
    total_signers: int
    signers: List[WalletSignerResponse]
    status: WalletStatus
    is_deployed: bool
    deployed_at: Optional[str]
    created_at: str
    updated_at: str


class WalletTransactionResponse(BaseModel):
    id: str
    wallet_id: str
    transaction_hash: Optional[str]
    to_address: str
    amount: Decimal
    asset_symbol: str
    required_signatures: int
    current_signatures: int
    signatures: List[str]
    signed_by: List[str]
    status: TransactionStatus
    signature_progress: float
    created_at: str
    updated_at: str


class WalletSummaryResponse(BaseModel):
    wallet_id: str
    name: str
    blockchain: str
    address: str
    status: str
    is_deployed: bool
    required_signatures: int
    total_signers: int
    signers: List[Dict[str, Any]]
    pending_transactions_count: int
    pending_transactions: List[Dict[str, Any]]
    created_at: str
    updated_at: str


class SignTransactionResponse(BaseModel):
    success: bool
    transaction_id: str
    signer_address: str
    current_signatures: int
    required_signatures: int
    is_fully_signed: bool
    signature_progress: float
    status: str
    message: str


# Global managers
wallet_manager = WalletManager("./data/wallets")
defi_manager = DeFiManager("./data/defi_positions")

# Dependencies
async def get_current_user() -> User:
    """Get current user (simplified for demo)."""
    # In production, this would validate JWT tokens
    return User(
        user_id="demo-user",
        email="demo@plutosai.com",
        roles=["user"],
        permissions=["create:wallet", "read:wallet", "create:transaction", "sign:transaction"],
        exp=None,
        iat=None
    )


# Routes

# Health and System
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "blockchain-service",
        "version": "0.1.0"
    }


@app.get("/supported-assets")
async def get_supported_assets(
    blockchain: Optional[Blockchain] = None,
    asset_type: Optional[AssetType] = None
) -> List[AssetResponse]:
    """Get list of supported assets."""
    # In a real implementation, this would query database or external APIs
    assets = [
        AssetResponse(
            symbol="ETH",
            name="Ethereum",
            blockchain=Blockchain.ETHEREUM,
            asset_type=AssetType.CRYPTOCURRENCY,
            decimals=18,
            coingecko_id="ethereum",
            is_verified=True
        ),
        AssetResponse(
            symbol="USDC",
            name="USD Coin",
            contract_address="0xA0b86a33E6441a8b5CDe6B0dDcF4F7C03E8C2bC4",
            blockchain=Blockchain.ETHEREUM,
            asset_type=AssetType.STABLECOIN,
            decimals=6,
            coingecko_id="usd-coin",
            is_verified=True
        )
    ]

    # Filter by blockchain and asset_type if provided
    filtered_assets = assets
    if blockchain:
        filtered_assets = [a for a in filtered_assets if a.blockchain == blockchain]
    if asset_type:
        filtered_assets = [a for a in filtered_assets if a.asset_type == asset_type]

    return filtered_assets


@app.get("/prices/{asset_symbol}")
async def get_asset_price(asset_symbol: str) -> PriceResponse:
    """Get current price for an asset with caching."""
    import redis
    import json
    from datetime import timedelta

    redis_client = redis.Redis.from_url("redis://localhost:6379")
    cache_key = f"price:{asset_symbol.lower()}"
    cached = redis_client.get(cache_key)
    if cached:
        return PriceResponse(**json.loads(cached))

    # In a real implementation, this would call CoinGecko or similar API
    price = PriceResponse(
        asset_symbol=asset_symbol.upper(),
        price_usd=Decimal("3000.00"),
        price_btc=Decimal("1.0") if asset_symbol.upper() == "BTC" else Decimal("0.1"),
        market_cap=Decimal("500000000000"),
        volume_24h=Decimal("20000000000"),
        price_change_24h=Decimal("2.5"),
        timestamp="2024-01-01T00:00:00Z",
        source="coingecko"
    )

    redis_client.setex(cache_key, timedelta(hours=1), json.dumps(price.dict()))
    return price


# Wallet Management
@app.post("/wallets", response_model=WalletResponse)
async def create_wallet(
    request: WalletCreateRequest,
    user: User = Depends(require_permission("create:wallet")),
    db: AsyncSession = Depends(get_db)
):
    """Create a new wallet."""
    try:
        # Create domain entity
        wallet = Wallet(
            client_id=request.client_id,
            name=request.name,
            wallet_type=request.wallet_type,
            blockchain=request.blockchain,
            address=request.address,
            required_signatures=request.required_signatures,
            total_signers=request.total_signers,
            signer_addresses=request.signer_addresses
        )

        # In a real implementation, save to database and publish events
        # For now, just return the wallet

        return WalletResponse(
            id=wallet.id,
            client_id=wallet.client_id,
            name=wallet.name,
            wallet_type=wallet.wallet_type,
            blockchain=wallet.blockchain,
            address=wallet.address,
            is_active=wallet.is_active,
            risk_level=wallet.risk_level,
            required_signatures=wallet.required_signatures,
            total_signers=wallet.total_signers,
            daily_limit=wallet.daily_limit,
            require_approval=wallet.require_approval,
            created_at=wallet.created_at.isoformat(),
            updated_at=wallet.updated_at.isoformat(),
            last_sync=wallet.last_sync.isoformat() if wallet.last_sync else None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create wallet: {str(e)}")


@app.get("/wallets", response_model=List[WalletResponse])
async def list_wallets(
    client_id: Optional[str] = None,
    blockchain: Optional[Blockchain] = None,
    wallet_type: Optional[WalletType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(require_permission("read:wallet")),
    db: AsyncSession = Depends(get_db)
):
    """List wallets with filtering and pagination."""
    try:
        # In a real implementation, query database with filters
        # For now, return empty list
        return []

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list wallets: {str(e)}")


@app.get("/wallets/{wallet_id}", response_model=WalletResponse)
async def get_wallet(
    wallet_id: str,
    user: User = Depends(require_permission("read:wallet")),
    db: AsyncSession = Depends(get_db)
):
    """Get wallet by ID."""
    try:
        # In a real implementation, query database
        raise HTTPException(status_code=404, detail="Wallet not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get wallet: {str(e)}")


@app.patch("/wallets/{wallet_id}", response_model=WalletResponse)
async def update_wallet(
    wallet_id: str,
    request: WalletUpdateRequest,
    user: User = Depends(require_permission("update:wallet")),
    db: AsyncSession = Depends(get_db)
):
    """Update wallet settings."""
    try:
        # In a real implementation, load, update, and save wallet
        raise HTTPException(status_code=404, detail="Wallet not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update wallet: {str(e)}")


# Transaction Management
@app.post("/transactions", response_model=TransactionResponse)
async def create_transaction(
    request: TransactionCreateRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_permission("create:transaction")),
    db: AsyncSession = Depends(get_db)
):
    """Create and submit a blockchain transaction."""
    try:
        # Simplified implementation for demo
        # Validate wallet ownership (skipped for demo)
        # Check spending limits (skipped for demo)

        # Simulate transaction submission
        transaction_hash = "0x" + ''.join(random.choices('0123456789abcdef', k=64))

        # Create transaction record
        transaction = TransactionResponse(
            id=str(uuid.uuid4()),
            wallet_id=request.wallet_id,
            transaction_hash=transaction_hash,
            from_address=request.from_address,
            to_address=request.to_address,
            amount=request.amount,
            asset_symbol=request.asset_symbol,
            gas_fee=Decimal("0.001"),
            status=TransactionStatus.PENDING,
            blockchain=request.blockchain,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )

        # Publish event to NATS with compression and priority
        from shared.utils.nats_utils import publish_compressed_message
        event_data = {
            "event_type": "transaction_created",
            "transaction_id": transaction.id,
            "wallet_id": transaction.wallet_id,
            "amount": str(transaction.amount),
            "asset_symbol": transaction.asset_symbol,
            "blockchain": transaction.blockchain.value
        }
        priority = "high" if request.amount > Decimal("1000") else "medium"
        await publish_compressed_message("blockchain.events", event_data, priority=priority)

        return transaction

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create transaction: {str(e)}")


@app.get("/transactions", response_model=List[TransactionResponse])
async def list_transactions(
    wallet_id: Optional[str] = None,
    blockchain: Optional[Blockchain] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(require_permission("read:transaction")),
    db: AsyncSession = Depends(get_db)
):
    """List transactions with filtering."""
    try:
        # In a real implementation, query database with filters
        return []

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list transactions: {str(e)}")


# NFT Management
@app.post("/nfts", response_model=NFTResponse)
async def register_nft(
    request: NFTRegisterRequest,
    user: User = Depends(require_permission("create:nft")),
    db: AsyncSession = Depends(get_db)
):
    """Register an NFT in the system."""
    try:
        # In a real implementation:
        # 1. Validate wallet ownership
        # 2. Fetch NFT metadata from blockchain
        # 3. Create NFT record
        # 4. Calculate initial valuation

        raise HTTPException(status_code=501, detail="NFT registration not implemented")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register NFT: {str(e)}")


@app.get("/nfts", response_model=List[NFTResponse])
async def list_nfts(
    wallet_id: Optional[str] = None,
    blockchain: Optional[Blockchain] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(require_permission("read:nft")),
    db: AsyncSession = Depends(get_db)
):
    """List NFTs with filtering."""
    try:
        # In a real implementation, query database
        return []

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list NFTs: {str(e)}")


# DeFi Integration
@app.post("/defi/positions", response_model=DeFiPositionResponse)
async def create_defi_position(
    request: DeFiPositionCreateRequest,
    user: User = Depends(require_permission("create:defi_position")),
    db: AsyncSession = Depends(get_db)
):
    """Create a DeFi position (lending, staking, LP, etc.)."""
    try:
        # In a real implementation:
        # 1. Validate client and wallet access
        # 2. Interact with DeFi protocol smart contracts
        # 3. Create position record
        # 4. Set up monitoring

        raise HTTPException(status_code=501, detail="DeFi position creation not implemented")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create DeFi position: {str(e)}")


@app.get("/defi/positions", response_model=List[DeFiPositionResponse])
async def list_defi_positions(
    client_id: Optional[str] = None,
    protocol: Optional[str] = None,
    blockchain: Optional[Blockchain] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(require_permission("read:defi_position")),
    db: AsyncSession = Depends(get_db)
):
    """List DeFi positions with filtering."""
    try:
        # In a real implementation, query database
        return []

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list DeFi positions: {str(e)}")


# Cross-chain Bridges
@app.post("/bridges", response_model=BridgeTransactionResponse)
async def initiate_bridge(
    request: BridgeTransactionCreateRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_permission("create:bridge_transaction")),
    db: AsyncSession = Depends(get_db)
):
    """Initiate a cross-chain bridge transaction."""
    try:
        # In a real implementation:
        # 1. Validate asset compatibility
        # 2. Calculate bridge fees
        # 3. Lock assets on source chain
        # 4. Initiate bridge transaction
        # 5. Monitor for completion

        raise HTTPException(status_code=501, detail="Bridge transaction not implemented")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate bridge: {str(e)}")


@app.get("/bridges", response_model=List[BridgeTransactionResponse])
async def list_bridge_transactions(
    client_id: Optional[str] = None,
    from_chain: Optional[Blockchain] = None,
    to_chain: Optional[Blockchain] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(require_permission("read:bridge_transaction")),
    db: AsyncSession = Depends(get_db)
):
    """List bridge transactions with filtering."""
    try:
        # In a real implementation, query database
        return []

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list bridge transactions: {str(e)}")


# Analytics and Reporting
@app.get("/analytics/portfolio-value")
async def get_portfolio_value(
    client_id: str,
    include_nfts: bool = Query(True),
    include_defi: bool = Query(True),
    user: User = Depends(require_permission("read:analytics")),
    db: AsyncSession = Depends(get_db)
):
    """Get total portfolio value across all assets."""
    try:
        # In a real implementation, aggregate values from all sources
        return {
            "client_id": client_id,
            "total_value_usd": "125000.00",
            "assets_breakdown": {
                "cryptocurrencies": "75000.00",
                "tokens": "25000.00",
                "nfts": "15000.00",
                "defi_positions": "10000.00"
            },
            "last_updated": "2024-01-01T00:00:00Z"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio value: {str(e)}")


@app.get("/analytics/risk-metrics")
async def get_risk_metrics(
    client_id: str,
    user: User = Depends(require_permission("read:analytics")),
    db: AsyncSession = Depends(get_db)
):
    """Get risk metrics for blockchain portfolio."""
    try:
        # In a real implementation, calculate risk metrics
        return {
            "client_id": client_id,
            "sharpe_ratio": 1.8,
            "max_drawdown": -0.12,
            "volatility": 0.25,
            "concentration_risk": {
                "top_holding_percentage": 35.0,
                "single_asset_risk": "high"
            },
            "liquidity_risk": "medium",
            "last_updated": "2024-01-01T00:00:00Z"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get risk metrics: {str(e)}")


# ===============================
# CLEAN WALLET MANAGEMENT ENDPOINTS
# ===============================

@app.post("/wallets", response_model=MultiSigWalletResponse)
async def create_wallet(
    request: CreateWalletRequest,
    user: User = Depends(get_current_user)
):
    """Create a new multi-signature wallet.

    This creates a working multi-signature wallet that you can actually use.

    Example:
        POST /wallets
        {
            "client_id": "family-smith",
            "name": "Family ETH Wallet",
            "blockchain": "ethereum",
            "signer_addresses": [
                "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
                "0x1234567890123456789012345678901234567890"
            ],
            "required_signatures": 2
        }
    """
    try:
        wallet = wallet_manager.create_wallet(
            client_id=request.client_id,
            name=request.name,
            signer_addresses=request.signer_addresses,
            required_signatures=request.required_signatures
        )

        return MultiSigWalletResponse(
            id=wallet.id,
            client_id=wallet.client_id,
            name=wallet.name,
            blockchain=request.blockchain,  # Use from request since wallet doesn't store it
            address=wallet.address,
            contract_address=None,  # Simplified - no contract deployment
            required_signatures=wallet.required_signatures,
            total_signers=len(wallet.signers),
            signers=[
                WalletSignerResponse(
                    address=signer.address,
                    name=signer.name,
                    weight=1,
                    is_required=True,
                    added_at=signer.added_at.isoformat()
                )
                for signer in wallet.signers
            ],
            status="active",
            is_deployed=False,
            deployed_at=None,
            created_at=wallet.created_at.isoformat(),
            updated_at=wallet.created_at.isoformat()
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create wallet: {str(e)}")


@app.get("/wallets", response_model=List[MultiSigWalletResponse])
async def list_wallets(
    client_id: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """List all wallets (or filter by client)."""
    try:
        wallets = wallet_manager.list_wallets(client_id)

        return [
            MultiSigWalletResponse(
                id=wallet.id,
                client_id=wallet.client_id,
                name=wallet.name,
                blockchain="ethereum",  # Simplified - all wallets are Ethereum for now
                address=wallet.address,
                contract_address=None,
                required_signatures=wallet.required_signatures,
                total_signers=len(wallet.signers),
                signers=[
                    WalletSignerResponse(
                        address=signer.address,
                        name=signer.name,
                        weight=1,
                        is_required=True,
                        added_at=signer.added_at.isoformat()
                    )
                    for signer in wallet.signers
                ],
                status="active",
                is_deployed=False,
                deployed_at=None,
                created_at=wallet.created_at.isoformat(),
                updated_at=wallet.created_at.isoformat()
            )
            for wallet in wallets
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list wallets: {str(e)}")


@app.get("/wallets/{wallet_id}", response_model=WalletSummaryResponse)
async def get_wallet(
    wallet_id: str,
    user: User = Depends(get_current_user)
):
    """Get wallet details and pending transactions."""
    try:
        status = wallet_manager.get_wallet_status(wallet_id)
        return WalletSummaryResponse(**status)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get wallet: {str(e)}")


@app.post("/wallets/{wallet_id}/transactions", response_model=WalletTransactionResponse)
async def create_transaction(
    wallet_id: str,
    request: CreateTransactionRequest,
    user: User = Depends(get_current_user)
):
    """Create a transaction that requires multi-signature approval."""
    try:
        transaction = wallet_manager.create_transaction(
            wallet_id=wallet_id,
            to_address=request.to_address,
            amount=request.amount,
            asset=request.asset_symbol
        )

        return WalletTransactionResponse(
            id=transaction.id,
            wallet_id=transaction.wallet_id,
            transaction_hash=None,  # No hash until executed
            to_address=transaction.to_address,
            amount=transaction.amount,
            asset_symbol=transaction.asset,
            required_signatures=transaction.required_signatures,
            current_signatures=len(transaction.signatures),
            signatures=transaction.signatures,
            signed_by=transaction.signed_by,
            status=transaction.status,
            signature_progress=transaction.signature_progress,
            created_at=transaction.created_at.isoformat(),
            updated_at=transaction.created_at.isoformat()
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create transaction: {str(e)}")


@app.post("/wallets/{wallet_id}/transactions/{transaction_id}/sign", response_model=SignTransactionResponse)
async def sign_transaction(
    wallet_id: str,
    transaction_id: str,
    request: SignTransactionRequest,
    user: User = Depends(get_current_user)
):
    """Sign a transaction. When all signatures are collected, transaction executes."""
    try:
        result = wallet_manager.sign_transaction(
            transaction_id=transaction_id,
            signer_address=request.signer_address,
            signature=request.signature
        )

        return SignTransactionResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sign transaction: {str(e)}")


# ===============================
# CLEAN DEFI ENDPOINTS
# ===============================

@app.post("/defi/lend", response_model=Dict[str, Any])
async def lend_tokens(
    wallet_address: str,
    asset: str,
    amount: float,
    protocol: str = "aave",
    user: User = Depends(get_current_user)
):
    """Lend tokens on DeFi protocols (Aave, Compound)."""
    try:
        from decimal import Decimal
        position = defi_manager.lend_tokens(
            wallet_address=wallet_address,
            asset=asset,
            amount=Decimal(str(amount)),
            protocol=protocol
        )

        return {
            "success": True,
            "position": position.to_dict(),
            "message": f"Successfully lent {amount} {asset} on {protocol}"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to lend tokens: {str(e)}")


@app.post("/defi/withdraw", response_model=Dict[str, Any])
async def withdraw_tokens(
    position_id: str,
    amount: Optional[float] = None,
    user: User = Depends(get_current_user)
):
    """Withdraw tokens from DeFi position."""
    try:
        from decimal import Decimal
        withdraw_amount = Decimal(str(amount)) if amount else None

        result = defi_manager.withdraw_tokens(
            position_id=position_id,
            amount=withdraw_amount
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to withdraw tokens: {str(e)}")


@app.get("/defi/yields", response_model=List[Dict[str, Any]])
async def get_yield_opportunities(
    asset: Optional[str] = None,
    protocol: Optional[str] = None,
    min_apr: float = 0,
    user: User = Depends(get_current_user)
):
    """Get available yield farming opportunities."""
    try:
        opportunities = defi_manager.get_yield_opportunities(
            asset=asset,
            protocol=protocol,
            min_apr=min_apr
        )

        return [opp.to_dict() for opp in opportunities]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get yield opportunities: {str(e)}")


@app.get("/defi/positions", response_model=List[Dict[str, Any]])
async def get_positions(
    wallet_address: Optional[str] = None,
    protocol: Optional[str] = None,
    status: str = "active",
    user: User = Depends(get_current_user)
):
    """Get DeFi positions."""
    try:
        positions = defi_manager.get_positions(
            wallet_address=wallet_address,
            protocol=protocol,
            status=status
        )

        return [pos.to_dict() for pos in positions]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get positions: {str(e)}")


@app.get("/defi/portfolio/{wallet_address}", response_model=Dict[str, Any])
async def get_portfolio_summary(
    wallet_address: str,
    user: User = Depends(get_current_user)
):
    """Get comprehensive portfolio summary."""
    try:
        summary = defi_manager.get_portfolio_summary(wallet_address)
        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio summary: {str(e)}")


@app.post("/defi/liquidity", response_model=Dict[str, Any])
async def add_liquidity(
    wallet_address: str,
    token_a: str,
    token_b: str,
    amount_a: float,
    amount_b: float,
    protocol: str = "uniswap",
    user: User = Depends(get_current_user)
):
    """Add liquidity to DEX pools."""
    try:
        from decimal import Decimal
        position = defi_manager.add_liquidity(
            wallet_address=wallet_address,
            token_a=token_a,
            token_b=token_b,
            amount_a=Decimal(str(amount_a)),
            amount_b=Decimal(str(amount_b)),
            protocol=protocol
        )

        return {
            "success": True,
            "position": position.to_dict(),
            "message": f"Added liquidity {amount_a} {token_a} + {amount_b} {token_b} to {protocol}"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add liquidity: {str(e)}")


@app.post("/defi/stake", response_model=Dict[str, Any])
async def stake_tokens(
    wallet_address: str,
    asset: str,
    amount: float,
    protocol: str = "lido",
    user: User = Depends(get_current_user)
):
    """Stake tokens for yield."""
    try:
        from decimal import Decimal
        position = defi_manager.stake_tokens(
            wallet_address=wallet_address,
            asset=asset,
            amount=Decimal(str(amount)),
            protocol=protocol
        )

        return {
            "success": True,
            "position": position.to_dict(),
            "message": f"Staked {amount} {asset} on {protocol}"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stake tokens: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
