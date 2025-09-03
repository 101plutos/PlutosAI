#!/usr/bin/env python3
"""
Clean & Simple DeFi Integration Demo

This demonstrates real DeFi functionality:
- Lending on Aave/Compound
- Yield farming opportunities
- Liquidity provision
- Staking
- Portfolio analytics

Usage:
    python defi_demo.py
"""

import sys
from decimal import Decimal
from pathlib import Path

# Add service to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from defi_manager import DeFiManager


def demo_defi_integration():
    """Demonstrate comprehensive DeFi integration."""
    print("🚀 PlutosAI DeFi Integration Demo")
    print("=" * 40)

    manager = DeFiManager("./demo_defi_positions")
    wallet_address = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"

    print(f"\n📋 Using wallet: {wallet_address}")

    # Step 1: Explore yield opportunities
    print("\n1️⃣ Exploring Yield Opportunities")
    print("-" * 30)

    opportunities = manager.get_yield_opportunities(min_apr=5.0)
    print(f"Found {len(opportunities)} yield opportunities:")

    for i, opp in enumerate(opportunities[:3], 1):  # Show top 3
        print(f"  {i}. {opp.protocol} - {opp.asset}")
        print(f"     APR: {opp.apr:.1f}%")
        print(f"     TVL: ${opp.tvl:,.0f}")
        print(f"     Risk: {opp.risk_level}")
        print(f"     Rewards: {', '.join(opp.rewards) if opp.rewards else 'None'}")
        print()

    # Step 2: Lend tokens on Aave
    print("\n2️⃣ Lending on Aave")
    print("-" * 30)

    try:
        lend_position = manager.lend_tokens(
            wallet_address=wallet_address,
            asset="USDC",
            amount=Decimal("1000"),
            protocol="aave"
        )

        print("✅ Lending position created!")
        print(f"   Position ID: {lend_position.id}")
        print(f"   Protocol: {lend_position.protocol}")
        print(f"   Asset: {lend_position.asset}")
        print(f"   Amount: ${lend_position.amount}")
        print(f"   APR: {lend_position.apr:.1f}%")
        print(f"   Value: ${lend_position.value_usd:.2f}")

    except Exception as e:
        print(f"❌ Failed to lend: {e}")
        return

    # Step 3: Lend more on Compound
    print("\n3️⃣ Lending on Compound")
    print("-" * 30)

    try:
        compound_position = manager.lend_tokens(
            wallet_address=wallet_address,
            asset="ETH",
            amount=Decimal("2"),
            protocol="compound"
        )

        print("✅ Compound position created!")
        print(f"   Position ID: {compound_position.id}")
        print(f"   Asset: {compound_position.asset}")
        print(f"   Amount: {compound_position.amount} ETH")
        print(f"   APR: {compound_position.apr:.1f}%")
        print(f"   Value: ${compound_position.value_usd:.2f}")

    except Exception as e:
        print(f"❌ Failed to lend on Compound: {e}")

    # Step 4: Add liquidity to Uniswap
    print("\n4️⃣ Adding Liquidity to Uniswap")
    print("-" * 30)

    try:
        liq_position = manager.add_liquidity(
            wallet_address=wallet_address,
            token_a="ETH",
            token_b="USDC",
            amount_a=Decimal("1"),
            amount_b=Decimal("2000"),
            protocol="uniswap"
        )

        print("✅ Liquidity position created!")
        print(f"   Position ID: {liq_position.id}")
        print(f"   Pair: {liq_position.asset}")
        print(f"   Protocol: {liq_position.protocol}")
        print(f"   APR: {liq_position.apr:.1f}%")
        print(f"   Rewards: {', '.join(liq_position.rewards)}")
        print(f"   Value: ${liq_position.value_usd:.2f}")

    except Exception as e:
        print(f"❌ Failed to add liquidity: {e}")

    # Step 5: Stake ETH
    print("\n5️⃣ Staking ETH")
    print("-" * 30)

    try:
        stake_position = manager.stake_tokens(
            wallet_address=wallet_address,
            asset="ETH",
            amount=Decimal("5"),
            protocol="lido"
        )

        print("✅ Staking position created!")
        print(f"   Position ID: {stake_position.id}")
        print(f"   Asset: {stake_position.asset}")
        print(f"   Amount: {stake_position.amount} ETH")
        print(f"   APR: {stake_position.apr:.1f}%")
        print(f"   Rewards: {', '.join(stake_position.rewards)}")
        print(f"   Value: ${stake_position.value_usd:.2f}")

    except Exception as e:
        print(f"❌ Failed to stake: {e}")

    # Step 6: Portfolio summary
    print("\n6️⃣ Portfolio Summary")
    print("-" * 30)

    try:
        summary = manager.get_portfolio_summary(wallet_address)

        print("📊 Portfolio Overview:")
        print(f"   Total Positions: {summary['total_positions']}")
        print(f"   Total Value: ${summary['total_value_usd']:.2f}")
        print(f"   Annual Yield: ${summary['total_annual_yield_usd']:.2f}")
        print(f"   Generated: {summary['generated_at'][:19]}")

        print("\n   Breakdown by Protocol:")
        for protocol, data in summary['positions_by_protocol'].items():
            print(f"     • {protocol}: {data['positions']} positions")
            print(f"       Value: ${data['total_value']:.2f}")
            print(f"       Yield: ${data['total_yield']:.2f}")
            print()

        print("   Top Yield Opportunities:")
        for i, opp in enumerate(summary['yield_opportunities'][:3], 1):
            print(f"     {i}. {opp['protocol']} - {opp['asset']} ({opp['apr']:.1f}% APR)")

    except Exception as e:
        print(f"❌ Failed to get portfolio summary: {e}")

    # Step 7: Withdraw from a position
    print("\n7️⃣ Withdrawing from Position")
    print("-" * 30)

    try:
        if 'lend_position' in locals():
            result = manager.withdraw_tokens(
                position_id=lend_position.id,
                amount=Decimal("500")  # Partial withdrawal
            )

            print("✅ Withdrawal completed!")
            print(f"   Withdrawn: ${result['withdrawn_amount']}")
            print(f"   Remaining: ${result['remaining_amount']}")
            print(f"   Rewards: ${result['rewards_claimed']}")
            print(f"   Status: {result['position_status']}")

    except Exception as e:
        print(f"❌ Failed to withdraw: {e}")

    # Step 8: Show all positions
    print("\n8️⃣ All Positions")
    print("-" * 30)

    try:
        all_positions = manager.get_positions(wallet_address=wallet_address)
        print(f"📋 Total positions: {len(all_positions)}")

        for i, pos in enumerate(all_positions, 1):
            print(f"  {i}. {pos.position_type.title()} - {pos.asset}")
            print(f"     Protocol: {pos.protocol}")
            print(f"     Amount: {pos.amount}")
            print(f"     APR: {pos.apr:.1f}%" if pos.apr else "     APR: N/A")
            print(f"     Value: ${pos.value_usd:.2f}")
            print(f"     Status: {pos.status}")
            print()

    except Exception as e:
        print(f"❌ Failed to get positions: {e}")

    print("\n🎊 DeFi Integration Demo Complete!")
    print("\n💡 DeFi Features Demonstrated:")
    print("   • Lending on Aave & Compound")
    print("   • Yield opportunity discovery")
    print("   • Liquidity provision on Uniswap")
    print("   • ETH staking on Lido")
    print("   • Portfolio analytics")
    print("   • Position management")
    print("\n📁 Check ./demo_defi_positions/ for stored positions!")


def demo_yield_comparison():
    """Compare yield opportunities across protocols."""
    print("\n🔍 Yield Comparison Demo")
    print("=" * 30)

    manager = DeFiManager()

    # Compare ETH yields
    print("ETH Yield Opportunities:")
    eth_yields = manager.get_yield_opportunities(asset="ETH", min_apr=3.0)
    for opp in eth_yields:
        print(f"   • {opp.protocol}: {opp.apr:.1f}% APR")
        print(f"     Risk: {opp.risk_level}")

    # Compare USDC yields
    print("\nUSDC Yield Opportunities:")
    usdc_yields = manager.get_yield_opportunities(asset="USDC", min_apr=2.0)
    for opp in usdc_yields:
        print(f"   • {opp.protocol}: {opp.apr:.1f}% APR")
        print(f"     Risk: {opp.risk_level}")

    print("\n💡 Best opportunities are sorted by APR!")


if __name__ == "__main__":
    # Clean up any previous demo data
    import shutil
    if Path("./demo_defi_positions").exists():
        shutil.rmtree("./demo_defi_positions")

    demo_defi_integration()
    demo_yield_comparison()
            print()

    except Exception as e:
        print(f"❌ Failed to get positions: {e}")

    print("\n🎊 DeFi Integration Demo Complete!")
    print("\n💡 DeFi Features Demonstrated:")
    print("   • Lending on Aave & Compound")
    print("   • Yield opportunity discovery")
    print("   • Liquidity provision on Uniswap")
    print("   • ETH staking")
    print("   • Portfolio analytics")
    print("   • Position management (withdrawals)")
    print("   • Real-time value tracking")
    print("\n📁 Check ./demo_defi_positions/ for stored positions!")


def demo_yield_comparison():
    """Compare yield opportunities across protocols."""
    print("\n🔍 Yield Comparison Demo")
    print("=" * 30)

    manager = DeFiManager()

    # Compare ETH yields
    print("ETH Yield Opportunities:")
    eth_yields = manager.get_yield_opportunities(asset="ETH", min_apr=3.0)
    for opp in eth_yields:
        print(".1f"            print(f"   • Risk: {opp.risk_level}")

    # Compare USDC yields
    print("\nUSDC Yield Opportunities:")
    usdc_yields = manager.get_yield_opportunities(asset="USDC", min_apr=2.0)
    for opp in usdc_yields:
        print(".1f"            print(f"   • Risk: {opp.risk_level}")

    print("\n💡 Best opportunities are sorted by APR!")


if __name__ == "__main__":
    # Clean up any previous demo data
    import shutil
    if Path("./demo_defi_positions").exists():
        shutil.rmtree("./demo_defi_positions")

    demo_defi_integration()
    demo_yield_comparison()
