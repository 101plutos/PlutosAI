"""Tests for the simple wallet system."""

import tempfile
import shutil
from decimal import Decimal
from pathlib import Path

import pytest

from src.simple_wallet import WalletManager, MultiSigWallet


class TestMultiSigWallet:
    """Test the multi-signature wallet functionality."""

    def test_wallet_creation(self):
        """Test creating a wallet."""
        signers = ["0x742d35Cc6634C0532925a3b844Bc454e4438f44e", "0x123..."]
        wallet = MultiSigWallet(
            id="test-wallet",
            client_id="test-client",
            name="Test Wallet",
            signers=[{"address": addr, "name": f"Signer {i+1}"} for i, addr in enumerate(signers)],
            required_signatures=2
        )

        assert wallet.id == "test-wallet"
        assert wallet.name == "Test Wallet"
        assert wallet.required_signatures == 2
        assert len(wallet.signers) == 2

    def test_wallet_address_generation(self):
        """Test deterministic address generation."""
        wallet = MultiSigWallet(
            id="test-wallet",
            client_id="test-client",
            name="Test Wallet",
            signers=[{"address": "0x123...", "name": "Signer 1"}],
            required_signatures=1
        )

        # Address should be deterministic
        assert wallet.address.startswith("0x")
        assert len(wallet.address) == 42

    def test_transaction_creation(self):
        """Test creating transactions."""
        wallet = MultiSigWallet(
            id="test-wallet",
            client_id="test-client",
            name="Test Wallet",
            signers=[{"address": "0x123...", "name": "Signer 1"}],
            required_signatures=1
        )

        tx = wallet.create_transaction(
            to_address="0x456...",
            amount=Decimal("1.0"),
            asset="ETH"
        )

        assert tx.id.startswith("tx_")
        assert tx.to_address == "0x456..."
        assert tx.amount == Decimal("1.0")
        assert tx.asset == "ETH"
        assert tx.status == "pending"
        assert tx.signature_progress == 0.0

    def test_transaction_signing(self):
        """Test transaction signing."""
        wallet = MultiSigWallet(
            id="test-wallet",
            client_id="test-client",
            name="Test Wallet",
            signers=[
                {"address": "0x123...", "name": "Signer 1"},
                {"address": "0x456...", "name": "Signer 2"}
            ],
            required_signatures=2
        )

        tx = wallet.create_transaction("0x789...", Decimal("1.0"))

        # First signature
        success = wallet.sign_transaction(tx.id, "sig1", "0x123...")
        assert success
        assert tx.current_signatures == 1
        assert tx.signature_progress == 50.0

        # Second signature (completes transaction)
        success = wallet.sign_transaction(tx.id, "sig2", "0x456...")
        assert success
        assert tx.current_signatures == 2
        assert tx.signature_progress == 100.0
        assert tx.status == "signed"

    def test_invalid_signer(self):
        """Test signing with invalid signer."""
        wallet = MultiSigWallet(
            id="test-wallet",
            client_id="test-client",
            name="Test Wallet",
            signers=[{"address": "0x123...", "name": "Signer 1"}],
            required_signatures=1
        )

        tx = wallet.create_transaction("0x789...", Decimal("1.0"))

        # Try to sign with unauthorized address
        with pytest.raises(ValueError, match="Unauthorized signer"):
            wallet.sign_transaction(tx.id, "sig", "0x999...")

    def test_duplicate_signatures(self):
        """Test preventing duplicate signatures."""
        wallet = MultiSigWallet(
            id="test-wallet",
            client_id="test-client",
            name="Test Wallet",
            signers=[{"address": "0x123...", "name": "Signer 1"}],
            required_signatures=1
        )

        tx = wallet.create_transaction("0x789...", Decimal("1.0"))

        # First signature should work
        success = wallet.sign_transaction(tx.id, "sig1", "0x123...")
        assert success

        # Second signature should fail
        success = wallet.sign_transaction(tx.id, "sig2", "0x123...")
        assert not success


class TestWalletManager:
    """Test the wallet manager."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = WalletManager(self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_create_wallet(self):
        """Test creating wallet through manager."""
        wallet = self.manager.create_wallet(
            client_id="test-client",
            name="Test Wallet",
            signer_addresses=["0x123...", "0x456..."],
            required_signatures=2
        )

        assert wallet.client_id == "test-client"
        assert wallet.name == "Test Wallet"
        assert wallet.required_signatures == 2
        assert len(wallet.signers) == 2

        # Check persistence
        loaded_wallet = self.manager.get_wallet(wallet.id)
        assert loaded_wallet is not None
        assert loaded_wallet.id == wallet.id

    def test_list_wallets(self):
        """Test listing wallets."""
        # Create multiple wallets
        wallet1 = self.manager.create_wallet("client1", "Wallet 1", ["0x123..."])
        wallet2 = self.manager.create_wallet("client2", "Wallet 2", ["0x456..."])
        wallet3 = self.manager.create_wallet("client1", "Wallet 3", ["0x789..."])

        # List all
        all_wallets = self.manager.list_wallets()
        assert len(all_wallets) == 3

        # List by client
        client1_wallets = self.manager.list_wallets("client1")
        assert len(client1_wallets) == 2
        assert all(w.client_id == "client1" for w in client1_wallets)

    def test_wallet_validation(self):
        """Test wallet creation validation."""
        # Too few signers
        with pytest.raises(ValueError, match="Need at least"):
            self.manager.create_wallet("client", "Wallet", ["0x123..."], required_signatures=2)

        # Invalid address
        with pytest.raises(ValueError, match="Invalid Ethereum address"):
            self.manager.create_wallet("client", "Wallet", ["invalid-address"])

        # Duplicate addresses
        with pytest.raises(ValueError, match="Duplicate signer addresses"):
            self.manager.create_wallet("client", "Wallet", ["0x123...", "0x123..."])

    def test_transaction_workflow(self):
        """Test complete transaction workflow."""
        # Create wallet
        wallet = self.manager.create_wallet(
            "test-client",
            "Test Wallet",
            ["0x123...", "0x456..."],
            required_signatures=2
        )

        # Create transaction
        tx = self.manager.create_transaction(
            wallet.id,
            "0x789...",
            Decimal("1.0")
        )

        # Sign with first signer
        result1 = self.manager.sign_transaction(tx.id, "0x123...", "sig1")
        assert result1["current_signatures"] == 1
        assert result1["is_fully_signed"] == False

        # Sign with second signer (completes)
        result2 = self.manager.sign_transaction(tx.id, "0x456...", "sig2")
        assert result2["current_signatures"] == 2
        assert result2["is_fully_signed"] == True
        assert "completed" in result2["message"].lower()

    def test_wallet_status(self):
        """Test getting wallet status."""
        wallet = self.manager.create_wallet("client", "Wallet", ["0x123..."])

        status = self.manager.get_wallet_status(wallet.id)

        assert "wallet" in status
        assert "summary" in status
        assert status["wallet"]["id"] == wallet.id
        assert status["summary"]["total_transactions"] == 0


if __name__ == "__main__":
    # Run simple validation
    print("🧪 Running simple wallet tests...")

    try:
        # Test basic functionality
        manager = WalletManager("./test_wallets")

        wallet = manager.create_wallet(
            "test-client",
            "Test Wallet",
            ["0x742d35Cc6634C0532925a3b844Bc454e4438f44e", "0x123..."],
            required_signatures=2
        )
        print(f"✅ Created wallet: {wallet.id}")

        tx = manager.create_transaction(wallet.id, "0x456...", Decimal("0.5"))
        print(f"✅ Created transaction: {tx.id}")

        result = manager.sign_transaction(tx.id, "0x742d35Cc6634C0532925a3b844Bc454e4438f44e", "test_sig")
        print(f"✅ Signed transaction: {result['message']}")

        print("🎊 All tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        exit(1)
