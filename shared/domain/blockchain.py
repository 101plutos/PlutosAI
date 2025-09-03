"""Blockchain domain models for PlutosAI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import uuid4


class Blockchain(Enum):
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    BSC = "bsc"  # Binance Smart Chain
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    AVALANCHE = "avalanche"
    SOLANA = "solana"
    BITCOIN = "bitcoin"
    LITECOIN = "litecoin"
    POLKADOT = "polkadot"


class AssetType(Enum):
    CRYPTOCURRENCY = "cryptocurrency"
    TOKEN = "token"  # ERC-20, BEP-20, etc.
    NFT = "nft"  # ERC-721, ERC-1155
    SECURITY_TOKEN = "security_token"  # STOs, tokenized securities
    STABLECOIN = "stablecoin"
    GOVERNANCE_TOKEN = "governance_token"


class TransactionType(Enum):
    TRANSFER = "transfer"
    SWAP = "swap"
    STAKE = "stake"
    UNSTAKE = "unstake"
    LEND = "lend"
    BORROW = "borrow"
    REDEEM = "redeem"
    CLAIM_REWARDS = "claim_rewards"
    BRIDGE = "bridge"  # Cross-chain transfer
    MINT = "mint"  # NFT minting
    BURN = "burn"
    APPROVE = "approve"  # Token approval for spending


class WalletType(Enum):
    HOT_WALLET = "hot_wallet"  # Connected to internet, for active trading
    COLD_WALLET = "cold_wallet"  # Offline storage, for long-term holding
    MULTISIG_WALLET = "multisig_wallet"  # Multi-signature wallet
    HARDWARE_WALLET = "hardware_wallet"  # Hardware security module
    CUSTODY_WALLET = "custody_wallet"  # Third-party custodian


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Asset:
    """Value object representing a blockchain asset."""
    symbol: str
    name: str
    contract_address: Optional[str] = None  # None for native tokens like ETH, BTC
    blockchain: Blockchain = Blockchain.ETHEREUM
    asset_type: AssetType = AssetType.CRYPTOCURRENCY
    decimals: int = 18
    coingecko_id: Optional[str] = None  # For price data integration
    is_verified: bool = False

    def __post_init__(self):
        self.symbol = self.symbol.upper().strip()


@dataclass
class Price:
    """Value object for asset price."""
    asset_symbol: str
    price_usd: Decimal
    price_btc: Optional[Decimal] = None
    market_cap: Optional[Decimal] = None
    volume_24h: Optional[Decimal] = None
    price_change_24h: Optional[Decimal] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = "coingecko"  # coingecko, defillama, etc.


@dataclass
class Wallet:
    """Entity representing a blockchain wallet."""
    id: str = field(default_factory=lambda: str(uuid4()))
    client_id: str
    name: str
    wallet_type: WalletType
    blockchain: Blockchain
    address: str
    public_key: Optional[str] = None
    encrypted_private_key: Optional[str] = None  # Encrypted with client-specific key
    derivation_path: Optional[str] = None  # For HD wallets
    is_active: bool = True
    risk_level: RiskLevel = RiskLevel.MEDIUM

    # Multi-signature settings
    required_signatures: int = 1
    total_signers: int = 1
    signer_addresses: List[str] = field(default_factory=list)

    # Security settings
    daily_limit: Optional[Decimal] = None
    require_approval: bool = False
    whitelisted_addresses: List[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_sync: Optional[datetime] = None

    # Domain events
    events: List[object] = field(default_factory=list, init=False)

    def __post_init__(self):
        self.name = self.name.strip()
        if self.wallet_type == WalletType.MULTISIG_WALLET:
            if len(self.signer_addresses) < self.total_signers:
                raise ValueError("Number of signer addresses must match total_signers")

    def add_transaction(self, transaction: BlockchainTransaction, added_by: str):
        """Record a new transaction."""
        self.updated_at = datetime.utcnow()
        self.last_sync = datetime.utcnow()

        event = WalletTransactionAdded(
            wallet_id=self.id,
            transaction_id=transaction.id,
            transaction_type=transaction.transaction_type,
            amount=transaction.amount,
            asset_symbol=transaction.asset_symbol,
            added_at=self.updated_at,
            added_by=added_by
        )
        self.events.append(event)

    def update_balance(self, asset_symbol: str, new_balance: Decimal, updated_by: str):
        """Update wallet balance for an asset."""
        self.updated_at = datetime.utcnow()

        event = WalletBalanceUpdated(
            wallet_id=self.id,
            asset_symbol=asset_symbol,
            new_balance=new_balance,
            updated_at=self.updated_at,
            updated_by=updated_by
        )
        self.events.append(event)

    def flag_suspicious_activity(self, reason: str, severity: RiskLevel, flagged_by: str):
        """Flag wallet for suspicious activity."""
        self.risk_level = severity
        self.updated_at = datetime.utcnow()

        event = WalletSuspiciousActivityFlagged(
            wallet_id=self.id,
            reason=reason,
            severity=severity,
            flagged_at=self.updated_at,
            flagged_by=flagged_by
        )
        self.events.append(event)


@dataclass
class BlockchainTransaction:
    """Entity representing a blockchain transaction."""
    id: str = field(default_factory=lambda: str(uuid4()))
    wallet_id: str
    blockchain: Blockchain
    transaction_hash: str
    block_number: Optional[int] = None
    block_timestamp: Optional[datetime] = None

    # Transaction details
    transaction_type: TransactionType
    from_address: str
    to_address: Optional[str] = None
    contract_address: Optional[str] = None  # For token transactions
    asset_symbol: str
    amount: Decimal
    gas_used: Optional[int] = None
    gas_price: Optional[Decimal] = None
    transaction_fee: Optional[Decimal] = None

    # Status
    status: str = "pending"  # pending, confirmed, failed
    confirmations: int = 0
    is_internal: bool = False  # Internal wallet-to-wallet transfer

    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_data: Optional[str] = None  # Raw transaction data

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Domain events
    events: List[object] = field(default_factory=list, init=False)

    def confirm_transaction(self, block_number: int, timestamp: datetime):
        """Mark transaction as confirmed."""
        self.status = "confirmed"
        self.block_number = block_number
        self.block_timestamp = timestamp
        self.updated_at = datetime.utcnow()

        event = TransactionConfirmed(
            transaction_id=self.id,
            transaction_hash=self.transaction_hash,
            block_number=block_number,
            confirmations=self.confirmations,
            confirmed_at=self.updated_at
        )
        self.events.append(event)

    def fail_transaction(self, reason: str):
        """Mark transaction as failed."""
        self.status = "failed"
        self.updated_at = datetime.utcnow()

        event = TransactionFailed(
            transaction_id=self.id,
            transaction_hash=self.transaction_hash,
            reason=reason,
            failed_at=self.updated_at
        )
        self.events.append(event)


@dataclass
class NFT:
    """Entity representing a Non-Fungible Token."""
    id: str = field(default_factory=lambda: str(uuid4()))
    wallet_id: str
    blockchain: Blockchain
    contract_address: str
    token_id: str
    token_standard: str  # ERC-721, ERC-1155

    # Metadata
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

    # Valuation
    floor_price: Optional[Decimal] = None
    last_sale_price: Optional[Decimal] = None
    estimated_value: Optional[Decimal] = None

    # Acquisition details
    acquired_at: Optional[datetime] = None
    acquisition_cost: Optional[Decimal] = None
    acquisition_tx_hash: Optional[str] = None

    # Current status
    is_listed: bool = False
    listing_price: Optional[Decimal] = None
    listing_platform: Optional[str] = None  # opensea, blur, etc.

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Domain events
    events: List[object] = field(default_factory=list, init=False)

    def update_valuation(self, estimated_value: Decimal, updated_by: str):
        """Update NFT valuation."""
        self.estimated_value = estimated_value
        self.updated_at = datetime.utcnow()

        event = NFTValuationUpdated(
            nft_id=self.id,
            token_id=self.token_id,
            estimated_value=estimated_value,
            updated_at=self.updated_at,
            updated_by=updated_by
        )
        self.events.append(event)


@dataclass
class DeFiPosition:
    """Entity representing a DeFi position (lending, staking, LP, etc.)."""
    id: str = field(default_factory=lambda: str(uuid4()))
    wallet_id: str
    client_id: str
    protocol: str  # aave, compound, uniswap, etc.
    blockchain: Blockchain
    position_type: str  # lending, staking, liquidity_pool, etc.

    # Assets involved
    assets: List[str] = field(default_factory=list)  # Asset symbols
    amounts: Dict[str, Decimal] = field(default_factory=dict)

    # Position details
    apr: Optional[Decimal] = None  # Annual percentage rate
    apy: Optional[Decimal] = None  # Annual percentage yield
    rewards_earned: Dict[str, Decimal] = field(default_factory=dict)

    # Risk metrics
    liquidation_price: Optional[Decimal] = None
    ltv_ratio: Optional[Decimal] = None  # Loan-to-value ratio

    # Status
    is_active: bool = True
    last_updated: datetime = field(default_factory=datetime.utcnow)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Domain events
    events: List[object] = field(default_factory=list, init=False)


@dataclass
class BridgeTransaction:
    """Entity representing a cross-chain bridge transaction."""
    id: str = field(default_factory=lambda: str(uuid4()))
    client_id: str
    from_chain: Blockchain
    to_chain: Blockchain
    bridge_protocol: str  # polygon-bridge, arbitrum-bridge, etc.

    # Asset details
    asset_symbol: str
    amount: Decimal
    bridge_fee: Decimal

    # Transaction hashes
    source_tx_hash: Optional[str] = None
    destination_tx_hash: Optional[str] = None

    # Status
    status: str = "pending"  # pending, bridging, completed, failed
    source_confirmations: int = 0
    destination_confirmations: int = 0

    # Estimated times
    estimated_completion_time: Optional[datetime] = None
    actual_completion_time: Optional[datetime] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Domain events
    events: List[object] = field(default_factory=list, init=False)


# Domain Events
@dataclass
class WalletTransactionAdded:
    wallet_id: str
    transaction_id: str
    transaction_type: TransactionType
    amount: Decimal
    asset_symbol: str
    added_at: datetime
    added_by: str


@dataclass
class WalletBalanceUpdated:
    wallet_id: str
    asset_symbol: str
    new_balance: Decimal
    updated_at: datetime
    updated_by: str


@dataclass
class WalletSuspiciousActivityFlagged:
    wallet_id: str
    reason: str
    severity: RiskLevel
    flagged_at: datetime
    flagged_by: str


@dataclass
class TransactionConfirmed:
    transaction_id: str
    transaction_hash: str
    block_number: int
    confirmations: int
    confirmed_at: datetime


@dataclass
class TransactionFailed:
    transaction_id: str
    transaction_hash: str
    reason: str
    failed_at: datetime


@dataclass
class NFTValuationUpdated:
    nft_id: str
    token_id: str
    estimated_value: Decimal
    updated_at: datetime
    updated_by: str


@dataclass
class DeFiPositionCreated:
    position_id: str
    client_id: str
    protocol: str
    position_type: str
    assets: List[str]
    created_at: datetime


@dataclass
class BridgeTransactionInitiated:
    bridge_id: str
    client_id: str
    from_chain: Blockchain
    to_chain: Blockchain
    asset_symbol: str
    amount: Decimal
    initiated_at: datetime


@dataclass
class AssetPriceUpdated:
    asset_symbol: str
    old_price: Decimal
    new_price: Decimal
    updated_at: datetime
