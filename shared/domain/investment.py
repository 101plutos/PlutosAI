"""Investment domain models for PlutosAI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import uuid4


class AssetClass(Enum):
    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    ALTERNATIVES = "alternatives"
    CASH = "cash"
    REAL_ESTATE = "real_estate"
    PRIVATE_EQUITY = "private_equity"
    HEDGE_FUND = "hedge_fund"
    COMMODITIES = "commodities"


class SecurityType(Enum):
    STOCK = "stock"
    BOND = "bond"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    OPTION = "option"
    FUTURE = "future"
    CRYPTO = "crypto"
    PRIVATE_SECURITY = "private_security"


class Currency(Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CHF = "CHF"
    CAD = "CAD"
    AUD = "AUD"


class TransactionType(Enum):
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    INTEREST = "interest"
    FEE = "fee"
    TAX = "tax"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    ADJUSTMENT = "adjustment"


@dataclass
class Security:
    """Value object representing a financial security."""
    symbol: str
    name: str
    security_type: SecurityType
    asset_class: AssetClass
    currency: Currency = Currency.USD
    exchange: Optional[str] = None
    isin: Optional[str] = None
    cusip: Optional[str] = None

    def __post_init__(self):
        self.symbol = self.symbol.upper().strip()


@dataclass
class Price:
    """Value object for security price."""
    value: Decimal
    currency: Currency = Currency.USD
    timestamp: datetime
    source: str  # pricing source (e.g., Bloomberg, Yahoo, Manual)


@dataclass
class Position:
    """Entity representing a position in a security."""
    id: str = field(default_factory=lambda: str(uuid4()))
    portfolio_id: str
    security: Security
    quantity: Decimal
    average_cost: Decimal
    currency: Currency = Currency.USD
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def market_value(self) -> Decimal:
        """Calculate market value based on current price."""
        # This would need current price lookup
        return Decimal('0')

    @property
    def unrealized_pnl(self) -> Decimal:
        """Calculate unrealized P&L."""
        return (self.market_value - (self.average_cost * self.quantity))


@dataclass
class Transaction:
    """Entity representing a transaction."""
    id: str = field(default_factory=lambda: str(uuid4()))
    portfolio_id: str
    security: Security
    transaction_type: TransactionType
    quantity: Decimal
    price: Decimal
    currency: Currency = Currency.USD
    trade_date: date
    settlement_date: Optional[date] = None
    counterparty: Optional[str] = None
    order_id: Optional[str] = None
    fees: Decimal = Decimal('0')
    taxes: Decimal = Decimal('0')
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def gross_amount(self) -> Decimal:
        """Calculate gross transaction amount."""
        return self.quantity * self.price

    @property
    def net_amount(self) -> Decimal:
        """Calculate net transaction amount."""
        return self.gross_amount + self.fees + self.taxes


@dataclass
class Portfolio:
    """Aggregate root for portfolio domain."""
    id: str = field(default_factory=lambda: str(uuid4()))
    client_id: str
    name: str
    description: Optional[str] = None
    benchmark: Optional[str] = None  # Benchmark index symbol
    currency: Currency = Currency.USD
    status: str = "active"

    # Portfolio composition constraints
    target_allocation: dict[str, Decimal] = field(default_factory=dict)
    min_allocation: dict[str, Decimal] = field(default_factory=dict)
    max_allocation: dict[str, Decimal] = field(default_factory=dict)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    # Domain events
    events: List[object] = field(default_factory=list, init=False)

    def __post_init__(self):
        self.name = self.name.strip()

    @property
    def positions(self) -> List[Position]:
        """Get all positions (would be loaded from repository)."""
        # This would be implemented in repository layer
        return []

    @property
    def total_value(self) -> Decimal:
        """Calculate total portfolio value."""
        return sum(pos.market_value for pos in self.positions)

    def add_position(self, security: Security, quantity: Decimal, price: Decimal, added_by: str):
        """Add a new position to the portfolio."""
        position = Position(
            portfolio_id=self.id,
            security=security,
            quantity=quantity,
            average_cost=price
        )

        self.updated_at = datetime.utcnow()
        self.updated_by = added_by

        event = PortfolioPositionAdded(
            portfolio_id=self.id,
            security_symbol=security.symbol,
            quantity=quantity,
            price=price,
            added_at=self.updated_at,
            added_by=added_by
        )
        self.events.append(event)

    def record_transaction(self, transaction: Transaction, recorded_by: str):
        """Record a transaction against the portfolio."""
        self.updated_at = datetime.utcnow()
        self.updated_by = recorded_by

        event = PortfolioTransactionRecorded(
            portfolio_id=self.id,
            transaction_id=transaction.id,
            security_symbol=transaction.security.symbol,
            transaction_type=transaction.transaction_type,
            quantity=transaction.quantity,
            price=transaction.price,
            recorded_at=self.updated_at,
            recorded_by=recorded_by
        )
        self.events.append(event)


@dataclass
class PortfolioSummary:
    """Read model for portfolio summary."""
    portfolio_id: str
    total_value: Decimal
    total_positions: int
    asset_allocation: dict[str, Decimal]
    performance_ytd: Optional[Decimal] = None
    performance_1y: Optional[Decimal] = None
    performance_3y: Optional[Decimal] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)


# Domain Events
@dataclass
class PortfolioCreated:
    portfolio_id: str
    client_id: str
    name: str
    created_at: datetime
    created_by: str


@dataclass
class PortfolioPositionAdded:
    portfolio_id: str
    security_symbol: str
    quantity: Decimal
    price: Decimal
    added_at: datetime
    added_by: str


@dataclass
class PortfolioTransactionRecorded:
    portfolio_id: str
    transaction_id: str
    security_symbol: str
    transaction_type: TransactionType
    quantity: Decimal
    price: Decimal
    recorded_at: datetime
    recorded_by: str


@dataclass
class PortfolioAllocationChanged:
    portfolio_id: str
    old_allocation: dict[str, Decimal]
    new_allocation: dict[str, Decimal]
    changed_at: datetime
    changed_by: str
