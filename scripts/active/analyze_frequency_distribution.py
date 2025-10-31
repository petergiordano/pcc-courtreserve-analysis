#!/usr/bin/env python3
"""
Frequency Distribution Analysis for PCC Customer Intelligence

Purpose: Segment customers by usage intensity for targeted campaigns
Output: 3 CSV files optimized for Google Sheets visualization

Business Context:
- Identify 2,008 pay-per-use customers for $477K conversion campaign
- Segment by usage intensity: daily/weekly/monthly/occasional
- Calculate DAU/WAU/MAU ratios for product stickiness
- Flag churn risk customers (days_since_last_visit > 30)

Author: Claude Code (Anthropic)
Date: October 29, 2025
"""

import sys
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Add scripts directory to path for imports
sys.path.append(str(Path(__file__).parent))

from db_loader import CourtReserveDB

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent.parent / 'deliverables' / 'data' / 'verified'

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_checkins_data():
    """Load check-ins data from SQLite database using db_loader."""
    with CourtReserveDB() as db:
        df = db.get_checkins()

    # Filter to only checked-in records (not no-shows)
    df = df[df['check_in_status'] == 'Checked-In'].copy()

    # Rename columns for consistency
    df = df.rename(columns={
        'player__#': 'customer_id',
        'paid_amount': 'price_amount'
    })

    # Ensure customer_id is integer type
    df['customer_id'] = df['customer_id'].astype(int)

    # Convert datetime (check_in_date_time already exists from db_loader)
    df['checkin_datetime'] = pd.to_datetime(df['check_in_date_time'])
    df['checkin_date'] = df['checkin_datetime'].dt.date

    # Get membership status from members table
    with CourtReserveDB() as db:
        members = db.get_members()

    # Extract member_#, membership_status, and current_membership
    members_status = members[['member_#', 'membership_status', 'current_membership']].copy()

    # Clean member_# column - convert to int, handling errors
    members_status['member_#'] = pd.to_numeric(members_status['member_#'], errors='coerce')
    members_status = members_status.dropna(subset=['member_#'])
    members_status['member_#'] = members_status['member_#'].astype(int)
    members_status = members_status.rename(columns={'member_#': 'customer_id'})

    # Merge membership status
    df = df.merge(members_status, on='customer_id', how='left')

    # Fill missing membership status with 'No Membership'
    df['membership_status'] = df['membership_status'].fillna('No Membership')
    df['current_membership'] = df['current_membership'].fillna('')

    # Add is_member flag for filtering
    # FIXED: Correctly identify PAID members vs free "Non-Member/Visitor" accounts
    df['is_member'] = df.apply(
        lambda row: 'Member' if (
            row['membership_status'] == 'Currently Active' and
            row['current_membership'] and
            'Non-Member' not in str(row['current_membership']) and
            'Visitor' not in str(row['current_membership'])
        ) else 'Pay-Per-Use',
        axis=1
    )

    return df


def calculate_frequency_metrics(df):
    """Calculate per-customer frequency metrics."""

    # Get date range for analysis
    min_date = df['checkin_datetime'].min()
    max_date = df['checkin_datetime'].max()
    analysis_days = (max_date - min_date).days
    analysis_months = analysis_days / 30.44  # Avg days per month

    print(f"Analysis period: {min_date.date()} to {max_date.date()}")
    print(f"Total days: {analysis_days}, Total months: {analysis_months:.1f}")

    # Build customer metrics step by step
    customer_metrics = []

    for customer_id, group in df.groupby('customer_id'):
        total_visits = len(group)
        first_visit = group['checkin_datetime'].min()
        last_visit = group['checkin_datetime'].max()
        unique_days = group['checkin_date'].nunique()
        total_spend = group['paid_amount'].sum() if 'paid_amount' in group.columns else 0.0

        # Get membership status from the group (should be consistent across all visits)
        membership_status = group['membership_status'].mode()[0] if len(group['membership_status'].mode()) > 0 else 'Unknown'

        # Get is_member from group (already calculated correctly in load_checkins_data)
        is_member = group['is_member'].mode()[0] if len(group['is_member'].mode()) > 0 else 'Pay-Per-Use'

        customer_metrics.append({
            'customer_id': customer_id,
            'total_visits': total_visits,
            'first_visit': first_visit,
            'last_visit': last_visit,
            'unique_days': unique_days,
            'total_spend': total_spend,
            'membership_status': membership_status,
            'is_member': is_member
        })

    customer_metrics = pd.DataFrame(customer_metrics)

    # Calculate derived metrics
    customer_metrics['days_active'] = (customer_metrics['last_visit'] - customer_metrics['first_visit']).dt.days + 1
    customer_metrics['visits_per_month'] = (customer_metrics['total_visits'] / customer_metrics['days_active'] * 30.44).round(2)
    customer_metrics['days_since_last_visit'] = (max_date - customer_metrics['last_visit']).dt.days
    customer_metrics['avg_days_between_visits'] = (customer_metrics['days_active'] / customer_metrics['total_visits']).round(1)

    # Frequency segmentation
    def classify_frequency(visits_per_month):
        if visits_per_month >= 20:
            return 'Daily User'
        elif visits_per_month >= 4:
            return 'Weekly User'
        elif visits_per_month >= 2:
            return 'Monthly User'
        else:
            return 'Occasional User'

    customer_metrics['frequency_segment'] = customer_metrics['visits_per_month'].apply(classify_frequency)

    # Churn risk flag (no visit in 30+ days)
    customer_metrics['churn_risk'] = customer_metrics['days_since_last_visit'].apply(
        lambda x: 'High Risk' if x > 30 else 'Active'
    )

    # Lifetime value estimate (annualized spend)
    customer_metrics['estimated_annual_ltv'] = (customer_metrics['total_spend'] / customer_metrics['days_active'] * 365).round(2)

    return customer_metrics


def calculate_dau_wau_mau(df):
    """Calculate daily active users, weekly active users, monthly active users."""

    # Get all dates in range
    min_date = df['checkin_date'].min()
    max_date = df['checkin_date'].max()

    # Daily active users
    dau = df.groupby('checkin_date')['customer_id'].nunique().reset_index()
    dau.columns = ['date', 'dau']
    dau['date'] = pd.to_datetime(dau['date'])

    # Calculate rolling WAU (7-day window)
    df['checkin_date_dt'] = pd.to_datetime(df['checkin_date'])

    wau_records = []
    for date in pd.date_range(min_date, max_date, freq='D'):
        week_start = date - timedelta(days=6)
        week_users = df[
            (df['checkin_date_dt'] >= week_start) &
            (df['checkin_date_dt'] <= date)
        ]['customer_id'].nunique()
        wau_records.append({'date': date, 'wau': week_users})

    wau = pd.DataFrame(wau_records)

    # Calculate rolling MAU (30-day window)
    mau_records = []
    for date in pd.date_range(min_date, max_date, freq='D'):
        month_start = date - timedelta(days=29)
        month_users = df[
            (df['checkin_date_dt'] >= month_start) &
            (df['checkin_date_dt'] <= date)
        ]['customer_id'].nunique()
        mau_records.append({'date': date, 'mau': month_users})

    mau = pd.DataFrame(mau_records)

    # Merge all metrics
    stickiness = dau.merge(wau, on='date', how='outer').merge(mau, on='date', how='outer')

    # Calculate ratios
    stickiness['dau_mau_ratio'] = (stickiness['dau'] / stickiness['mau']).round(3)
    stickiness['dau_wau_ratio'] = (stickiness['dau'] / stickiness['wau']).round(3)
    stickiness['wau_mau_ratio'] = (stickiness['wau'] / stickiness['mau']).round(3)

    # Sort by date
    stickiness = stickiness.sort_values('date')

    return stickiness


def create_frequency_summary(customer_metrics):
    """Create segment-level summary statistics."""

    summary = customer_metrics.groupby('frequency_segment').agg(
        customer_count=('customer_id', 'count'),
        avg_visits_per_month=('visits_per_month', 'mean'),
        avg_total_visits=('total_visits', 'mean'),
        avg_total_spend=('total_spend', 'mean'),
        avg_annual_ltv=('estimated_annual_ltv', 'mean'),
        member_count=('is_member', lambda x: (x == 'Member').sum()),
        pay_per_use_count=('is_member', lambda x: (x == 'Pay-Per-Use').sum()),
        high_churn_risk_count=('churn_risk', lambda x: (x == 'High Risk').sum())
    ).reset_index()

    # Calculate percentages
    total_customers = summary['customer_count'].sum()
    summary['pct_of_total'] = (summary['customer_count'] / total_customers * 100).round(1)
    summary['member_pct'] = (summary['member_count'] / summary['customer_count'] * 100).round(1)
    summary['churn_risk_pct'] = (summary['high_churn_risk_count'] / summary['customer_count'] * 100).round(1)

    # Round numeric columns
    summary['avg_visits_per_month'] = summary['avg_visits_per_month'].round(1)
    summary['avg_total_visits'] = summary['avg_total_visits'].round(0)
    summary['avg_total_spend'] = summary['avg_total_spend'].round(2)
    summary['avg_annual_ltv'] = summary['avg_annual_ltv'].round(2)

    # Sort by frequency (Daily > Weekly > Monthly > Occasional)
    frequency_order = ['Daily User', 'Weekly User', 'Monthly User', 'Occasional User']
    summary['sort_order'] = summary['frequency_segment'].apply(lambda x: frequency_order.index(x))
    summary = summary.sort_values('sort_order').drop('sort_order', axis=1)

    return summary


def main():
    """Main execution function."""

    print("=" * 80)
    print("FREQUENCY DISTRIBUTION ANALYSIS")
    print("=" * 80)
    print()

    # Load data
    print("Loading check-ins data from database...")
    df = load_checkins_data()
    print(f"Loaded {len(df):,} check-ins from {df['customer_id'].nunique():,} unique customers")
    print()

    # Calculate per-customer frequency metrics
    print("Calculating per-customer frequency metrics...")
    customer_metrics = calculate_frequency_metrics(df)
    print(f"Processed {len(customer_metrics):,} customers")
    print()

    # Calculate DAU/WAU/MAU
    print("Calculating DAU/WAU/MAU stickiness metrics...")
    stickiness = calculate_dau_wau_mau(df)
    print(f"Calculated stickiness for {len(stickiness):,} days")
    print()

    # Create summary
    print("Creating frequency segment summary...")
    summary = create_frequency_summary(customer_metrics)
    print(f"Segmented into {len(summary)} frequency groups")
    print()

    # Save outputs (split by membership status)
    print("Saving CSV files...")

    # Prepare output columns
    output_columns = [
        'customer_id', 'total_visits', 'unique_days', 'first_visit', 'last_visit',
        'days_active', 'visits_per_month', 'avg_days_between_visits',
        'days_since_last_visit', 'frequency_segment', 'is_member',
        'churn_risk', 'total_spend', 'estimated_annual_ltv'
    ]

    # Split customer metrics by membership status
    members = customer_metrics[customer_metrics['is_member'] == 'Member'].copy()
    non_members = customer_metrics[customer_metrics['is_member'] == 'Pay-Per-Use'].copy()

    # File 1a: Per-customer frequency distribution (MEMBERS)
    output_file_1a = OUTPUT_DIR / 'frequency_distribution_members.csv'
    if len(members) > 0:
        members[output_columns].to_csv(output_file_1a, index=False)
        print(f"  ✓ {output_file_1a} ({len(members):,} members)")
    else:
        print(f"  ⚠ No members found - skipping members file")

    # File 1b: Per-customer frequency distribution (NON-MEMBERS)
    output_file_1b = OUTPUT_DIR / 'frequency_distribution_nonmembers.csv'
    if len(non_members) > 0:
        non_members[output_columns].to_csv(output_file_1b, index=False)
        print(f"  ✓ {output_file_1b} ({len(non_members):,} non-members)")
    else:
        print(f"  ⚠ No non-members found - skipping non-members file")

    # File 2a: Frequency segment summary (MEMBERS)
    output_file_2a = OUTPUT_DIR / 'frequency_summary_members.csv'
    if len(members) > 0:
        summary_members = create_frequency_summary(members)
        summary_members.to_csv(output_file_2a, index=False)
        print(f"  ✓ {output_file_2a}")
    else:
        print(f"  ⚠ No members - skipping members summary")

    # File 2b: Frequency segment summary (NON-MEMBERS)
    output_file_2b = OUTPUT_DIR / 'frequency_summary_nonmembers.csv'
    if len(non_members) > 0:
        summary_non_members = create_frequency_summary(non_members)
        summary_non_members.to_csv(output_file_2b, index=False)
        print(f"  ✓ {output_file_2b}")
    else:
        print(f"  ⚠ No non-members - skipping non-members summary")

    # File 3a: DAU/WAU/MAU stickiness (MEMBERS)
    output_file_3a = OUTPUT_DIR / 'dau_wau_mau_members.csv'
    if len(members) > 0:
        df_members = df[df['is_member'] == 'Member']
        stickiness_members = calculate_dau_wau_mau(df_members)
        stickiness_members.to_csv(output_file_3a, index=False)
        print(f"  ✓ {output_file_3a}")
    else:
        print(f"  ⚠ No members - skipping members stickiness")

    # File 3b: DAU/WAU/MAU stickiness (NON-MEMBERS)
    output_file_3b = OUTPUT_DIR / 'dau_wau_mau_nonmembers.csv'
    if len(non_members) > 0:
        df_non_members = df[df['is_member'] == 'Pay-Per-Use']
        stickiness_non_members = calculate_dau_wau_mau(df_non_members)
        stickiness_non_members.to_csv(output_file_3b, index=False)
        print(f"  ✓ {output_file_3b}")
    else:
        print(f"  ⚠ No non-members - skipping non-members stickiness")

    print()
    print("=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    print()

    # Overall membership split
    print(f"MEMBERSHIP BREAKDOWN:")
    print(f"  Total customers: {len(customer_metrics):,}")
    print(f"  Members: {len(members):,} ({len(members)/len(customer_metrics)*100:.1f}%)")
    print(f"  Non-Members (Pay-Per-Use): {len(non_members):,} ({len(non_members)/len(customer_metrics)*100:.1f}%)")
    print()

    # Members segment breakdown
    if len(members) > 0:
        print("MEMBERS - FREQUENCY SEGMENT BREAKDOWN:")
        print(summary_members[['frequency_segment', 'customer_count', 'pct_of_total', 'avg_visits_per_month', 'avg_annual_ltv']].to_string(index=False))
        print()

        # Member churn risk
        members_high_risk = members[members['churn_risk'] == 'High Risk']
        print(f"MEMBERS - CHURN RISK:")
        print(f"  High risk members (30+ days inactive): {len(members_high_risk):,} ({len(members_high_risk)/len(members)*100:.1f}%)")
        print(f"  At-risk annual value: ${members_high_risk['estimated_annual_ltv'].sum():,.0f}")
        print()

        # Member stickiness
        recent_stickiness_members = stickiness_members.tail(30)
        print(f"MEMBERS - PRODUCT STICKINESS (Last 30 Days):")
        print(f"  Avg DAU/MAU ratio: {recent_stickiness_members['dau_mau_ratio'].mean():.1%}")
        print(f"  Avg DAU/WAU ratio: {recent_stickiness_members['dau_wau_ratio'].mean():.1%}")
        print(f"  Avg MAU: {recent_stickiness_members['mau'].mean():.0f} unique members/month")
        print()

    # Non-members segment breakdown
    if len(non_members) > 0:
        print("NON-MEMBERS - FREQUENCY SEGMENT BREAKDOWN:")
        print(summary_non_members[['frequency_segment', 'customer_count', 'pct_of_total', 'avg_visits_per_month', 'avg_annual_ltv']].to_string(index=False))
        print()

        # Pay-per-use conversion opportunity
        print(f"NON-MEMBERS - CONVERSION OPPORTUNITY:")
        print(f"  Total non-member customers: {len(non_members):,}")
        print(f"  Total annual spend: ${non_members['estimated_annual_ltv'].sum():,.0f}")
        print(f"  Avg spend per customer: ${non_members['estimated_annual_ltv'].mean():,.0f}/year")
        print()

        # Non-member churn risk
        non_members_high_risk = non_members[non_members['churn_risk'] == 'High Risk']
        print(f"NON-MEMBERS - CHURN RISK:")
        print(f"  High risk non-members (30+ days inactive): {len(non_members_high_risk):,} ({len(non_members_high_risk)/len(non_members)*100:.1f}%)")
        print(f"  Potential lost conversions: {len(non_members_high_risk):,} customers")
        print()

        # Non-member stickiness
        recent_stickiness_non_members = stickiness_non_members.tail(30)
        print(f"NON-MEMBERS - PRODUCT STICKINESS (Last 30 Days):")
        print(f"  Avg DAU/MAU ratio: {recent_stickiness_non_members['dau_mau_ratio'].mean():.1%}")
        print(f"  Avg DAU/WAU ratio: {recent_stickiness_non_members['dau_wau_ratio'].mean():.1%}")
        print(f"  Avg MAU: {recent_stickiness_non_members['mau'].mean():.0f} unique non-members/month")
        print()

    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()
