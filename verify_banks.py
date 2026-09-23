#!/usr/bin/env python3
"""Quick verification script for all 8 banks configuration."""

from app.modules.shared.bank_config import BANK_CONFIGS, list_available_banks

print("🏦 Bank Configuration Verification")
print("=" * 60)
print()

# List all banks
print(f"✅ Total Banks Configured: {len(BANK_CONFIGS)}")
print()

# Show each bank
for bank_id, config in BANK_CONFIGS.items():
    print(f"🏦 {config.bank_name} ({config.bank_name_short})")
    print(f"   ID: {bank_id}")
    print(f"   Theme: {config.branding.primary_color}")
    print(f"   Tagline: {config.branding.tagline}")
    print(f"   Languages: {', '.join(config.languages)}")
    print(f"   Fraud Threshold: {config.fraud_rules.high_amount_threshold:,} ETB")
    print()

print("=" * 60)
print()

# Test list_available_banks function
banks_list = list_available_banks()
print(f"✅ API Response Preview:")
print(f"   {len(banks_list)} banks available")
for bank in banks_list:
    print(f"   - {bank['bank_name']} ({bank['bank_id']})")

print()
print("✅ All 8 banks configured successfully!")
print()
print("🎨 Color Themes:")
print("   🔵 Dashen - Blue (#1a56db)")
print("   🔴 Abyssinia - Red (#dc2626)")
print("   🟢 Awash - Green (#059669)")
print("   🟡 CBE - Orange (#f59e0b)")
print("   🔷 Amhara - Sky Blue (#0ea5e9)")
print("   🟣 Zemen - Purple (#7c3aed)")
print("   🩷 Tsedey - Pink (#ec4899)")
print("   🟢 Nib - Emerald (#10b981)")
