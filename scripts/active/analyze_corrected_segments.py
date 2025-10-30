#!/usr/bin/env python3
"""
Corrected Customer Segmentation Analysis

This script fixes the pay-per-use analysis by properly distinguishing:
1. True Pay-Per-Use players (drop-in reservations only)
2. Program Participants (enrolled in multi-week programs)
3. Members (existing members)

Key Fix: Excludes registration_type='Full' from pay-per-use calculations
to avoid counting full event prices multiple times per check-in.

Author: Claude Code (Anthropic)
Date: October 29, 2025
"""

import pandas as pd
import numpy as np
import json
import sqlite3
from datetime import datetime
from pathlib import Path
import sys

# Add scripts directory to path
sys.path.append(str(Path(__file__).parent))
from db_loader import CourtReserveDB

# Output directory
OUTPUT_DIR = Path('deliverables/data')
OUTPUT_DIR.mkdir(exist_ok=True)

print("=" * 80)
print("CORRECTED CUSTOMER SEGMENTATION ANALYSIS")
print("=" * 80)
print(f"\nKey Fix: Excluding registration_type='Full' from pay-per-use calculations")
print(f"Output Directory: {OUTPUT_DIR}")
print()

# Load data from database
print("Loading data from database...")
with CourtReserveDB() as db:
    checkins = db.get_checkins()
    members = db.get_members()
    transactions = db.get_transactions()

print(f"  Loaded {len(checkins):,} check-in records")
print(f"  Loaded {len(members):,} member records")
print(f"  Loaded {len(transactions):,} transaction records")

# Parse dates
checkins['checkin_datetime'] = pd.to_datetime(checkins['check_in_date_time'], errors='coerce')

# Parse price amounts
checkins['price_amount'] = checkins['price_amount'].fillna(0)

# ============================================================================
# 1. CLASSIFY CUSTOMERS INTO SEGMENTS
# ============================================================================
print("\n" + "=" * 80)
print("1. CLASSIFYING CUSTOMERS BY BEHAVIOR")
print("=" * 80)

# Get active members (status is "Currently Active" not "Active")
active_members = set(members[members['membership_status'] == 'Currently Active']['member_#'].unique())
print(f"\nActive Members: {len(active_members):,}")

# Classify all customers
customer_classification = {}

for player_id in checkins['player__#'].unique():
    player_checkins = checkins[checkins['player__#'] == player_id]

    # Check if member
    is_member = player_id in active_members

    # Count registration types
    reg_types = player_checkins['registration_type'].value_counts()
    has_full_events = reg_types.get('Full', 0) > 0
    has_dropins = player_checkins[player_checkins['registration_type'].isin(['Reservation', 'Drop-In'])].shape[0] > 0

    # Classify
    if is_member:
        segment = 'Member'
    elif has_full_events and has_dropins:
        segment = 'Program Participant + Drop-In'
    elif has_full_events:
        segment = 'Program Participant'
    elif has_dropins:
        segment = 'True Pay-Per-Use'
    else:
        segment = 'Other'

    customer_classification[player_id] = {
        'segment': segment,
        'is_member': is_member,
        'full_events': reg_types.get('Full', 0),
        'dropins': player_checkins[player_checkins['registration_type'].isin(['Reservation', 'Drop-In'])].shape[0],
        'total_checkins': len(player_checkins)
    }

# Convert to DataFrame
classification_df = pd.DataFrame.from_dict(customer_classification, orient='index')
classification_df.index.name = 'player__#'
classification_df = classification_df.reset_index()

# Print segment distribution
segment_dist = classification_df['segment'].value_counts()
print("\nCustomer Segment Distribution:")
print("-" * 80)
for segment, count in segment_dist.items():
    pct = count / len(classification_df) * 100
    print(f"  {segment:35} {count:6,} ({pct:5.1f}%)")
print("-" * 80)
print(f"  {'TOTAL':35} {len(classification_df):6,}")

# ============================================================================
# 2. CORRECTED PAY-PER-USE REVENUE ANALYSIS
# ============================================================================
print("\n" + "=" * 80)
print("2. CORRECTED PAY-PER-USE REVENUE ANALYSIS")
print("=" * 80)

# TRUE Pay-Per-Use: Non-members, Drop-In/Reservation only (EXCLUDE Full events)
true_ppu_checkins = checkins[
    (~checkins['player__#'].isin(active_members)) &
    (checkins['registration_type'].isin(['Reservation', 'Drop-In'])) &
    (checkins['price_amount'] > 0)
].copy()

print(f"\nTrue Pay-Per-Use Check-ins: {len(true_ppu_checkins):,}")
print(f"Unique Players: {true_ppu_checkins['player__#'].nunique():,}")
print(f"Total Revenue: ${true_ppu_checkins['price_amount'].sum():,.2f}")
print(f"Average per check-in: ${true_ppu_checkins['price_amount'].mean():.2f}")

# Calculate spending per customer
ppu_customer_spending = true_ppu_checkins.groupby('player__#').agg({
    'price_amount': 'sum',
    'player_first_name': 'first',
    'player_last_name': 'first',
    'check_in_date_time': ['count', 'min', 'max']
}).reset_index()

ppu_customer_spending.columns = ['player__#', 'total_spent', 'first_name', 'last_name',
                                   'num_visits', 'first_visit', 'last_visit']

# Calculate date range for monthly average
ppu_customer_spending['first_visit_dt'] = pd.to_datetime(ppu_customer_spending['first_visit'], errors='coerce')
ppu_customer_spending['last_visit_dt'] = pd.to_datetime(ppu_customer_spending['last_visit'], errors='coerce')
ppu_customer_spending['days_active'] = (ppu_customer_spending['last_visit_dt'] -
                                         ppu_customer_spending['first_visit_dt']).dt.days + 1
ppu_customer_spending['months_active'] = ppu_customer_spending['days_active'] / 30.44
ppu_customer_spending['monthly_spend'] = ppu_customer_spending['total_spent'] / ppu_customer_spending['months_active']

# Fix any divide by zero or infinite values
mask_inf = np.isinf(ppu_customer_spending['monthly_spend'])
ppu_customer_spending.loc[mask_inf, 'monthly_spend'] = ppu_customer_spending.loc[mask_inf, 'total_spent']

print(f"\nMonthly Spending Stats:")
print(f"  Average: ${ppu_customer_spending['monthly_spend'].mean():.2f}/month")
print(f"  Median: ${ppu_customer_spending['monthly_spend'].median():.2f}/month")
print(f"  75th percentile: ${ppu_customer_spending['monthly_spend'].quantile(0.75):.2f}/month")

# High-value targets (>$80/month)
high_value_targets = ppu_customer_spending[ppu_customer_spending['monthly_spend'] > 80]
print(f"\nHigh-Value Conversion Targets (>$80/month): {len(high_value_targets):,}")
print(f"  Total Monthly Revenue: ${high_value_targets['monthly_spend'].sum():,.2f}")
print(f"  Average Monthly Spend: ${high_value_targets['monthly_spend'].mean():.2f}")

# ============================================================================
# 3. PROGRAM PARTICIPANTS ANALYSIS
# ============================================================================
print("\n" + "=" * 80)
print("3. PROGRAM PARTICIPANTS ANALYSIS")
print("=" * 80)

# Program participants: Non-members with Full event registrations
program_checkins = checkins[
    (~checkins['player__#'].isin(active_members)) &
    (checkins['registration_type'] == 'Full')
].copy()

print(f"\nProgram Event Check-ins: {len(program_checkins):,}")
print(f"Unique Program Participants: {program_checkins['player__#'].nunique():,}")

# Get actual program payments from transactions
# Filter transactions for non-members
transactions['is_member'] = transactions['member_#'].isin(active_members)
program_transactions = transactions[
    (~transactions['is_member']) &
    (transactions['trans_type'].str.contains('Payment', na=False)) &
    (transactions['category'].str.contains('Drills|Skills|Event', na=False, case=False))
]

print(f"\nProgram Participant Payments (from transactions):")
if len(program_transactions) > 0:
    # Parse transaction amounts
    program_transactions['amount'] = program_transactions['total'].str.replace('$', '').str.replace(',', '').str.replace('(', '').str.replace(')', '').astype(float)
    program_revenue = program_transactions['amount'].sum()
    print(f"  Total Program Revenue: ${program_revenue:,.2f}")
    print(f"  Number of Payments: {len(program_transactions):,}")
    print(f"  Average Payment: ${program_transactions['amount'].mean():.2f}")
else:
    program_revenue = 0
    print(f"  No program payment transactions found in database")
    print(f"  Note: Program revenue tracked separately in event management system")

# ============================================================================
# 4. CORRECTED FREQUENCY ANALYSIS
# ============================================================================
print("\n" + "=" * 80)
print("4. CORRECTED FREQUENCY ANALYSIS")
print("=" * 80)

# Calculate visit frequency per customer (all checkins)
all_checkins_with_dates = checkins[checkins['checkin_datetime'].notna()].copy()

# Calculate analysis period
analysis_start = all_checkins_with_dates['checkin_datetime'].min()
analysis_end = all_checkins_with_dates['checkin_datetime'].max()
analysis_days = (analysis_end - analysis_start).days
analysis_months = analysis_days / 30.44

print(f"\nAnalysis Period:")
print(f"  Start: {analysis_start.strftime('%Y-%m-%d')}")
print(f"  End: {analysis_end.strftime('%Y-%m-%d')}")
print(f"  Duration: {analysis_days} days ({analysis_months:.1f} months)")

# Frequency by customer
customer_frequency = all_checkins_with_dates.groupby('player__#').agg({
    'checkin_datetime': 'count'
}).reset_index()
customer_frequency.columns = ['player__#', 'total_visits']
customer_frequency['avg_visits_per_month'] = customer_frequency['total_visits'] / analysis_months

# Merge with classification
customer_frequency = customer_frequency.merge(classification_df[['player__#', 'segment', 'is_member']],
                                               on='player__#', how='left')

# Categorize frequency
def categorize_frequency(visits_per_month):
    if visits_per_month >= 20:
        return 'Daily User'
    elif visits_per_month >= 4:
        return 'Weekly User'
    elif visits_per_month >= 1.5:
        return 'Monthly User'
    else:
        return 'Occasional User'

customer_frequency['frequency_segment'] = customer_frequency['avg_visits_per_month'].apply(categorize_frequency)

# Separate members and non-members
members_freq = customer_frequency[customer_frequency['is_member'] == True]
nonmembers_freq = customer_frequency[customer_frequency['is_member'] == False]

# Create frequency summaries
def create_frequency_summary(df, label):
    summary = df.groupby('frequency_segment').agg({
        'player__#': 'count',
        'avg_visits_per_month': 'mean',
        'total_visits': 'mean'
    }).reset_index()

    summary.columns = ['frequency_segment', 'customer_count', 'avg_visits_per_month', 'avg_total_visits']
    summary['avg_visits_per_month'] = summary['avg_visits_per_month'].round(1)
    summary['avg_total_visits'] = summary['avg_total_visits'].round(0).astype(int)

    # Sort by frequency
    freq_order = ['Daily User', 'Weekly User', 'Monthly User', 'Occasional User']
    summary['freq_order'] = summary['frequency_segment'].apply(lambda x: freq_order.index(x) if x in freq_order else 999)
    summary = summary.sort_values('freq_order').drop('freq_order', axis=1)

    print(f"\n{label} Frequency Distribution:")
    print(summary.to_string(index=False))

    return summary

members_summary = create_frequency_summary(members_freq, "MEMBERS")
nonmembers_summary = create_frequency_summary(nonmembers_freq, "NON-MEMBERS")

# ============================================================================
# 5. SAVE RESULTS
# ============================================================================
print("\n" + "=" * 80)
print("5. SAVING CORRECTED RESULTS")
print("=" * 80)

# Save frequency summaries
members_summary.to_csv(OUTPUT_DIR / 'frequency_summary_members_corrected.csv', index=False)
print(f"\n✓ Saved: {OUTPUT_DIR / 'frequency_summary_members_corrected.csv'}")

nonmembers_summary.to_csv(OUTPUT_DIR / 'frequency_summary_nonmembers_corrected.csv', index=False)
print(f"✓ Saved: {OUTPUT_DIR / 'frequency_summary_nonmembers_corrected.csv'}")

# Save customer classification
classification_df.to_csv(OUTPUT_DIR / 'customer_classification.csv', index=False)
print(f"✓ Saved: {OUTPUT_DIR / 'customer_classification.csv'}")

# Save pay-per-use customers with spending
ppu_customer_spending.to_csv(OUTPUT_DIR / 'pay_per_use_spending_corrected.csv', index=False)
print(f"✓ Saved: {OUTPUT_DIR / 'pay_per_use_spending_corrected.csv'}")

# Save high-value targets
high_value_targets.to_csv(OUTPUT_DIR / 'high_value_conversion_targets.csv', index=False)
print(f"✓ Saved: {OUTPUT_DIR / 'high_value_conversion_targets.csv'}")

# ============================================================================
# 6. COMPARISON SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("6. BEFORE vs AFTER COMPARISON")
print("=" * 80)

# Load old pay-per-use insights if they exist
old_insights_file = Path('deliverables/data/pay_per_use_insights.txt')
if old_insights_file.exists():
    print("\nOLD ANALYSIS (Included Full Events):")
    print("  Based on: All non-member check-ins (including Full event duplicates)")
    print("  Issue: Counted $660 for every check-in of 6-week programs")
else:
    print("\nOLD ANALYSIS: Not available for comparison")

print("\nNEW ANALYSIS (Drop-In Only):")
print(f"  True Pay-Per-Use Players: {true_ppu_checkins['player__#'].nunique():,}")
print(f"  Total Drop-In Revenue: ${true_ppu_checkins['price_amount'].sum():,.2f}")
print(f"  Average per Visit: ${true_ppu_checkins['price_amount'].mean():.2f}")
print(f"  High-Value Targets (>$80/mo): {len(high_value_targets):,}")

print("\nPROGRAM PARTICIPANTS:")
print(f"  Unique Participants: {program_checkins['player__#'].nunique():,}")
print(f"  Total Program Check-ins: {len(program_checkins):,}")
if program_revenue > 0:
    print(f"  Program Revenue: ${program_revenue:,.2f}")

# Create comprehensive summary
summary_data = {
    'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'analysis_period': {
        'start': analysis_start.strftime('%Y-%m-%d'),
        'end': analysis_end.strftime('%Y-%m-%d'),
        'days': analysis_days,
        'months': round(analysis_months, 1)
    },
    'segments': {
        'active_members': int(len(active_members)),
        'true_pay_per_use': int(true_ppu_checkins['player__#'].nunique()),
        'program_participants': int(program_checkins['player__#'].nunique()),
        'total_unique_players': int(checkins['player__#'].nunique())
    },
    'pay_per_use_revenue': {
        'total_revenue': float(true_ppu_checkins['price_amount'].sum()),
        'total_checkins': int(len(true_ppu_checkins)),
        'avg_per_visit': float(true_ppu_checkins['price_amount'].mean()),
        'unique_players': int(true_ppu_checkins['player__#'].nunique()),
        'high_value_targets_over_80': int(len(high_value_targets)),
        'high_value_monthly_revenue': float(high_value_targets['monthly_spend'].sum())
    },
    'program_participants': {
        'unique_participants': int(program_checkins['player__#'].nunique()),
        'total_checkins': int(len(program_checkins)),
        'revenue_from_transactions': float(program_revenue) if program_revenue > 0 else None
    },
    'methodology_fix': {
        'issue': 'Full event prices were counted on every check-in',
        'solution': 'Excluded registration_type=Full from pay-per-use calculations',
        'impact': 'Dramatically reduced inflated revenue figures'
    }
}

# Save summary as JSON
with open(OUTPUT_DIR / 'corrected_segmentation_summary.json', 'w') as f:
    json.dump(summary_data, f, indent=2)
print(f"\n✓ Saved: {OUTPUT_DIR / 'corrected_segmentation_summary.json'}")

print("\n" + "=" * 80)
print("CORRECTED ANALYSIS COMPLETE")
print("=" * 80)
print("\nKey Files Generated:")
print(f"  • frequency_summary_members_corrected.csv")
print(f"  • frequency_summary_nonmembers_corrected.csv")
print(f"  • customer_classification.csv")
print(f"  • pay_per_use_spending_corrected.csv")
print(f"  • high_value_conversion_targets.csv")
print(f"  • corrected_segmentation_summary.json")
print("\nNext Steps:")
print("  1. Review high_value_conversion_targets.csv for accurate conversion list")
print("  2. Use corrected frequency summaries for updated charts")
print("  3. Update presentation with corrected revenue figures")
print("  4. Consider program participants as separate conversion strategy")
print("=" * 80)
