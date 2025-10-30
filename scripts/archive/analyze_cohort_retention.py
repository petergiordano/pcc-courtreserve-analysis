#!/usr/bin/env python3
"""
Cohort Retention Analysis Script

Purpose: Track retention rates for customer cohorts over time
Analyzes: Monthly cohorts, retention curves, churn analysis

Input: courtreserve.db (SQLite database)
Output: CSV files in ../deliverables/data/

Author: Claude Code (Anthropic)
Date: October 29, 2025
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Configuration
DB_PATH = Path(__file__).parent.parent / 'courtreserve.db'
OUTPUT_DIR = Path(__file__).parent.parent / 'deliverables/data'
ANALYSIS_DATE = datetime(2025, 10, 27)

def load_checkins_with_membership():
    """
    Load check-in data with membership status for cohort analysis.

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


def calculate_cohorts(df, membership_type='all'):
    """
    Assign customers to cohorts based on their first visit month.

    Args:
        df: DataFrame with check-in data
        membership_type: 'Member', 'Pay-Per-Use', or 'all'

    Returns:
        DataFrame with customer_id, cohort_month, first_visit
    """
    print(f"Calculating cohorts ({membership_type})...")

    # Filter by membership type
    if membership_type != 'all':
        df = df[df['is_member'] == membership_type].copy()

    # Get first visit per customer
    first_visits = df.groupby('customer_id')['checkin_datetime'].min().reset_index()
    first_visits.columns = ['customer_id', 'first_visit']

    # Extract cohort month (YYYY-MM)
    first_visits['cohort_month'] = first_visits['first_visit'].dt.to_period('M')

    print(f"  ✓ Identified {first_visits['cohort_month'].nunique()} cohorts")
    print(f"  ✓ Date range: {first_visits['cohort_month'].min()} to {first_visits['cohort_month'].max()}")

    return first_visits


def calculate_retention_matrix(df, cohorts, membership_type='all'):
    """
    Calculate retention matrix (cohort x month_number).

    Args:
        df: DataFrame with check-in data
        cohorts: DataFrame with customer_id, cohort_month, first_visit
        membership_type: 'Member', 'Pay-Per-Use', or 'all'

    Returns:
        DataFrame with retention rates per cohort per month
    """
    print(f"Calculating retention matrix ({membership_type})...")

    # Filter by membership type
    if membership_type != 'all':
        df = df[df['is_member'] == membership_type].copy()

    # Add month period to check-ins
    df['activity_month'] = pd.to_datetime(df['checkin_datetime']).dt.to_period('M')

    # Merge cohorts with check-ins
    activity = df.merge(cohorts[['customer_id', 'cohort_month']], on='customer_id', how='inner')

    # Calculate months since cohort start
    activity['months_since_start'] = (activity['activity_month'] - activity['cohort_month']).apply(lambda x: x.n)

    # Create retention matrix
    retention_data = []

    for cohort in sorted(cohorts['cohort_month'].unique()):
        cohort_customers = cohorts[cohorts['cohort_month'] == cohort]['customer_id'].unique()
        cohort_size = len(cohort_customers)

        # Calculate retention for each month (0 to 12)
        for month_num in range(13):
            # Count active customers in this month
            active_customers = activity[
                (activity['cohort_month'] == cohort) &
                (activity['months_since_start'] == month_num)
            ]['customer_id'].nunique()

            retention_rate = (active_customers / cohort_size * 100) if cohort_size > 0 else 0

            retention_data.append({
                'cohort_month': str(cohort),
                'month_number': month_num,
                'cohort_size': cohort_size,
                'active_customers': active_customers,
                'retention_rate': round(retention_rate, 1),
                'membership_type': membership_type
            })

    retention_df = pd.DataFrame(retention_data)

    print(f"  ✓ Calculated retention for {retention_df['cohort_month'].nunique()} cohorts")
    print(f"  ✓ Tracking {retention_df['month_number'].max() + 1} months")

    return retention_df


def calculate_cohort_summary(retention_df, membership_type='all'):
    """
    Calculate summary statistics per cohort.

    Args:
        retention_df: DataFrame with retention matrix
        membership_type: 'Member', 'Pay-Per-Use', or 'all'

    Returns:
        DataFrame with cohort summary metrics
    """
    print(f"Calculating cohort summary ({membership_type})...")

    summary_data = []

    for cohort in retention_df['cohort_month'].unique():
        cohort_data = retention_df[retention_df['cohort_month'] == cohort]

        # Get cohort size (month 0)
        cohort_size = cohort_data[cohort_data['month_number'] == 0]['cohort_size'].iloc[0]

        # Get retention rates at key milestones
        retention_m1 = cohort_data[cohort_data['month_number'] == 1]['retention_rate'].iloc[0] if len(cohort_data[cohort_data['month_number'] == 1]) > 0 else None
        retention_m3 = cohort_data[cohort_data['month_number'] == 3]['retention_rate'].iloc[0] if len(cohort_data[cohort_data['month_number'] == 3]) > 0 else None
        retention_m6 = cohort_data[cohort_data['month_number'] == 6]['retention_rate'].iloc[0] if len(cohort_data[cohort_data['month_number'] == 6]) > 0 else None
        retention_m12 = cohort_data[cohort_data['month_number'] == 12]['retention_rate'].iloc[0] if len(cohort_data[cohort_data['month_number'] == 12]) > 0 else None

        # Calculate average retention (months 1-6)
        avg_retention_6m = cohort_data[(cohort_data['month_number'] >= 1) & (cohort_data['month_number'] <= 6)]['retention_rate'].mean()

        summary_data.append({
            'cohort_month': cohort,
            'cohort_size': cohort_size,
            'retention_month_1': retention_m1,
            'retention_month_3': retention_m3,
            'retention_month_6': retention_m6,
            'retention_month_12': retention_m12,
            'avg_retention_6_months': round(avg_retention_6m, 1),
            'membership_type': membership_type
        })

    summary_df = pd.DataFrame(summary_data)

    print(f"  ✓ Calculated summary for {len(summary_df)} cohorts")

    return summary_df


def calculate_churn_analysis(df, cohorts, membership_type='all'):
    """
    Analyze churn patterns (customers who haven't returned in 30+ days).

    Args:
        df: DataFrame with check-in data
        cohorts: DataFrame with customer_id, cohort_month, first_visit
        membership_type: 'Member', 'Pay-Per-Use', or 'all'

    Returns:
        DataFrame with churn analysis per cohort
    """
    print(f"Calculating churn analysis ({membership_type})...")

    # Filter by membership type
    if membership_type != 'all':
        df = df[df['is_member'] == membership_type].copy()

    # Get last visit per customer
    last_visits = df.groupby('customer_id')['checkin_datetime'].max().reset_index()
    last_visits.columns = ['customer_id', 'last_visit']

    # Merge with cohorts
    customer_activity = cohorts.merge(last_visits, on='customer_id', how='left')

    # Calculate days since last visit
    customer_activity['days_since_last_visit'] = (ANALYSIS_DATE - customer_activity['last_visit']).dt.days

    # Classify as churned if >30 days inactive
    customer_activity['is_churned'] = customer_activity['days_since_last_visit'] > 30

    # Calculate churn stats per cohort
    churn_data = []

    for cohort in sorted(customer_activity['cohort_month'].unique()):
        cohort_customers = customer_activity[customer_activity['cohort_month'] == cohort]
        cohort_size = len(cohort_customers)
        churned_count = cohort_customers['is_churned'].sum()
        churn_rate = (churned_count / cohort_size * 100) if cohort_size > 0 else 0

        # Calculate days since cohort start
        cohort_start_date = pd.Period(cohort).to_timestamp()
        cohort_age_days = (ANALYSIS_DATE - cohort_start_date).days

        churn_data.append({
            'cohort_month': str(cohort),
            'cohort_size': cohort_size,
            'churned_customers': churned_count,
            'active_customers': cohort_size - churned_count,
            'churn_rate': round(churn_rate, 1),
            'cohort_age_days': cohort_age_days,
            'membership_type': membership_type
        })

    churn_df = pd.DataFrame(churn_data)

    print(f"  ✓ Calculated churn for {len(churn_df)} cohorts")

    return churn_df


def main():
    """Main execution function."""
    print("\n" + "="*70)
    print("COHORT RETENTION ANALYSIS")
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
    print("GENERATING COHORT RETENTION FILES")
    print("-"*70)

    # Split by membership type
    members_df = df[df['is_member'] == 'Member'].copy()
    nonmembers_df = df[df['is_member'] == 'Pay-Per-Use'].copy()

    # --- MEMBERS ANALYSIS ---
    if len(members_df) > 0:
        # Calculate cohorts
        cohorts_members = calculate_cohorts(members_df, 'Member')

        # FILE 1: Retention matrix (MEMBERS)
        retention_members = calculate_retention_matrix(members_df, cohorts_members, 'Member')
        output_file = OUTPUT_DIR / 'cohort_retention_matrix_members.csv'
        retention_members.to_csv(output_file, index=False)
        print(f"\n1. Retention Matrix (MEMBERS)")
        print(f"  ✓ {output_file}")
        print(f"  ✓ {len(retention_members):,} rows ({retention_members['cohort_month'].nunique()} cohorts × {retention_members['month_number'].max()+1} months)")

        # FILE 2: Cohort summary (MEMBERS)
        summary_members = calculate_cohort_summary(retention_members, 'Member')
        output_file = OUTPUT_DIR / 'cohort_summary_members.csv'
        summary_members.to_csv(output_file, index=False)
        print(f"\n2. Cohort Summary (MEMBERS)")
        print(f"  ✓ {output_file}")
        print(f"  ✓ {len(summary_members)} cohorts")

        # FILE 3: Churn analysis (MEMBERS)
        churn_members = calculate_churn_analysis(members_df, cohorts_members, 'Member')
        output_file = OUTPUT_DIR / 'cohort_churn_members.csv'
        churn_members.to_csv(output_file, index=False)
        print(f"\n3. Churn Analysis (MEMBERS)")
        print(f"  ✓ {output_file}")
        print(f"  ✓ {len(churn_members)} cohorts")

    # --- NON-MEMBERS ANALYSIS ---
    if len(nonmembers_df) > 0:
        # Calculate cohorts
        cohorts_nonmembers = calculate_cohorts(nonmembers_df, 'Pay-Per-Use')

        # FILE 4: Retention matrix (NON-MEMBERS)
        retention_nonmembers = calculate_retention_matrix(nonmembers_df, cohorts_nonmembers, 'Pay-Per-Use')
        output_file = OUTPUT_DIR / 'cohort_retention_matrix_nonmembers.csv'
        retention_nonmembers.to_csv(output_file, index=False)
        print(f"\n4. Retention Matrix (NON-MEMBERS)")
        print(f"  ✓ {output_file}")
        print(f"  ✓ {len(retention_nonmembers):,} rows ({retention_nonmembers['cohort_month'].nunique()} cohorts × {retention_nonmembers['month_number'].max()+1} months)")

        # FILE 5: Cohort summary (NON-MEMBERS)
        summary_nonmembers = calculate_cohort_summary(retention_nonmembers, 'Pay-Per-Use')
        output_file = OUTPUT_DIR / 'cohort_summary_nonmembers.csv'
        summary_nonmembers.to_csv(output_file, index=False)
        print(f"\n5. Cohort Summary (NON-MEMBERS)")
        print(f"  ✓ {output_file}")
        print(f"  ✓ {len(summary_nonmembers)} cohorts")

        # FILE 6: Churn analysis (NON-MEMBERS)
        churn_nonmembers = calculate_churn_analysis(nonmembers_df, cohorts_nonmembers, 'Pay-Per-Use')
        output_file = OUTPUT_DIR / 'cohort_churn_nonmembers.csv'
        churn_nonmembers.to_csv(output_file, index=False)
        print(f"\n6. Churn Analysis (NON-MEMBERS)")
        print(f"  ✓ {output_file}")
        print(f"  ✓ {len(churn_nonmembers)} cohorts")

    # Summary statistics
    print("\n" + "-"*70)
    print("COHORT RETENTION SUMMARY")
    print("-"*70)

    if len(members_df) > 0:
        print(f"\nMEMBERS:")
        print(f"  Total cohorts: {len(summary_members)}")
        print(f"  Date range: {summary_members['cohort_month'].min()} to {summary_members['cohort_month'].max()}")
        print(f"  Average cohort size: {summary_members['cohort_size'].mean():.0f} customers")
        print(f"  Average 1-month retention: {summary_members['retention_month_1'].mean():.1f}%")
        print(f"  Average 3-month retention: {summary_members['retention_month_3'].mean():.1f}%")
        print(f"  Average 6-month retention: {summary_members['retention_month_6'].mean():.1f}%")
        print(f"\n  Overall churn rate: {churn_members['churn_rate'].mean():.1f}%")
        print(f"  Churned customers: {churn_members['churned_customers'].sum():,}")
        print(f"  Active customers: {churn_members['active_customers'].sum():,}")

    if len(nonmembers_df) > 0:
        print(f"\nNON-MEMBERS:")
        print(f"  Total cohorts: {len(summary_nonmembers)}")
        print(f"  Date range: {summary_nonmembers['cohort_month'].min()} to {summary_nonmembers['cohort_month'].max()}")
        print(f"  Average cohort size: {summary_nonmembers['cohort_size'].mean():.0f} customers")
        print(f"  Average 1-month retention: {summary_nonmembers['retention_month_1'].mean():.1f}%")
        print(f"  Average 3-month retention: {summary_nonmembers['retention_month_3'].mean():.1f}%")
        print(f"\n  Overall churn rate: {churn_nonmembers['churn_rate'].mean():.1f}%")
        print(f"  Churned customers: {churn_nonmembers['churned_customers'].sum():,}")
        print(f"  Active customers: {churn_nonmembers['active_customers'].sum():,}")

    print("\n" + "="*70)
    print("✅ COHORT RETENTION ANALYSIS COMPLETE")
    print("="*70)
    print()


if __name__ == '__main__':
    main()
