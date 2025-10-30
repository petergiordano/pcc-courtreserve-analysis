#!/usr/bin/env python3
"""
Activation Journey Analysis Script

Purpose: Track customer activation journey from first visit to regular usage
Analyzes: Time to Nth visit, activation funnel, visit velocity

Input: courtreserve.db (SQLite database)
Output: CSV files in ../deliverables/data/

Author: Claude Code (Anthropic)
Date: October 29, 2025
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Configuration
DB_PATH = Path(__file__).parent.parent / 'courtreserve.db'
OUTPUT_DIR = Path(__file__).parent.parent / 'deliverables/data'
ANALYSIS_DATE = datetime(2025, 10, 27)

# Activation milestones (visit numbers to track)
ACTIVATION_MILESTONES = [1, 2, 3, 5, 10, 20]

def load_checkins_with_membership():
    """
    Load check-in data with membership status for activation tracking.

    Returns:
        DataFrame with columns: customer_id, checkin_datetime, checkin_date, membership_status, is_member
    """
    print("Loading check-in data with membership status...")

    conn = sqlite3.connect(DB_PATH)

    # Load check-ins
    checkins = pd.read_sql_query("""
        SELECT
            "player__#" as customer_id,
            check_in_date_time,
            check_in_status
        FROM checkins
        WHERE check_in_status = 'Checked-In'
    """, conn)

    # Load member status
    members = pd.read_sql_query("""
        SELECT
            "member_#",
            membership_status
        FROM members
    """, conn)

    conn.close()

    # Convert dates
    checkins['checkin_datetime'] = pd.to_datetime(checkins['check_in_date_time'])
    checkins['checkin_date'] = checkins['checkin_datetime'].dt.date

    # Clean member_# (convert to numeric, drop phone numbers)
    members['member_#'] = pd.to_numeric(members['member_#'], errors='coerce')
    members = members.dropna(subset=['member_#'])
    members['member_#'] = members['member_#'].astype(int)

    # Merge to get membership status
    df = checkins.merge(
        members,
        left_on='customer_id',
        right_on='member_#',
        how='left'
    )

    # Fill missing membership status
    df['membership_status'] = df['membership_status'].fillna('No Membership')

    # Classify as member or pay-per-use
    df['is_member'] = df['membership_status'].apply(
        lambda x: 'Member' if x == 'Currently Active' else 'Pay-Per-Use'
    )

    print(f"  ✓ Loaded {len(df):,} check-ins from {df['customer_id'].nunique():,} customers")
    print(f"  ✓ Members: {len(df[df['is_member']=='Member']):,} check-ins")
    print(f"  ✓ Non-Members: {len(df[df['is_member']=='Pay-Per-Use']):,} check-ins")

    return df[['customer_id', 'checkin_datetime', 'checkin_date', 'membership_status', 'is_member']]


def calculate_activation_journey(df, membership_type='all'):
    """
    Calculate activation journey metrics for each customer.

    Args:
        df: DataFrame with check-in data
        membership_type: 'Member', 'Pay-Per-Use', or 'all'

    Returns:
        DataFrame with activation metrics per customer
    """
    print(f"Calculating activation journey ({membership_type})...")

    # Filter by membership type
    if membership_type != 'all':
        df = df[df['is_member'] == membership_type].copy()

    activation_data = []

    for customer_id, group in df.groupby('customer_id'):
        # Sort by visit date
        visits = group.sort_values('checkin_datetime')

        # Get membership status (mode)
        membership_status = visits['membership_status'].mode()[0] if len(visits['membership_status'].mode()) > 0 else 'Unknown'
        is_member = visits['is_member'].mode()[0] if len(visits['is_member'].mode()) > 0 else 'Pay-Per-Use'

        # Basic metrics
        total_visits = len(visits)
        first_visit = visits['checkin_datetime'].iloc[0]
        last_visit = visits['checkin_datetime'].iloc[-1]
        days_active = (last_visit - first_visit).days + 1

        # Calculate time to each milestone visit
        milestone_times = {}
        for milestone in ACTIVATION_MILESTONES:
            if total_visits >= milestone:
                milestone_visit_date = visits['checkin_datetime'].iloc[milestone - 1]
                days_to_milestone = (milestone_visit_date - first_visit).days
                milestone_times[f'days_to_visit_{milestone}'] = days_to_milestone
            else:
                milestone_times[f'days_to_visit_{milestone}'] = None

        # Calculate visit velocity (visits per week in first 30 days)
        first_30_days = first_visit + timedelta(days=30)
        visits_in_first_30 = len(visits[visits['checkin_datetime'] <= first_30_days])
        visit_velocity_30d = visits_in_first_30 / 4.29  # weeks in 30 days

        # Calculate activation status
        activation_status = 'Not Activated'
        if total_visits >= 20:
            activation_status = 'Fully Activated (20+ visits)'
        elif total_visits >= 10:
            activation_status = 'Highly Activated (10-19 visits)'
        elif total_visits >= 5:
            activation_status = 'Moderately Activated (5-9 visits)'
        elif total_visits >= 3:
            activation_status = 'Early Activated (3-4 visits)'
        elif total_visits >= 2:
            activation_status = 'Initial Activation (2 visits)'
        else:
            activation_status = 'One-Time User (1 visit)'

        # Calculate days since last visit (churn risk)
        days_since_last = (ANALYSIS_DATE - last_visit.to_pydatetime()).days

        activation_data.append({
            'customer_id': customer_id,
            'total_visits': total_visits,
            'first_visit': first_visit,
            'last_visit': last_visit,
            'days_active': days_active,
            'days_since_last_visit': days_since_last,
            'visits_in_first_30_days': visits_in_first_30,
            'visit_velocity_30d': round(visit_velocity_30d, 2),
            **milestone_times,
            'activation_status': activation_status,
            'membership_status': membership_status,
            'is_member': is_member
        })

    print(f"  ✓ Calculated activation journey for {len(activation_data):,} customers")

    return pd.DataFrame(activation_data)


def calculate_activation_funnel(df, membership_type='all'):
    """
    Calculate activation funnel (how many customers reach each milestone).

    Args:
        df: DataFrame with activation journey data
        membership_type: 'Member', 'Pay-Per-Use', or 'all'

    Returns:
        DataFrame with funnel metrics
    """
    print(f"Calculating activation funnel ({membership_type})...")

    funnel_data = []

    for milestone in ACTIVATION_MILESTONES:
        customers_reached = len(df[df['total_visits'] >= milestone])
        pct_of_total = (customers_reached / len(df) * 100) if len(df) > 0 else 0

        # Calculate average time to reach this milestone
        milestone_col = f'days_to_visit_{milestone}'
        avg_days = df[df[milestone_col].notna()][milestone_col].mean()
        median_days = df[df[milestone_col].notna()][milestone_col].median()

        funnel_data.append({
            'milestone': f'Visit {milestone}',
            'milestone_number': milestone,
            'customers_reached': customers_reached,
            'pct_of_starting_cohort': round(pct_of_total, 1),
            'avg_days_to_reach': round(avg_days, 1) if pd.notna(avg_days) else None,
            'median_days_to_reach': round(median_days, 1) if pd.notna(median_days) else None,
            'membership_type': membership_type
        })

    print(f"  ✓ Calculated funnel for {len(funnel_data)} milestones")

    return pd.DataFrame(funnel_data)


def calculate_velocity_distribution(df, membership_type='all'):
    """
    Analyze distribution of visit velocity (visits per week in first 30 days).

    Args:
        df: DataFrame with activation journey data
        membership_type: 'Member', 'Pay-Per-Use', or 'all'

    Returns:
        DataFrame with velocity segment distribution
    """
    print(f"Calculating velocity distribution ({membership_type})...")

    # Define velocity segments
    def classify_velocity(velocity):
        if velocity >= 2:
            return 'High Velocity (2+ visits/week)'
        elif velocity >= 1:
            return 'Medium Velocity (1-2 visits/week)'
        elif velocity >= 0.5:
            return 'Low Velocity (0.5-1 visits/week)'
        else:
            return 'Very Low Velocity (<0.5 visits/week)'

    df['velocity_segment'] = df['visit_velocity_30d'].apply(classify_velocity)

    # Calculate segment distribution
    velocity_summary = df.groupby('velocity_segment').agg(
        customer_count=('customer_id', 'count'),
        avg_total_visits=('total_visits', 'mean'),
        avg_days_to_visit_5=('days_to_visit_5', 'mean'),
        pct_reached_visit_10=('total_visits', lambda x: (x >= 10).sum() / len(x) * 100)
    ).reset_index()

    velocity_summary['pct_of_total'] = (velocity_summary['customer_count'] / len(df) * 100).round(1)
    velocity_summary['avg_total_visits'] = velocity_summary['avg_total_visits'].round(1)
    velocity_summary['avg_days_to_visit_5'] = velocity_summary['avg_days_to_visit_5'].round(1)
    velocity_summary['pct_reached_visit_10'] = velocity_summary['pct_reached_visit_10'].round(1)
    velocity_summary['membership_type'] = membership_type

    # Sort by velocity
    velocity_order = [
        'High Velocity (2+ visits/week)',
        'Medium Velocity (1-2 visits/week)',
        'Low Velocity (0.5-1 visits/week)',
        'Very Low Velocity (<0.5 visits/week)'
    ]
    velocity_summary['sort_order'] = velocity_summary['velocity_segment'].apply(lambda x: velocity_order.index(x))
    velocity_summary = velocity_summary.sort_values('sort_order').drop('sort_order', axis=1)

    print(f"  ✓ Calculated velocity distribution for {len(velocity_summary)} segments")

    return velocity_summary


def main():
    """Main execution function."""
    print("\n" + "="*70)
    print("ACTIVATION JOURNEY ANALYSIS")
    print("="*70)
    print(f"Database: {DB_PATH}")
    print(f"Analysis Date: {ANALYSIS_DATE.strftime('%Y-%m-%d')}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print()

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    df = load_checkins_with_membership()

    print("\n" + "-"*70)
    print("GENERATING ACTIVATION JOURNEY FILES")
    print("-"*70)

    # Split by membership type
    members_df = df[df['is_member'] == 'Member'].copy()
    nonmembers_df = df[df['is_member'] == 'Pay-Per-Use'].copy()

    # --- FILE 1: Per-customer activation journey (MEMBERS) ---
    if len(members_df) > 0:
        activation_members = calculate_activation_journey(members_df, 'Member')
        output_file = OUTPUT_DIR / 'activation_journey_members.csv'
        activation_members.to_csv(output_file, index=False)
        print(f"\n1. Per-Customer Activation Journey (MEMBERS)")
        print(f"  ✓ {output_file}")
        print(f"  ✓ {len(activation_members):,} members")
        print(f"  ✓ Columns: {len(activation_members.columns)}")

    # --- FILE 2: Per-customer activation journey (NON-MEMBERS) ---
    if len(nonmembers_df) > 0:
        activation_nonmembers = calculate_activation_journey(nonmembers_df, 'Pay-Per-Use')
        output_file = OUTPUT_DIR / 'activation_journey_nonmembers.csv'
        activation_nonmembers.to_csv(output_file, index=False)
        print(f"\n2. Per-Customer Activation Journey (NON-MEMBERS)")
        print(f"  ✓ {output_file}")
        print(f"  ✓ {len(activation_nonmembers):,} non-members")
        print(f"  ✓ Columns: {len(activation_nonmembers.columns)}")

    # --- FILE 3: Activation funnel (MEMBERS) ---
    if len(members_df) > 0:
        funnel_members = calculate_activation_funnel(activation_members, 'Member')
        output_file = OUTPUT_DIR / 'activation_funnel_members.csv'
        funnel_members.to_csv(output_file, index=False)
        print(f"\n3. Activation Funnel (MEMBERS)")
        print(f"  ✓ {output_file}")
        print(f"  ✓ {len(funnel_members)} milestones tracked")

    # --- FILE 4: Activation funnel (NON-MEMBERS) ---
    if len(nonmembers_df) > 0:
        funnel_nonmembers = calculate_activation_funnel(activation_nonmembers, 'Pay-Per-Use')
        output_file = OUTPUT_DIR / 'activation_funnel_nonmembers.csv'
        funnel_nonmembers.to_csv(output_file, index=False)
        print(f"\n4. Activation Funnel (NON-MEMBERS)")
        print(f"  ✓ {output_file}")
        print(f"  ✓ {len(funnel_nonmembers)} milestones tracked")

    # --- FILE 5: Velocity distribution (MEMBERS) ---
    if len(members_df) > 0:
        velocity_members = calculate_velocity_distribution(activation_members, 'Member')
        output_file = OUTPUT_DIR / 'activation_velocity_members.csv'
        velocity_members.to_csv(output_file, index=False)
        print(f"\n5. Visit Velocity Distribution (MEMBERS)")
        print(f"  ✓ {output_file}")
        print(f"  ✓ {len(velocity_members)} velocity segments")

    # --- FILE 6: Velocity distribution (NON-MEMBERS) ---
    if len(nonmembers_df) > 0:
        velocity_nonmembers = calculate_velocity_distribution(activation_nonmembers, 'Pay-Per-Use')
        output_file = OUTPUT_DIR / 'activation_velocity_nonmembers.csv'
        velocity_nonmembers.to_csv(output_file, index=False)
        print(f"\n6. Visit Velocity Distribution (NON-MEMBERS)")
        print(f"  ✓ {output_file}")
        print(f"  ✓ {len(velocity_nonmembers)} velocity segments")

    # Summary statistics
    print("\n" + "-"*70)
    print("ACTIVATION JOURNEY SUMMARY")
    print("-"*70)

    if len(members_df) > 0:
        print(f"\nMEMBERS ({len(activation_members):,} customers):")
        print(f"  Fully Activated (20+ visits): {len(activation_members[activation_members['total_visits'] >= 20]):,} ({len(activation_members[activation_members['total_visits'] >= 20]) / len(activation_members) * 100:.1f}%)")
        print(f"  Highly Activated (10-19 visits): {len(activation_members[(activation_members['total_visits'] >= 10) & (activation_members['total_visits'] < 20)]):,} ({len(activation_members[(activation_members['total_visits'] >= 10) & (activation_members['total_visits'] < 20)]) / len(activation_members) * 100:.1f}%)")
        print(f"  Moderately Activated (5-9 visits): {len(activation_members[(activation_members['total_visits'] >= 5) & (activation_members['total_visits'] < 10)]):,} ({len(activation_members[(activation_members['total_visits'] >= 5) & (activation_members['total_visits'] < 10)]) / len(activation_members) * 100:.1f}%)")
        print(f"  Early Activated (3-4 visits): {len(activation_members[(activation_members['total_visits'] >= 3) & (activation_members['total_visits'] < 5)]):,} ({len(activation_members[(activation_members['total_visits'] >= 3) & (activation_members['total_visits'] < 5)]) / len(activation_members) * 100:.1f}%)")
        print(f"  One-Time Users (1 visit): {len(activation_members[activation_members['total_visits'] == 1]):,} ({len(activation_members[activation_members['total_visits'] == 1]) / len(activation_members) * 100:.1f}%)")
        print(f"\n  Average days to visit 5: {activation_members['days_to_visit_5'].mean():.1f} days")
        print(f"  Average days to visit 10: {activation_members['days_to_visit_10'].mean():.1f} days")
        print(f"  Average visit velocity (first 30 days): {activation_members['visit_velocity_30d'].mean():.2f} visits/week")

    if len(nonmembers_df) > 0:
        print(f"\nNON-MEMBERS ({len(activation_nonmembers):,} customers):")
        print(f"  Fully Activated (20+ visits): {len(activation_nonmembers[activation_nonmembers['total_visits'] >= 20]):,} ({len(activation_nonmembers[activation_nonmembers['total_visits'] >= 20]) / len(activation_nonmembers) * 100:.1f}%)")
        print(f"  Highly Activated (10-19 visits): {len(activation_nonmembers[(activation_nonmembers['total_visits'] >= 10) & (activation_nonmembers['total_visits'] < 20)]):,} ({len(activation_nonmembers[(activation_nonmembers['total_visits'] >= 10) & (activation_nonmembers['total_visits'] < 20)]) / len(activation_nonmembers) * 100:.1f}%)")
        print(f"  Moderately Activated (5-9 visits): {len(activation_nonmembers[(activation_nonmembers['total_visits'] >= 5) & (activation_nonmembers['total_visits'] < 10)]):,} ({len(activation_nonmembers[(activation_nonmembers['total_visits'] >= 5) & (activation_nonmembers['total_visits'] < 10)]) / len(activation_nonmembers) * 100:.1f}%)")
        print(f"  Early Activated (3-4 visits): {len(activation_nonmembers[(activation_nonmembers['total_visits'] >= 3) & (activation_nonmembers['total_visits'] < 5)]):,} ({len(activation_nonmembers[(activation_nonmembers['total_visits'] >= 3) & (activation_nonmembers['total_visits'] < 5)]) / len(activation_nonmembers) * 100:.1f}%)")
        print(f"  One-Time Users (1 visit): {len(activation_nonmembers[activation_nonmembers['total_visits'] == 1]):,} ({len(activation_nonmembers[activation_nonmembers['total_visits'] == 1]) / len(activation_nonmembers) * 100:.1f}%)")

    print("\n" + "="*70)
    print("✅ ACTIVATION JOURNEY ANALYSIS COMPLETE")
    print("="*70)
    print()


if __name__ == '__main__':
    main()
