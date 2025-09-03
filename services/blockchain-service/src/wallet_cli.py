#!/usr/bin/env python3
"""
Clean & Easy Multi-Signature Wallet CLI

A simple command-line interface for managing multi-signature wallets.

Usage:
    python wallet_cli.py create --client-id family-smith --name "Family ETH" --blockchain ethereum --signers 0x123...,0x456... --required 2
    python wallet_cli.py list --client-id family-smith
    python wallet_cli.py transaction --wallet-id <id> --to 0x789... --amount 0.1
    python wallet_cli.py sign --wallet-id <id> --transaction-id <tx_id> --signer 0x123... --signature <sig>
    python wallet_cli.py status --wallet-id <id>

Environment Variables:
    BLOCKCHAIN_SERVICE_URL: Service URL (default: http://localhost:8006)
    API_TOKEN: Authentication token (default: demo-token)
"""

import asyncio
import argparse
import os
import sys
from decimal import Decimal
from typing import List, Optional

import httpx


class WalletCLI:
    """Clean and easy wallet management CLI."""

    def __init__(self, base_url: str = None, token: str = None):
        self.base_url = base_url or os.getenv("BLOCKCHAIN_SERVICE_URL", "http://localhost:8006")
        self.token = token or os.getenv("API_TOKEN", "demo-token")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.token}"}
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def create_wallet(
        self,
        client_id: str,
        name: str,
        blockchain: str,
        signers: List[str],
        required: int = 2
    ):
        """Create a new multi-signature wallet."""
        url = "/wallets/create-multisig"
        payload = {
            "client_id": client_id,
            "name": name,
            "blockchain": blockchain,
            "signer_addresses": signers,
            "required_signatures": required
        }

        print(f"🚀 Creating wallet '{name}' on {blockchain}")
        print(f"   Signers: {len(signers)}")
        print(f"   Required signatures: {required}")

        response = await self.client.post(url, json=payload)

        if response.status_code == 200:
            wallet = response.json()
            print("✅ Wallet created successfully!"            print(f"   ID: {wallet['id']}")
            print(f"   Address: {wallet['address']}")
            print(f"   Status: {wallet['status']}")
        else:
            print(f"❌ Failed to create wallet: {response.text}")

    async def list_wallets(self, client_id: Optional[str] = None):
        """List wallets."""
        url = "/wallets"
        params = {}
        if client_id:
            params["client_id"] = client_id

        response = await self.client.get(url, params=params)

        if response.status_code == 200:
            wallets = response.json()
            if not wallets:
                print("No wallets found.")
                return

            print(f"📋 Found {len(wallets)} wallet(s):")
            print()

            for wallet in wallets:
                print(f"🔑 {wallet['name']}")
                print(f"   ID: {wallet['id']}")
                print(f"   Blockchain: {wallet['blockchain']}")
                print(f"   Address: {wallet['address']}")
                print(f"   Signers: {wallet['total_signers']}")
                print(f"   Required: {wallet['required_signatures']}")
                print(f"   Status: {wallet['status']}")
                print()
        else:
            print(f"❌ Failed to list wallets: {response.text}")

    async def create_transaction(
        self,
        wallet_id: str,
        to_address: str,
        amount: Decimal,
        asset: str = "ETH"
    ):
        """Create a transaction."""
        url = f"/wallets/{wallet_id}/transactions"
        payload = {
            "to_address": to_address,
            "amount": str(amount),
            "asset_symbol": asset
        }

        print(f"💸 Creating transaction")
        print(f"   Wallet: {wallet_id}")
        print(f"   To: {to_address}")
        print(f"   Amount: {amount} {asset}")

        response = await self.client.post(url, json=payload)

        if response.status_code == 200:
            tx = response.json()
            print("✅ Transaction created!"            print(f"   ID: {tx['id']}")
            print(f"   Status: {tx['status']}")
            print(".1f"        else:
            print(f"❌ Failed to create transaction: {response.text}")

    async def sign_transaction(
        self,
        wallet_id: str,
        transaction_id: str,
        signer_address: str,
        signature: str
    ):
        """Sign a transaction."""
        url = f"/wallets/{wallet_id}/transactions/{transaction_id}/sign"
        payload = {
            "signature": signature,
            "signer_address": signer_address
        }

        print(f"✍️  Signing transaction {transaction_id}")
        print(f"   Signer: {signer_address}")

        response = await self.client.post(url, json=payload)

        if response.status_code == 200:
            result = response.json()
            if result["success"]:
                print("✅ Signature accepted!"                print(f"   Status: {result['status']}")
                print(".1f"                print(f"   Message: {result['message']}")
            else:
                print("❌ Signature rejected!")
        else:
            print(f"❌ Failed to sign transaction: {response.text}")

    async def wallet_status(self, wallet_id: str):
        """Get wallet status."""
        url = f"/wallets/{wallet_id}"

        response = await self.client.get(url)

        if response.status_code == 200:
            wallet = response.json()
            print(f"🔑 {wallet['name']}")
            print(f"   ID: {wallet['id']}")
            print(f"   Blockchain: {wallet['blockchain']}")
            print(f"   Address: {wallet['address']}")
            print(f"   Status: {wallet['status']}")
            print(f"   Deployed: {wallet['is_deployed']}")
            print(f"   Signers: {wallet['total_signers']}")
            print(f"   Required: {wallet['required_signatures']}")

            signers = wallet.get('signers', [])
            if signers:
                print("   Signer addresses:")
                for signer in signers:
                    print(f"     - {signer['address']} ({signer['name'] or 'Unnamed'})")

            pending = wallet.get('pending_transactions', [])
            if pending:
                print(f"   Pending transactions: {len(pending)}")
                for tx in pending:
                    print(f"     - {tx['id']}: {tx['amount']} {tx['asset_symbol']} ({tx['signature_progress']:.1f}%)")
        else:
            print(f"❌ Failed to get wallet status: {response.text}")

    def generate_mock_signature(self, transaction_id: str, signer_address: str) -> str:
        """Generate mock signature for demo purposes."""
        import hashlib
        import secrets

        data = f"{transaction_id}:{signer_address}:{secrets.token_hex(16)}"
        return hashlib.sha256(data.encode()).hexdigest()[:130]


def create_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Clean & Easy Multi-Signature Wallet CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a 2-of-3 wallet
  python wallet_cli.py create --client-id family-smith --name "Family ETH" --blockchain ethereum --signers 0x123...,0x456...,0x789... --required 2

  # List wallets for a client
  python wallet_cli.py list --client-id family-smith

  # Create a transaction
  python wallet_cli.py transaction --wallet-id <id> --to 0xabc... --amount 0.5

  # Sign a transaction (with mock signature)
  python wallet_cli.py sign --wallet-id <id> --transaction-id <tx_id> --signer 0x123...

  # Check wallet status
  python wallet_cli.py status --wallet-id <id>
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create wallet command
    create_parser = subparsers.add_parser("create", help="Create a new multi-signature wallet")
    create_parser.add_argument("--client-id", required=True, help="Client identifier")
    create_parser.add_argument("--name", required=True, help="Wallet name")
    create_parser.add_argument("--blockchain", required=True, help="Target blockchain")
    create_parser.add_argument("--signers", required=True, help="Comma-separated signer addresses")
    create_parser.add_argument("--required", type=int, default=2, help="Required signatures")

    # List wallets command
    list_parser = subparsers.add_parser("list", help="List wallets")
    list_parser.add_argument("--client-id", help="Filter by client ID")

    # Create transaction command
    tx_parser = subparsers.add_parser("transaction", help="Create a transaction")
    tx_parser.add_argument("--wallet-id", required=True, help="Wallet ID")
    tx_parser.add_argument("--to", required=True, help="Recipient address")
    tx_parser.add_argument("--amount", required=True, type=Decimal, help="Amount to send")
    tx_parser.add_argument("--asset", default="ETH", help="Asset symbol")

    # Sign transaction command
    sign_parser = subparsers.add_parser("sign", help="Sign a transaction")
    sign_parser.add_argument("--wallet-id", required=True, help="Wallet ID")
    sign_parser.add_argument("--transaction-id", required=True, help="Transaction ID")
    sign_parser.add_argument("--signer", required=True, help="Signer address")
    sign_parser.add_argument("--signature", help="Transaction signature (auto-generated if not provided)")

    # Wallet status command
    status_parser = subparsers.add_parser("status", help="Get wallet status")
    status_parser.add_argument("--wallet-id", required=True, help="Wallet ID")

    return parser


async def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    async with WalletCLI() as cli:
        if args.command == "create":
            signers = [s.strip() for s in args.signers.split(",")]
            await cli.create_wallet(
                client_id=args.client_id,
                name=args.name,
                blockchain=args.blockchain,
                signers=signers,
                required=args.required
            )

        elif args.command == "list":
            await cli.list_wallets(client_id=getattr(args, 'client_id', None))

        elif args.command == "transaction":
            await cli.create_transaction(
                wallet_id=args.wallet_id,
                to_address=args.to,
                amount=args.amount,
                asset=args.asset
            )

        elif args.command == "sign":
            signature = args.signature
            if not signature:
                # Generate mock signature for demo
                signature = cli.generate_mock_signature(args.transaction_id, args.signer)

            await cli.sign_transaction(
                wallet_id=args.wallet_id,
                transaction_id=args.transaction_id,
                signer_address=args.signer,
                signature=signature
            )

        elif args.command == "status":
            await cli.wallet_status(args.wallet_id)

        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
