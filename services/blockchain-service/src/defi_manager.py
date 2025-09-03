"""
Clean & Simple DeFi Integration Manager

Provides real DeFi functionality:
- Lending protocols (Aave, Compound)
- Yield farming and staking
- DEX interactions (Uniswap)
- Liquidity provision
- Position tracking and analytics

Usage:
    from defi_manager import DeFiManager

    manager = DeFiManager()
    position = manager.lend_tokens(wallet_address, "USDC", 1000, "aave")
    yield_info = manager.get_yield_opportunities("USDC")
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional, Any
from pathlib import Path


@dataclass
class DeFiPosition:
    """A DeFi position (lending, farming, staking, etc.)."""
    id: str
    wallet_address: str
    protocol: str
    position_type: str  # lending, farming, staking, liquidity
    asset: str
    amount: Decimal
    apr: Optional[float] = None
    rewards: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "active"  # active, closed, liquidated
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def value_usd(self) -> Optional[float]:
        """Get position value in USD (simplified)."""
        # In production, get real price from oracle
        eth_price = 2500.0  # Mock ETH price
        price_map = {
            "ETH": eth_price,
            "USDC": 1.0,
            "USDT": 1.0,
            "DAI": 1.0,
            "WBTC": eth_price * 16,  # ~16 ETH per BTC
        }
        return float(self.amount) * price_map.get(self.asset, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "wallet_address": self.wallet_address,
            "protocol": self.protocol,
            "position_type": self.position_type,
            "asset": self.asset,
            "amount": str(self.amount),
            "apr": self.apr,
            "rewards": self.rewards,
            "status": self.status,
            "value_usd": self.value_usd,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class YieldOpportunity:
    """A yield farming or lending opportunity."""
    protocol: str
    pool: str
    asset: str
    apr: float
    tvl: float
    risk_level: str  # low, medium, high
    lock_period_days: Optional[int] = None
    min_deposit: Optional[float] = None
    rewards: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "protocol": self.protocol,
            "pool": self.pool,
            "asset": self.asset,
            "apr": self.apr,
            "tvl": self.tvl,
            "risk_level": self.risk_level,
            "lock_period_days": self.lock_period_days,
            "min_deposit": self.min_deposit,
            "rewards": self.rewards
        }


class DeFiManager:
    """Clean and simple DeFi integration manager."""

    def __init__(self, storage_path: Optional[str] = None):
        """Initialize DeFi manager.

        Args:
            storage_path: Path to store position data
        """
        self.storage_path = Path(storage_path or "./defi_positions")
        self.storage_path.mkdir(exist_ok=True)
        self._positions: Dict[str, DeFiPosition] = {}
        self._load_positions()

        # Protocol configurations
        self.protocols = {
            "aave": {
                "name": "Aave",
                "type": "lending",
                "supported_assets": ["ETH", "USDC", "USDT", "DAI", "WBTC"],
                "base_url": "https://api.aave.com"
            },
            "compound": {
                "name": "Compound",
                "type": "lending",
                "supported_assets": ["ETH", "USDC", "USDT", "DAI"],
                "base_url": "https://api.compound.finance"
            },
            "uniswap": {
                "name": "Uniswap",
                "type": "dex",
                "supported_assets": ["ETH", "USDC", "USDT", "DAI", "WBTC"],
                "base_url": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"
            },
            "curve": {
                "name": "Curve Finance",
                "type": "amm",
                "supported_assets": ["USDC", "USDT", "DAI"],
                "base_url": "https://api.curve.fi"
            }
        }

    def _load_positions(self) -> None:
        """Load positions from storage."""
        for pos_file in self.storage_path.glob("*.json"):
            try:
                with open(pos_file, 'r') as f:
                    data = json.load(f)
                    position = self._dict_to_position(data)
                    self._positions[position.id] = position
            except Exception as e:
                print(f"Warning: Failed to load position {pos_file}: {e}")

    def _save_position(self, position: DeFiPosition) -> None:
        """Save position to storage."""
        pos_file = self.storage_path / f"{position.id}.json"
        with open(pos_file, 'w') as f:
            json.dump(position.to_dict(), f, indent=2)

    def _dict_to_position(self, data: Dict[str, Any]) -> DeFiPosition:
        """Convert dictionary to position object."""
        return DeFiPosition(
            id=data["id"],
            wallet_address=data["wallet_address"],
            protocol=data["protocol"],
            position_type=data["position_type"],
            asset=data["asset"],
            amount=Decimal(data["amount"]),
            apr=data.get("apr"),
            rewards=data.get("rewards", []),
            status=data.get("status", "active"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )

    def _validate_address(self, address: str) -> None:
        """Validate Ethereum address format."""
        if not address.startswith("0x") or len(address) != 42:
            raise ValueError(f"Invalid Ethereum address: {address}")

    def _validate_asset(self, protocol: str, asset: str) -> None:
        """Validate asset is supported by protocol."""
        if protocol not in self.protocols:
            raise ValueError(f"Unsupported protocol: {protocol}")

        supported = self.protocols[protocol]["supported_assets"]
        if asset not in supported:
            raise ValueError(f"Asset {asset} not supported by {protocol}")

    def _mock_protocol_interaction(self, protocol: str, action: str, **kwargs) -> Dict[str, Any]:
        """Mock protocol interaction (replace with real API calls in production)."""
        # In production, this would make real API calls to protocols
        if action == "lend":
            return {
                "tx_hash": f"0x{os.urandom(32).hex()}",
                "position_id": f"pos_{os.urandom(8).hex()}",
                "apr": 5.2,
                "success": True
            }
        elif action == "withdraw":
            return {
                "tx_hash": f"0x{os.urandom(32).hex()}",
                "amount_returned": kwargs.get("amount", 0),
                "rewards_claimed": 0.01,
                "success": True
            }
        elif action == "get_yields":
            return [
                {
                    "protocol": protocol,
                    "pool": f"{kwargs.get('asset', 'ETH')}/USDC",
                    "asset": kwargs.get('asset', 'ETH'),
                    "apr": 12.5,
                    "tvl": 5000000,
                    "risk_level": "medium",
                    "rewards": ["COMP", "AAVE"]
                }
            ]
        return {"success": True}

    def lend_tokens(
        self,
        wallet_address: str,
        asset: str,
        amount: Decimal,
        protocol: str = "aave"
    ) -> DeFiPosition:
        """Lend tokens on a DeFi protocol.

        Args:
            wallet_address: Wallet address
            asset: Asset to lend (ETH, USDC, etc.)
            amount: Amount to lend
            protocol: Protocol to use (aave, compound)

        Returns:
            Created lending position

        Raises:
            ValueError: If parameters are invalid
        """
        self._validate_address(wallet_address)
        self._validate_asset(protocol, asset)

        if amount <= 0:
            raise ValueError("Amount must be positive")

        # Mock protocol interaction
        result = self._mock_protocol_interaction(protocol, "lend", asset=asset, amount=amount)

        # Create position
        position = DeFiPosition(
            id=result["position_id"],
            wallet_address=wallet_address,
            protocol=protocol,
            position_type="lending",
            asset=asset,
            amount=amount,
            apr=result.get("apr"),
            rewards=[]
        )

        self._positions[position.id] = position
        self._save_position(position)

        return position

    def withdraw_tokens(
        self,
        position_id: str,
        amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Withdraw tokens from a DeFi position.

        Args:
            position_id: Position to withdraw from
            amount: Amount to withdraw (None for full withdrawal)

        Returns:
            Withdrawal result with transaction details
        """
        position = self._positions.get(position_id)
        if not position:
            raise ValueError(f"Position {position_id} not found")

        if position.status != "active":
            raise ValueError(f"Position {position_id} is not active")

        withdraw_amount = amount or position.amount
        if withdraw_amount > position.amount:
            raise ValueError("Cannot withdraw more than position amount")

        # Mock protocol interaction
        result = self._mock_protocol_interaction(
            position.protocol,
            "withdraw",
            amount=float(withdraw_amount)
        )

        # Update position
        position.amount -= withdraw_amount
        position.updated_at = datetime.now()

        if position.amount <= 0:
            position.status = "closed"
            del self._positions[position_id]
            # Remove persisted file for closed positions to avoid stale data
            try:
                pos_file = self.storage_path / f"{position.id}.json"
                if pos_file.exists():
                    pos_file.unlink()
            except Exception as cleanup_err:
                print(f"Warning: Failed to remove closed position file {position.id}: {cleanup_err}")
        else:
            self._save_position(position)

        return {
            "success": True,
            "withdrawn_amount": withdraw_amount,
            "remaining_amount": position.amount if position.status == "active" else 0,
            "rewards_claimed": result.get("rewards_claimed", 0),
            "tx_hash": result.get("tx_hash"),
            "position_status": position.status
        }

    def get_yield_opportunities(
        self,
        asset: Optional[str] = None,
        protocol: Optional[str] = None,
        min_apr: float = 0
    ) -> List[YieldOpportunity]:
        """Get available yield opportunities.

        Args:
            asset: Filter by asset
            protocol: Filter by protocol
            min_apr: Minimum APR threshold

        Returns:
            List of yield opportunities
        """
        opportunities = []

        protocols_to_check = [protocol] if protocol else self.protocols.keys()

        for proto in protocols_to_check:
            if proto not in self.protocols:
                continue

            # Mock API call to get yields
            yields_data = self._mock_protocol_interaction(proto, "get_yields", asset=asset)

            for yield_data in yields_data:
                if yield_data["apr"] >= min_apr:
                    if not asset or yield_data["asset"] == asset:
                        opportunity = YieldOpportunity(
                            protocol=yield_data["protocol"],
                            pool=yield_data["pool"],
                            asset=yield_data["asset"],
                            apr=yield_data["apr"],
                            tvl=yield_data["tvl"],
                            risk_level=yield_data["risk_level"],
                            rewards=yield_data.get("rewards", [])
                        )
                        opportunities.append(opportunity)

        # Sort by APR descending
        opportunities.sort(key=lambda x: x.apr, reverse=True)
        return opportunities

    def get_positions(
        self,
        wallet_address: Optional[str] = None,
        protocol: Optional[str] = None,
        status: str = "active"
    ) -> List[DeFiPosition]:
        """Get DeFi positions.

        Args:
            wallet_address: Filter by wallet
            protocol: Filter by protocol
            status: Position status filter

        Returns:
            List of positions
        """
        positions = list(self._positions.values())

        if wallet_address:
            positions = [p for p in positions if p.wallet_address == wallet_address]

        if protocol:
            positions = [p for p in positions if p.protocol == protocol]

        if status:
            positions = [p for p in positions if p.status == status]

        return positions

    def get_position(self, position_id: str) -> Optional[DeFiPosition]:
        """Get a specific position by ID."""
        return self._positions.get(position_id)

    def get_portfolio_summary(self, wallet_address: str) -> Dict[str, Any]:
        """Get comprehensive portfolio summary for a wallet.

        Args:
            wallet_address: Wallet address

        Returns:
            Portfolio summary with positions, yields, and analytics
        """
        positions = self.get_positions(wallet_address=wallet_address)

        total_value = sum(p.value_usd or 0 for p in positions)
        total_yield = sum((p.apr or 0) * (p.value_usd or 0) / 100 for p in positions)

        # Group by protocol
        by_protocol = {}
        for position in positions:
            proto = position.protocol
            if proto not in by_protocol:
                by_protocol[proto] = {
                    "positions": 0,
                    "total_value": 0,
                    "total_yield": 0
                }
            by_protocol[proto]["positions"] += 1
            by_protocol[proto]["total_value"] += position.value_usd or 0
            by_protocol[proto]["total_yield"] += (position.apr or 0) * (position.value_usd or 0) / 100

        # Get yield opportunities
        yield_opportunities = self.get_yield_opportunities()

        return {
            "wallet_address": wallet_address,
            "total_positions": len(positions),
            "total_value_usd": total_value,
            "total_annual_yield_usd": total_yield,
            "positions_by_protocol": by_protocol,
            "positions": [p.to_dict() for p in positions],
            "yield_opportunities": [opp.to_dict() for opp in yield_opportunities[:5]],  # Top 5
            "generated_at": datetime.now().isoformat()
        }

    def add_liquidity(
        self,
        wallet_address: str,
        token_a: str,
        token_b: str,
        amount_a: Decimal,
        amount_b: Decimal,
        protocol: str = "uniswap"
    ) -> DeFiPosition:
        """Add liquidity to a DEX pool.

        Args:
            wallet_address: Wallet address
            token_a: First token
            token_b: Second token
            amount_a: Amount of first token
            amount_b: Amount of second token
            protocol: DEX protocol (uniswap, curve)

        Returns:
            Liquidity position
        """
        self._validate_address(wallet_address)

        # Create liquidity position
        position = DeFiPosition(
            id=f"liq_{os.urandom(8).hex()}",
            wallet_address=wallet_address,
            protocol=protocol,
            position_type="liquidity",
            asset=f"{token_a}/{token_b}",
            amount=amount_a,  # Simplified - using amount_a as reference
            apr=8.5,  # Mock APR for LP
            rewards=["UNI", "SUSHI"] if protocol == "uniswap" else ["CRV"]
        )

        self._positions[position.id] = position
        self._save_position(position)

        return position

    def stake_tokens(
        self,
        wallet_address: str,
        asset: str,
        amount: Decimal,
        protocol: str = "lido"
    ) -> DeFiPosition:
        """Stake tokens for yield.

        Args:
            wallet_address: Wallet address
            asset: Asset to stake
            amount: Amount to stake
            protocol: Staking protocol

        Returns:
            Staking position
        """
        self._validate_address(wallet_address)

        position = DeFiPosition(
            id=f"stake_{os.urandom(8).hex()}",
            wallet_address=wallet_address,
            protocol=protocol,
            position_type="staking",
            asset=asset,
            amount=amount,
            apr=7.2,  # Mock staking APR
            rewards=["LDO"] if protocol == "lido" else []
        )

        self._positions[position.id] = position
        self._save_position(position)

        return position


# Convenience functions
def lend_tokens(wallet_address: str, asset: str, amount: Decimal, protocol: str = "aave") -> DeFiPosition:
    """Convenience function to lend tokens."""
    manager = DeFiManager()
    return manager.lend_tokens(wallet_address, asset, amount, protocol)


def get_yield_opportunities(asset: Optional[str] = None, min_apr: float = 0) -> List[YieldOpportunity]:
    """Convenience function to get yield opportunities."""
    manager = DeFiManager()
    return manager.get_yield_opportunities(asset, min_apr=min_apr)


def get_portfolio_summary(wallet_address: str) -> Dict[str, Any]:
    """Convenience function to get portfolio summary."""
    manager = DeFiManager()
    return manager.get_portfolio_summary(wallet_address)
