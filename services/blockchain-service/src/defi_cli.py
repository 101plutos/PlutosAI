#!/usr/bin/env python3
"""
Simple DeFi CLI

Usage:
    python defi_cli.py lend --wallet <addr> --asset ETH --amount 1.0 --protocol aave
    python defi_cli.py yields --asset ETH --min-apr 5.0
    python defi_cli.py positions --wallet <addr>
    python defi_cli.py portfolio --wallet <addr>
    python defi_cli.py withdraw --position <id> --amount 0.5
    python defi_cli.py liquidity --wallet <addr> --token-a ETH --token-b USDC --amount-a 1.0 --amount-b 2000
    python defi_cli.py stake --wallet <addr> --asset ETH --amount 5.0 --protocol lido
"""

import argparse
import sys
from decimal import Decimal
from pathlib import Path

# Add service to path
sys.path.insert(0, str(Path(__file__).parent))

from defi_manager import DeFiManager


def main():
    parser = argparse.ArgumentParser(description="Simple DeFi CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Lend tokens
    lend_parser = subparsers.add_parser("lend", help="Lend tokens")
    lend_parser.add_argument("--wallet", required=True, help="Wallet address")
    lend_parser.add_argument("--asset", required=True, help="Asset to lend")
    lend_parser.add_argument("--amount", required=True, type=float, help="Amount to lend")
    lend_parser.add_argument("--protocol", default="aave", help="Protocol (aave, compound)")

    # Get yields
    yields_parser = subparsers.add_parser("yields", help="Get yield opportunities")
    yields_parser.add_argument("--asset", help="Filter by asset")
    yields_parser.add_argument("--protocol", help="Filter by protocol")
    yields_parser.add_argument("--min-apr", type=float, default=0, help="Minimum APR")

    # Get positions
    positions_parser = subparsers.add_parser("positions", help="Get positions")
    positions_parser.add_argument("--wallet", help="Filter by wallet")
    positions_parser.add_argument("--protocol", help="Filter by protocol")
    positions_parser.add_argument("--status", default="active", help="Position status")

    # Portfolio summary
    portfolio_parser = subparsers.add_parser("portfolio", help="Get portfolio summary")
    portfolio_parser.add_argument("--wallet", required=True, help="Wallet address")

    # Withdraw tokens
    withdraw_parser = subparsers.add_parser("withdraw", help="Withdraw from position")
    withdraw_parser.add_argument("--position", required=True, help="Position ID")
    withdraw_parser.add_argument("--amount", type=float, help="Amount to withdraw (optional)")

    # Add liquidity
    liquidity_parser = subparsers.add_parser("liquidity", help="Add liquidity")
    liquidity_parser.add_argument("--wallet", required=True, help="Wallet address")
    liquidity_parser.add_argument("--token-a", required=True, help="First token")
    liquidity_parser.add_argument("--token-b", required=True, help="Second token")
    liquidity_parser.add_argument("--amount-a", required=True, type=float, help="Amount of first token")
    liquidity_parser.add_argument("--amount-b", required=True, type=float, help="Amount of second token")
    liquidity_parser.add_argument("--protocol", default="uniswap", help="DEX protocol")

    # Stake tokens
    stake_parser = subparsers.add_parser("stake", help="Stake tokens")
    stake_parser.add_argument("--wallet", required=True, help="Wallet address")
    stake_parser.add_argument("--asset", required=True, help="Asset to stake")
    stake_parser.add_argument("--amount", required=True, type=float, help="Amount to stake")
    stake_parser.add_argument("--protocol", default="lido", help="Staking protocol")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = DeFiManager("./defi_positions")

    try:
        if args.command == "lend":
            position = manager.lend_tokens(
                wallet_address=args.wallet,
                asset=args.asset,
                amount=Decimal(str(args.amount)),
                protocol=args.protocol
            )
            print("✅ Lended tokens!")
            print(f"   Position ID: {position.id}")
            print(f"   Protocol: {position.protocol}")
            print(f"   Amount: {position.amount} {position.asset}")
            print(f"   APR: {position.apr:.1f}%")
            print(f"   Value: ${position.value_usd:.2f}")

        elif args.command == "yields":
            opportunities = manager.get_yield_opportunities(
                asset=args.asset if hasattr(args, 'asset') and args.asset else None,
                protocol=args.protocol if hasattr(args, 'protocol') and args.protocol else None,
                min_apr=args.min_apr
            )
            print(f"📈 Found {len(opportunities)} yield opportunities:")
            for opp in opportunities:
                print(f"   Risk: {opp.risk_level}")

        elif args.command == "positions":
            positions = manager.get_positions(
                wallet_address=args.wallet if hasattr(args, 'wallet') and args.wallet else None,
                protocol=args.protocol if hasattr(args, 'protocol') and args.protocol else None,
                status=args.status
            )
            print(f"📋 Found {len(positions)} positions:")
            for pos in positions:
                print(f"   • {pos.position_type.title()}: {pos.amount} {pos.asset} on {pos.protocol}")
                print(f"     Value: ${pos.value_usd:.2f}")

        elif args.command == "portfolio":
            summary = manager.get_portfolio_summary(args.wallet)
            print("📊 Portfolio Summary:")
            print(f"   Positions: {summary['total_positions']}")
            print(f"   Total Value: ${summary['total_value_usd']:.2f}")
            print(f"   Protocols: {len(summary['positions_by_protocol'])}")

        elif args.command == "withdraw":
            result = manager.withdraw_tokens(
                position_id=args.position,
                amount=Decimal(str(args.amount)) if args.amount else None
            )
            print("✅ Withdrawal completed!")
            print(f"   Withdrawn: {result['withdrawn_amount']}")
            print(f"   Remaining: {result['remaining_amount']}")
            print(f"   Status: {result['position_status']}")

        elif args.command == "liquidity":
            position = manager.add_liquidity(
                wallet_address=args.wallet,
                token_a=args.token_a,
                token_b=args.token_b,
                amount_a=Decimal(str(args.amount_a)),
                amount_b=Decimal(str(args.amount_b)),
                protocol=args.protocol
            )
            print("✅ Added liquidity!")
            print(f"   Position ID: {position.id}")
            print(f"   Pair: {position.asset}")
            print(f"   Protocol: {position.protocol}")
            print(f"   Value: ${position.value_usd:.2f}")

        elif args.command == "stake":
            position = manager.stake_tokens(
                wallet_address=args.wallet,
                asset=args.asset,
                amount=Decimal(str(args.amount)),
                protocol=args.protocol
            )
            print("✅ Staked tokens!")
            print(f"   Position ID: {position.id}")
            print(f"   Asset: {position.asset}")
            print(f"   Amount: {position.amount}")
            print(f"   Protocol: {position.protocol}")
            print(f"   Value: ${position.value_usd:.2f}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
