#!/usr/bin/env python3
"""
Simple Wallet CLI

Usage:
    python simple_cli.py create --client demo --name "My Wallet" --signers 0x123...,0x456... --required 2
    python simple_cli.py list --client demo
    python simple_cli.py transaction --wallet <id> --to 0x789... --amount 0.1
    python simple_cli.py sign --transaction <tx_id> --signer 0x123... --signature <sig>
    python simple_cli.py status --wallet <id>
"""

import argparse
import sys
from decimal import Decimal
from pathlib import Path

# Add service to path
sys.path.insert(0, str(Path(__file__).parent))

from simple_wallet import WalletManager


def main():
    parser = argparse.ArgumentParser(description="Simple Multi-Signature Wallet CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Create wallet
    create_parser = subparsers.add_parser("create", help="Create wallet")
    create_parser.add_argument("--client", required=True, help="Client ID")
    create_parser.add_argument("--name", required=True, help="Wallet name")
    create_parser.add_argument("--signers", required=True, help="Signer addresses (comma-separated)")
    create_parser.add_argument("--required", type=int, default=2, help="Required signatures")

    # List wallets
    list_parser = subparsers.add_parser("list", help="List wallets")
    list_parser.add_argument("--client", help="Filter by client ID")

    # Create transaction
    tx_parser = subparsers.add_parser("transaction", help="Create transaction")
    tx_parser.add_argument("--wallet", required=True, help="Wallet ID")
    tx_parser.add_argument("--to", required=True, help="Recipient address")
    tx_parser.add_argument("--amount", required=True, type=Decimal, help="Amount")
    tx_parser.add_argument("--asset", default="ETH", help="Asset symbol")

    # Sign transaction
    sign_parser = subparsers.add_parser("sign", help="Sign transaction")
    sign_parser.add_argument("--transaction", required=True, help="Transaction ID")
    sign_parser.add_argument("--signer", required=True, help="Signer address")
    sign_parser.add_argument("--signature", required=True, help="Signature")

    # Wallet status
    status_parser = subparsers.add_parser("status", help="Wallet status")
    status_parser.add_argument("--wallet", required=True, help="Wallet ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = WalletManager("./wallets")

    try:
        if args.command == "create":
            signers = [s.strip() for s in args.signers.split(",")]
            wallet = manager.create_wallet(
                client_id=args.client,
                name=args.name,
                signer_addresses=signers,
                required_signatures=args.required
            )
            print("✅ Wallet created!"            print(f"   ID: {wallet.id}")
            print(f"   Address: {wallet.address}")

        elif args.command == "list":
            wallets = manager.list_wallets(args.client if hasattr(args, 'client') and args.client else None)
            if not wallets:
                print("No wallets found.")
                return

            print(f"📋 Wallets ({len(wallets)}):")
            for wallet in wallets:
                print(f"   • {wallet.name} ({wallet.id}) - {len(wallet.signers)} signers")

        elif args.command == "transaction":
            tx = manager.create_transaction(
                wallet_id=args.wallet,
                to_address=args.to,
                amount=args.amount,
                asset=args.asset
            )
            print("✅ Transaction created!"            print(f"   ID: {tx.id}")
            print(f"   Status: {tx.status}")

        elif args.command == "sign":
            result = manager.sign_transaction(
                transaction_id=args.transaction,
                signer_address=args.signer,
                signature=args.signature
            )
            print(f"✅ {result['message']}")

        elif args.command == "status":
            status = manager.get_wallet_status(args.wallet)
            wallet = status['wallet']
            print(f"📋 {wallet['name']}")
            print(f"   Address: {wallet['address']}")
            print(f"   Status: {wallet['status']}")
            print(f"   Transactions: {status['summary']['total_transactions']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
