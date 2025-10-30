#!/usr/bin/env python3
"""
Comprehensive Audit: "Full Event Duplication" Bug Impact

This script audits all revenue calculations across the codebase to identify
where the "Full event duplication" bug has inflated figures.

Bug Description:
- CourtReserve check-in records show full program price on EVERY attendance
- Customers pay once but price appears multiple times in check-ins table
- This inflates revenue calculations by factor of # of sessions attended

Author: Claude Code (Anthropic)
Date: October 29, 2025
"""

import pandas as pd
import numpy as np
import sqlite3
import json
from pathlib import Path
from datetime import datetime

print("=" * 80)
print("COMPREHENSIVE AUDIT: FULL EVENT DUPLICATION BUG")
print("=" * 80)
print()

# ============================================================================
# 1. DATABASE VERIFICATION - GROUND TRUTH
# ============================================================================
print("1. ESTABLISHING GROUND TRUTH FROM TRANSACTIONS TABLE")
print("=" * 80)

conn = sqlite3.connect('courtreserve.db')

# Get actual payment totals from transactions
trans_query = """
SELECT
    CASE
        WHEN m."member_#" IS NOT NULL AND m.membership_status = 'Currently Active' THEN 'Active Member'
        ELSE 'Non-Member'
    END as customer_type,
    COUNT(*) as num_payments,
    SUM(CAST(REPLACE(REPLACE(REPLACE(REPLACE(t.total, '$', ''), ',', ''), '(', ''), ')', '') AS REAL)) as total_amount
FROM transactions t
LEFT JOIN members m ON t."member_#" = m."member_#"
WHERE t.trans_type LIKE '%Payment%'
  AND t.total != ''
GROUP BY customer_type
"""

trans_df = pd.read_sql_query(trans_query, conn)
print("\nACTUAL PAYMENTS (from Transactions Table):")
print(trans_df.to_string(index=False))

total_payments = trans_df['total_amount'].sum()
non_member_payments = trans_df[trans_df['customer_type'] == 'Non-Member']['total_amount'].sum()
member_payments = trans_df[trans_df['customer_type'] == 'Active Member']['total_amount'].sum()

print(f"\n{'TOTAL ACTUAL PAYMENTS:':<40} ${total_payments:>12,.2f}")
print(f"{'  Non-Member Payments:':<40} ${non_member_payments:>12,.2f}")
print(f"{'  Member Payments:':<40} ${member_payments:>12,.2f}")

# ============================================================================
# 2. CHECK-INS TABLE ANALYSIS - IDENTIFY INFLATION
# ============================================================================
print("\n\n2. CHECK-INS TABLE ANALYSIS (Source of Bug)")
print("=" * 80)

checkins_query = """
SELECT
    registration_type,
    COUNT(*) as num_checkins,
    COUNT(DISTINCT "player__#") as unique_players,
    SUM(price_amount) as total_shown,
    AVG(price_amount) as avg_price
FROM checkins
WHERE price_amount > 0
GROUP BY registration_type
ORDER BY total_shown DESC
"""

checkins_df = pd.read_sql_query(checkins_query, conn)
print("\nCHECK-INS REVENUE BY TYPE:")
print(checkins_df.to_string(index=False))

checkins_total = checkins_df['total_shown'].sum()
full_events_total = checkins_df[checkins_df['registration_type'] == 'Full']['total_shown'].sum()
dropin_total = checkins_df[checkins_df['registration_type'].isin(['Drop-In', 'Reservation'])]['total_shown'].sum()

print(f"\n{'TOTAL CHECK-INS REVENUE:':<40} ${checkins_total:>12,.2f}")
print(f"{'  Full Events (INFLATED):':<40} ${full_events_total:>12,.2f}")
print(f"{'  Drop-In/Reservation:':<40} ${dropin_total:>12,.2f}")

# Calculate inflation factor
inflation_factor = checkins_total / total_payments if total_payments > 0 else 0
print(f"\n{'INFLATION FACTOR:':<40} {inflation_factor:>12.2f}x")
print(f"{'  (Check-ins total / Transactions total)':<40}")

# ============================================================================
# 3. MEMBER vs NON-MEMBER BREAKDOWN
# ============================================================================
print("\n\n3. MEMBER vs NON-MEMBER REVENUE COMPARISON")
print("=" * 80)

# Non-members from check-ins
nonmember_checkins_query = """
SELECT
    registration_type,
    COUNT(*) as num_checkins,
    COUNT(DISTINCT c."player__#") as unique_players,
    SUM(c.price_amount) as total_shown
FROM checkins c
WHERE c.price_amount > 0
  AND c."player__#" NOT IN (
      SELECT "member_#" FROM members WHERE membership_status = 'Currently Active'
  )
GROUP BY registration_type
"""

nm_checkins_df = pd.read_sql_query(nonmember_checkins_query, conn)
print("\nNON-MEMBER CHECK-INS (All Types):")
print(nm_checkins_df.to_string(index=False))

nm_checkins_total = nm_checkins_df['total_shown'].sum()
nm_full_total = nm_checkins_df[nm_checkins_df['registration_type'] == 'Full']['total_shown'].sum()
nm_dropin_total = nm_checkins_df[nm_checkins_df['registration_type'].isin(['Drop-In', 'Reservation'])]['total_shown'].sum()

print(f"\n{'NON-MEMBER CHECK-INS TOTAL:':<40} ${nm_checkins_total:>12,.2f}")
print(f"{'  From Transactions (ACTUAL):':<40} ${non_member_payments:>12,.2f}")
print(f"{'  Difference (INFLATION):':<40} ${nm_checkins_total - non_member_payments:>12,.2f}")
print(f"{'  Inflation Factor:':<40} {nm_checkins_total / non_member_payments if non_member_payments > 0 else 0:>12.2f}x")

# ============================================================================
# 4. AFFECTED CALCULATIONS AUDIT
# ============================================================================
print("\n\n4. AUDIT OF AFFECTED CALCULATIONS")
print("=" * 80)

audit_results = []

# 4.1 Pay-Per-Use Analysis
print("\n4.1 PAY-PER-USE ANALYSIS")
print("-" * 80)

# Old method (WRONG)
old_ppu_query = """
SELECT
    COUNT(DISTINCT c."player__#") as unique_players,
    SUM(c.price_amount) as total_revenue
FROM checkins c
WHERE c.price_amount > 0
  AND c."player__#" NOT IN (
      SELECT "member_#" FROM members WHERE membership_status = 'Currently Active'
  )
"""
old_ppu = pd.read_sql_query(old_ppu_query, conn).iloc[0]

# New method (CORRECT)
new_ppu_query = """
SELECT
    COUNT(DISTINCT c."player__#") as unique_players,
    SUM(c.price_amount) as total_revenue
FROM checkins c
WHERE c.price_amount > 0
  AND c.registration_type NOT IN ('Full')
  AND c."player__#" NOT IN (
      SELECT "member_#" FROM members WHERE membership_status = 'Currently Active'
  )
"""
new_ppu = pd.read_sql_query(new_ppu_query, conn).iloc[0]

print(f"OLD METHOD (included Full events):")
print(f"  Players: {old_ppu['unique_players']:,}")
print(f"  Revenue: ${old_ppu['total_revenue']:,.2f}")
print(f"\nNEW METHOD (excluded Full events):")
print(f"  Players: {new_ppu['unique_players']:,}")
print(f"  Revenue: ${new_ppu['total_revenue']:,.2f}")
print(f"\nINFLATION: ${old_ppu['total_revenue'] - new_ppu['total_revenue']:,.2f} ({(old_ppu['total_revenue'] / new_ppu['total_revenue'] if new_ppu['total_revenue'] > 0 else 0):.1f}x)")

audit_results.append({
    'calculation': 'Pay-Per-Use Revenue',
    'old_value': float(old_ppu['total_revenue']),
    'new_value': float(new_ppu['total_revenue']),
    'inflation': float(old_ppu['total_revenue'] - new_ppu['total_revenue']),
    'impact': 'HIGH - Primary conversion opportunity calculation'
})

# 4.2 Total Facility Revenue
print("\n\n4.2 TOTAL FACILITY REVENUE")
print("-" * 80)

print(f"From Check-Ins Table: ${checkins_total:,.2f}")
print(f"From Transactions Table: ${total_payments:,.2f}")
print(f"Difference: ${checkins_total - total_payments:,.2f}")
print(f"Check-ins shows {(checkins_total / total_payments):.1f}x actual revenue")

audit_results.append({
    'calculation': 'Total Facility Revenue',
    'old_value': float(checkins_total),
    'new_value': float(total_payments),
    'inflation': float(checkins_total - total_payments),
    'impact': 'MEDIUM - Used in financial projections'
})

# 4.3 Member Spending (Check if members are affected)
print("\n\n4.3 MEMBER SPENDING ANALYSIS")
print("-" * 80)

member_checkins_query = """
SELECT
    registration_type,
    COUNT(*) as num_checkins,
    SUM(c.price_amount) as total_shown
FROM checkins c
WHERE c.price_amount > 0
  AND c."player__#" IN (
      SELECT "member_#" FROM members WHERE membership_status = 'Currently Active'
  )
GROUP BY registration_type
"""

member_checkins_df = pd.read_sql_query(member_checkins_query, conn)
print("\nMEMBER CHECK-INS BY TYPE:")
if len(member_checkins_df) > 0:
    print(member_checkins_df.to_string(index=False))
    member_checkins_total = member_checkins_df['total_shown'].sum()
    member_full_total = member_checkins_df[member_checkins_df['registration_type'] == 'Full']['total_shown'].sum() if 'Full' in member_checkins_df['registration_type'].values else 0

    print(f"\n{'MEMBER CHECK-INS TOTAL:':<40} ${member_checkins_total:>12,.2f}")
    print(f"{'  From Transactions (ACTUAL):':<40} ${member_payments:>12,.2f}")
    print(f"{'  Difference:':<40} ${member_checkins_total - member_payments:>12,.2f}")

    if member_full_total > 0:
        print(f"{'  Full Events in Check-ins:':<40} ${member_full_total:>12,.2f}")
        print(f"\n⚠️  MEMBERS ARE ALSO AFFECTED by Full event duplication")

        audit_results.append({
            'calculation': 'Member Spending',
            'old_value': float(member_checkins_total),
            'new_value': float(member_payments),
            'inflation': float(member_checkins_total - member_payments),
            'impact': 'MEDIUM - Affects member value calculations'
        })
    else:
        print(f"\n✓ Members have no Full event check-ins - NOT affected by bug")
else:
    print("No member check-ins with prices found")

# ============================================================================
# 5. PERSONA EXAMPLES VERIFICATION
# ============================================================================
print("\n\n5. PERSONA EXAMPLES VERIFICATION")
print("=" * 80)

# Check if any personas are mentioned in reports
personas = ['Mark Tomlinson', 'Sarah', 'Amanda', 'Bruce']

for persona in personas:
    # Check transactions
    persona_trans_query = f"""
    SELECT
        t."member_#",
        t.player,
        COUNT(*) as num_payments,
        SUM(CAST(REPLACE(REPLACE(REPLACE(REPLACE(t.total, '$', ''), ',', ''), '(', ''), ')', '') AS REAL)) as total_paid
    FROM transactions t
    WHERE t.player LIKE '%{persona}%'
      AND t.trans_type LIKE '%Payment%'
    GROUP BY t."member_#", t.player
    """
    persona_trans = pd.read_sql_query(persona_trans_query, conn)

    if len(persona_trans) > 0:
        print(f"\n{persona}:")
        for _, row in persona_trans.iterrows():
            print(f"  ID: {row['member_#']}")
            print(f"  Payments: {row['num_payments']}")
            print(f"  Total Paid: ${row['total_paid']:,.2f}")

            # Check check-ins for same person
            persona_checkins_query = f"""
            SELECT
                registration_type,
                COUNT(*) as num_checkins,
                SUM(price_amount) as total_shown
            FROM checkins
            WHERE "player__#" = {row['member_#']}
              AND price_amount > 0
            GROUP BY registration_type
            """
            persona_checkins = pd.read_sql_query(persona_checkins_query, conn)

            if len(persona_checkins) > 0:
                total_checkins = persona_checkins['total_shown'].sum()
                print(f"  Check-ins Total: ${total_checkins:,.2f}")
                if total_checkins > row['total_paid'] * 1.1:  # More than 10% difference
                    print(f"  ⚠️  INFLATED by ${total_checkins - row['total_paid']:,.2f}")
                    print(f"     Check-ins breakdown:")
                    for _, c_row in persona_checkins.iterrows():
                        print(f"       {c_row['registration_type']}: {c_row['num_checkins']} check-ins, ${c_row['total_shown']:,.2f}")

conn.close()

# ============================================================================
# 6. AFFECTED FILES AND SCRIPTS
# ============================================================================
print("\n\n6. AFFECTED FILES AND SCRIPTS")
print("=" * 80)

affected_scripts = []

# Check which scripts use checkins.price_amount
scripts_dir = Path('scripts')
for script_file in scripts_dir.glob('analyze_*.py'):
    with open(script_file, 'r') as f:
        content = f.read()

    has_price_amount = 'price_amount' in content
    has_checkins = 'checkins' in content
    has_registration_filter = "registration_type != 'Full'" in content or 'registration_type NOT IN' in content

    if has_price_amount and has_checkins:
        status = 'FIXED' if has_registration_filter else 'NEEDS FIX'
        affected_scripts.append({
            'script': script_file.name,
            'uses_price': has_price_amount,
            'uses_checkins': has_checkins,
            'has_filter': has_registration_filter,
            'status': status
        })

print("\nSCRIPT AUDIT RESULTS:")
print(f"{'Script':<45} {'Status':<15} {'Has Filter'}")
print("-" * 80)
for script in sorted(affected_scripts, key=lambda x: x['status']):
    emoji = '✓' if script['status'] == 'FIXED' else '⚠️ '
    print(f"{emoji} {script['script']:<43} {script['status']:<15} {script['has_filter']}")

# Check deliverables
print("\n\nAFFECTED DELIVERABLE FILES:")
deliverables = [
    ('deliverables/reports/PARTNER_NARRATIVE_Customer_Intelligence_Strategy.md', 'Partner narrative with revenue figures'),
    ('deliverables/reports/jtbd-analysis-report-enhanced.md', 'Technical report with segment analysis'),
    ('deliverables/visualizations/pay_per_use_segment.png', 'Pay-per-use visualization'),
    ('deliverables/data/pay_per_use_insights.txt', 'Pay-per-use insights text')
]

for filepath, description in deliverables:
    exists = Path(filepath).exists()
    status = '✓ Exists' if exists else 'Missing'
    print(f"  {status:<15} {filepath}")
    print(f"{'':15} → {description}")

# ============================================================================
# 7. SUMMARY AND RECOMMENDATIONS
# ============================================================================
print("\n\n7. AUDIT SUMMARY")
print("=" * 80)

print("\nKEY FINDINGS:")
print(f"  1. Check-ins table shows {inflation_factor:.1f}x actual revenue")
print(f"  2. Non-member revenue inflated by ${nm_checkins_total - non_member_payments:,.2f}")
print(f"  3. Full events account for ${full_events_total:,.2f} in check-ins")
print(f"  4. Actual total revenue: ${total_payments:,.2f} (from transactions)")

print("\nAFFECTED CALCULATIONS:")
for i, result in enumerate(audit_results, 1):
    print(f"\n  {i}. {result['calculation']}")
    print(f"     Old: ${result['old_value']:,.2f}")
    print(f"     New: ${result['new_value']:,.2f}")
    print(f"     Inflation: ${result['inflation']:,.2f}")
    print(f"     Impact: {result['impact']}")

print("\n\nSCRIPTS NEEDING FIXES:")
needs_fix = [s for s in affected_scripts if s['status'] == 'NEEDS FIX']
if needs_fix:
    for script in needs_fix:
        print(f"  ⚠️  {script['script']}")
else:
    print("  ✓ All scripts have been corrected")

print("\n\nFILES REQUIRING REGENERATION:")
print("  1. deliverables/visualizations/pay_per_use_segment.png")
print("  2. deliverables/data/pay_per_use_insights.txt")
print("  3. Any reports citing pay-per-use revenue > $250K")
print("  4. Presentation slides with $439K conversion opportunity")

# Save audit results
audit_summary = {
    'audit_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'ground_truth': {
        'total_payments': float(total_payments),
        'non_member_payments': float(non_member_payments),
        'member_payments': float(member_payments)
    },
    'checkins_inflated': {
        'total_shown': float(checkins_total),
        'inflation_factor': float(inflation_factor),
        'full_events_total': float(full_events_total)
    },
    'affected_calculations': audit_results,
    'scripts_needing_fix': [s['script'] for s in needs_fix]
}

output_file = Path('docs/audit_full_event_bug_results.json')
with open(output_file, 'w') as f:
    json.dump(audit_summary, f, indent=2)

print(f"\n\n✓ Audit results saved to: {output_file}")
print("=" * 80)
