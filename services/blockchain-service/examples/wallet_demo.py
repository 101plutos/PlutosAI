#!/usr/bin/env python3
"""
Clean and Easy Multi-Signature Wallet Demo

This script demonstrates how to create and manage multi-signature wallets
using the PlutosAI blockchain service. It's designed to be simple and easy
to understand and use.

Requirements:
- Python 3.11+
- httpx (pip install httpx)

Usage:
    python wallet_demo.py
"""

import asyncio
import json
from decimal import Decimal
from typing import Dict, List, Optional

import httpx


class WalletDemo:
    """Clean and easy wallet management demo."""

    def __init__(self, base_url: str = "http://localhost:8006"):
        """Initialize with blockchain service URL."""
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            headers={"Authorization": "Bearer demo-token"}
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
        signer_addresses: List[str],
        required_signatures: int = 2
    ) -> Dict:
        """Create a new multi-signature wallet.

        Args:
            client_id: Client identifier
            name: Wallet name
            blockchain: Target blockchain (ethereum, polygon, etc.)
            signer_addresses: List of signer addresses
            required_signatures: Number of signatures required

        Returns:
            Wallet creation response
        """
        url = f"{self.base_url}/wallets/create-multisig"
        payload = {
            "client_id": client_id,
            "name": name,
            "blockchain": blockchain,
            "signer_addresses": signer_addresses,
            "required_signatures": required_signatures
        }

        print(f"🚀 Creating wallet '{name}' on {blockchain}...")
        print(f"   Signers: {len(signer_addresses)}")
        print(f"   Required signatures: {required_signatures}")

        response = await self.client.post(url, json=payload)
        response.raise_for_status()

        wallet = response.json()
        print(f"✅ Wallet created successfully!")
        print(f"   Wallet ID: {wallet['id']}")
        print(f"   Address: {wallet['address']}")
        print()

        return wallet

    async def get_wallet_summary(self, wallet_id: str) -> Dict:
        """Get comprehensive wallet information."""
        url = f"{self.base_url}/wallets/{wallet_id}"

        response = await self.client.get(url)
        response.raise_for_status()

        return response.json()

    async def create_transaction(
        self,
        wallet_id: str,
        to_address: str,
        amount: Decimal,
        asset_symbol: str = "ETH"
    ) -> Dict:
        """Create a transaction requiring multi-signature approval.

        Args:
            wallet_id: Wallet identifier
            to_address: Recipient address
            amount: Amount to send
            asset_symbol: Asset to send (default: ETH)

        Returns:
            Transaction creation response
        """
        url = f"{self.base_url}/wallets/{wallet_id}/transactions"
        payload = {
            "to_address": to_address,
            "amount": str(amount),
            "asset_symbol": asset_symbol
        }

        print(f"💸 Creating transaction...")
        print(f"   From wallet: {wallet_id}")
        print(f"   To: {to_address}")
        print(f"   Amount: {amount} {asset_symbol}")

        response = await self.client.post(url, json=payload)
        response.raise_for_status()

        transaction = response.json()
        print(f"✅ Transaction created!")
        print(f"   Transaction ID: {transaction['id']}")
        print(f"   Status: {transaction['status']}")
        print(f"   Progress: {transaction['signature_progress']:.1f}%")
        print()

        return transaction

    async def sign_transaction(
        self,
        wallet_id: str,
        transaction_id: str,
        signature: str,
        signer_address: str
    ) -> Dict:
        """Sign a pending transaction.

        Args:
            wallet_id: Wallet identifier
            transaction_id: Transaction identifier
            signature: Transaction signature
            signer_address: Address of the signer

        Returns:
            Signing response with status
        """
        url = f"{self.base_url}/wallets/{wallet_id}/transactions/{transaction_id}/sign"
        payload = {
            "signature": signature,
            "signer_address": signer_address
        }

        print(f"✍️  Signing transaction {transaction_id}...")
        print(f"   Signer: {signer_address}")

        response = await self.client.post(url, json=payload)
        response.raise_for_status()

        result = response.json()
        print(f"✅ Signature {'accepted' if result['success'] else 'rejected'}!")
        print(f"   Status: {result['status']}")
        print(f"   Progress: {result['signature_progress']:.1f}%")
        print(f"   Message: {result['message']}")
        print()

        return result

    async def add_signer(
        self,
        wallet_id: str,
        signer_address: str,
        signer_name: Optional[str] = None
    ) -> Dict:
        """Add a new signer to the wallet."""
        url = f"{self.base_url}/wallets/{wallet_id}/signers"
        payload = {
            "signer_address": signer_address,
            "signer_name": signer_name
        }

        print(f"👥 Adding signer to wallet {wallet_id}...")
        print(f"   Address: {signer_address}")
        if signer_name:
            print(f"   Name: {signer_name}")

        response = await self.client.post(url, json=payload)
        response.raise_for_status()

        result = response.json()
        print(f"✅ Signer added successfully!")
        print()

        return result

    async def list_wallets(self, client_id: Optional[str] = None) -> List[Dict]:
        """List wallets with optional client filter."""
        url = f"{self.base_url}/wallets"
        params = {}
        if client_id:
            params["client_id"] = client_id

        response = await self.client.get(url, params=params)
        response.raise_for_status()

        return response.json()

    def generate_mock_signature(self, transaction_id: str, signer_address: str) -> str:
        """Generate a mock signature for demo purposes.

        In production, this would use actual cryptographic signing.
        """
        import hashlib
        import secrets

        # Create a deterministic mock signature based on inputs
        data = f"{transaction_id}:{signer_address}:{secrets.token_hex(16)}"
        return hashlib.sha256(data.encode()).hexdigest()[:130]  # Mock signature length


async def main():
    """Demonstrate the complete wallet management workflow."""

    print("🔐 PlutosAI Multi-Signature Wallet Demo")
    print("=" * 50)

    async with WalletDemo() as demo:

        # Step 1: Create a multi-signature wallet
        print("\n1️⃣ Creating Multi-Signature Wallet")
        print("-" * 30)

        signer_addresses = [
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",  # Family member 1
            "0x1234567890123456789012345678901234567890",  # Family member 2
            "0x0987654321098765432109876543210987654321",  # Family member 3
        ]

        wallet = await demo.create_wallet(
            client_id="family-smith",
            name="Smith Family ETH Wallet",
            blockchain="ethereum",
            signer_addresses=signer_addresses,
            required_signatures=2
        )

        wallet_id = wallet["id"]

        # Step 2: Add an additional signer
        print("\n2️⃣ Adding Additional Signer")
        print("-" * 30)

        await demo.add_signer(
            wallet_id=wallet_id,
            signer_address="0xABCDEF1234567890ABCDEF1234567890ABCDEF12",
            signer_name="Family Trustee"
        )

        # Step 3: Create a transaction
        print("\n3️⃣ Creating Transaction")
        print("-" * 30)

        transaction = await demo.create_transaction(
            wallet_id=wallet_id,
            to_address="0xDEADBEEF1234567890DEADBEEF1234567890DEAD",
            amount=Decimal("0.1"),
            asset_symbol="ETH"
        )

        transaction_id = transaction["id"]

        # Step 4: Sign the transaction with multiple signers
        print("\n4️⃣ Multi-Signature Approval Process")
        print("-" * 30)

        # First signature
        signature1 = demo.generate_mock_signature(transaction_id, signer_addresses[0])
        await demo.sign_transaction(
            wallet_id=wallet_id,
            transaction_id=transaction_id,
            signature=signature1,
            signer_address=signer_addresses[0]
        )

        # Second signature (required for 2-of-3 wallet)
        signature2 = demo.generate_mock_signature(transaction_id, signer_addresses[1])
        result = await demo.sign_transaction(
            wallet_id=wallet_id,
            transaction_id=transaction_id,
            signature=signature2,
            signer_address=signer_addresses[1]
        )

        # Step 5: Check final status
        print("\n5️⃣ Final Status Check")
        print("-" * 30)

        if result["is_fully_signed"]:
            print("🎉 Transaction is fully signed and ready for blockchain!")
            print(f"   Status: {result['status']}")
            print("   The transaction can now be broadcast to the network.")
        else:
            remaining = result["required_signatures"] - result["current_signatures"]
            print(f"⏳ Transaction needs {remaining} more signature(s)")

        # Step 6: Show wallet summary
        print("\n6️⃣ Wallet Summary")
        print("-" * 30)

        summary = await demo.get_wallet_summary(wallet_id)
        print(f"Wallet: {summary['name']}")
        print(f"Blockchain: {summary['blockchain']}")
        print(f"Address: {summary['address']}")
        print(f"Status: {summary['status']}")
        print(f"Signers: {summary['total_signers']}")
        print(f"Required Signatures: {summary['required_signatures']}")
        print(f"Pending Transactions: {summary['pending_transactions_count']}")

        if summary["pending_transactions"]:
            print("\nPending Transactions:")
            for tx in summary["pending_transactions"]:
                print(f"  - {tx['id']}: {tx['amount']} {tx['asset_symbol']} → {tx['to_address'][:10]}...")
                print(f"    Progress: {tx['signature_progress']:.1f}%")

    print("\n🎊 Demo completed successfully!")
    print("\n💡 Key Features Demonstrated:")
    print("   • Easy wallet creation with multiple signers")
    print("   • Simple transaction creation")
    print("   • Clean multi-signature approval process")
    print("   • Real-time status tracking")
    print("   • Comprehensive wallet management")


if __name__ == "__main__":
    asyncio.run(main())
