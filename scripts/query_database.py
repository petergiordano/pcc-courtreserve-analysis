#!/usr/bin/env python3
"""
Query utility for CourtReserve SQLite database.

Usage:
    python3 scripts/query_database.py

This script provides common queries and utilities for analyzing the
CourtReserve database.
"""

import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = 'courtreserve.db'


def connect_db():
    """Connect to the database."""
    return sqlite3.connect(DB_PATH)


def run_query(sql, params=None):
    """Run a SQL query and return results as DataFrame."""
    conn = connect_db()
    if params:
        df = pd.read_sql_query(sql, conn, params=params)
    else:
        df = pd.read_sql_query(sql, conn)
    conn.close()
    return df


# ============================================================================
# Common Queries
# ============================================================================

def get_table_counts():
    """Get record count for all tables."""
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    print("=" * 80)
    print("TABLE RECORD COUNTS")
    print("=" * 80)

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"   {table[0]:30s} {count:>10,} records")

    conn.close()


def get_date_ranges():
    """Show date ranges for each table."""
    queries = {
        'Reservations': """
            SELECT
                MIN(start_datetime) as earliest,
                MAX(start_datetime) as latest,
                COUNT(DISTINCT DATE(start_datetime)) as days
            FROM reservations
            WHERE start_datetime IS NOT NULL
        """,
        'Check-ins': """
            SELECT
                MIN(checkin_datetime) as earliest,
                MAX(checkin_datetime) as latest,
                COUNT(DISTINCT DATE(checkin_datetime)) as days
            FROM checkins
            WHERE checkin_datetime IS NOT NULL
        """,
        'Court Utilization': """
            SELECT
                MIN(date) as earliest,
                MAX(date) as latest,
                COUNT(DISTINCT date) as days
            FROM court_utilization
            WHERE date IS NOT NULL
        """,
        'Event Registrants': """
            SELECT
                MIN(event_date) as earliest,
                MAX(event_date) as latest,
                COUNT(DISTINCT event_date) as days
            FROM event_registrants
            WHERE event_date IS NOT NULL
        """,
    }

    print("\n" + "=" * 80)
    print("DATE RANGES")
    print("=" * 80)

    for name, sql in queries.items():
        df = run_query(sql)
        if not df.empty and df.iloc[0]['earliest']:
            earliest = df.iloc[0]['earliest']
            latest = df.iloc[0]['latest']
            days = df.iloc[0]['days']
            print(f"\n{name}:")
            print(f"   Earliest: {earliest}")
            print(f"   Latest:   {latest}")
            print(f"   Days:     {days}")


def get_member_summary():
    """Get member summary statistics."""
    sql = """
        SELECT
            membership_status,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as pct
        FROM members
        GROUP BY membership_status
        ORDER BY count DESC
    """

    print("\n" + "=" * 80)
    print("MEMBER STATUS BREAKDOWN")
    print("=" * 80)

    df = run_query(sql)
    for _, row in df.iterrows():
        print(f"   {row['membership_status']:20s} {row['count']:>6,} ({row['pct']:>5.1f}%)")

    # Member type breakdown
    sql = """
        SELECT
            membership_type,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as pct
        FROM members
        WHERE membership_status = 'Active'
        GROUP BY membership_type
        ORDER BY count DESC
    """

    print("\n" + "=" * 80)
    print("ACTIVE MEMBER TYPE BREAKDOWN")
    print("=" * 80)

    df = run_query(sql)
    for _, row in df.iterrows():
        print(f"   {row['membership_type']:20s} {row['count']:>6,} ({row['pct']:>5.1f}%)")


def get_pay_per_use_summary():
    """Get pay-per-use (non-member) check-in summary."""
    sql = """
        SELECT
            COUNT(DISTINCT player__) as unique_players,
            COUNT(*) as total_checkins,
            AVG(price_amount) as avg_price,
            SUM(price_amount) as total_spent
        FROM checkins
        WHERE membership_name LIKE '%Non-Member%'
           OR membership_name LIKE '%Visitor%'
           OR registration_type = 'Drop-In'
    """

    print("\n" + "=" * 80)
    print("PAY-PER-USE SEGMENT SUMMARY")
    print("=" * 80)

    df = run_query(sql)
    if not df.empty:
        row = df.iloc[0]
        print(f"   Unique Players:  {row['unique_players']:>6,}")
        print(f"   Total Check-ins: {row['total_checkins']:>6,}")
        print(f"   Average Price:   ${row['avg_price']:>6.2f}")
        print(f"   Total Spent:     ${row['total_spent']:>10,.2f}")

    # Top spenders
    sql = """
        SELECT
            player__,
            player_first_name || ' ' || player_last_name as player_name,
            COUNT(*) as visits,
            SUM(price_amount) as total_spent,
            ROUND(SUM(price_amount) / 4.0, 2) as monthly_avg
        FROM checkins
        WHERE (membership_name LIKE '%Non-Member%'
           OR membership_name LIKE '%Visitor%'
           OR registration_type = 'Drop-In')
          AND price_amount > 0
        GROUP BY player__
        HAVING SUM(price_amount) > 80
        ORDER BY total_spent DESC
        LIMIT 10
    """

    print("\n" + "=" * 80)
    print("TOP 10 PAY-PER-USE SPENDERS (>$80 total)")
    print("=" * 80)

    df = run_query(sql)
    if not df.empty:
        for _, row in df.iterrows():
            print(f"   {row['player_name']:25s} {row['visits']:>3} visits  ${row['total_spent']:>7.2f}  (${row['monthly_avg']:>6.2f}/mo avg)")


def get_shadow_market_summary():
    """Get weekday daytime (9 AM-4 PM) utilization summary."""
    sql = """
        SELECT
            AVG(utilization_pct) as avg_utilization,
            MIN(utilization_pct) as min_utilization,
            MAX(utilization_pct) as max_utilization
        FROM court_utilization
        WHERE CAST(strftime('%w', date) AS INTEGER) BETWEEN 1 AND 5  -- Monday-Friday
          AND time_slot BETWEEN '9:00 AM - 10:00 AM' AND '3:00 PM - 4:00 PM'
          AND utilization_pct IS NOT NULL
    """

    print("\n" + "=" * 80)
    print("SHADOW MARKET (Weekday 9 AM-4 PM) SUMMARY")
    print("=" * 80)

    df = run_query(sql)
    if not df.empty:
        row = df.iloc[0]
        print(f"   Average Utilization: {row['avg_utilization']:>5.1f}%")
        print(f"   Min Utilization:     {row['min_utilization']:>5.1f}%")
        print(f"   Max Utilization:     {row['max_utilization']:>5.1f}%")
        print(f"   Empty Capacity:      {100 - row['avg_utilization']:>5.1f}%")


def get_top_activity_types():
    """Get top activity types from check-ins."""
    sql = """
        SELECT
            event_name,
            COUNT(*) as checkins,
            COUNT(DISTINCT player__) as unique_players,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as pct
        FROM checkins
        WHERE event_name IS NOT NULL AND event_name != ''
        GROUP BY event_name
        ORDER BY checkins DESC
        LIMIT 10
    """

    print("\n" + "=" * 80)
    print("TOP 10 ACTIVITY TYPES (by check-ins)")
    print("=" * 80)

    df = run_query(sql)
    for _, row in df.iterrows():
        print(f"   {row['event_name'][:50]:50s} {row['checkins']:>6,} ({row['pct']:>4.1f}%)")


# ============================================================================
# Custom Query Examples
# ============================================================================

def example_custom_queries():
    """Show examples of custom queries users can run."""
    print("\n" + "=" * 80)
    print("CUSTOM QUERY EXAMPLES")
    print("=" * 80)

    examples = [
        {
            'title': '1. Reservations by Day of Week',
            'sql': """
                SELECT
                    CASE CAST(strftime('%w', start_datetime) AS INTEGER)
                        WHEN 0 THEN 'Sunday'
                        WHEN 1 THEN 'Monday'
                        WHEN 2 THEN 'Tuesday'
                        WHEN 3 THEN 'Wednesday'
                        WHEN 4 THEN 'Thursday'
                        WHEN 5 THEN 'Friday'
                        WHEN 6 THEN 'Saturday'
                    END as day_of_week,
                    COUNT(*) as reservations
                FROM reservations
                WHERE start_datetime IS NOT NULL
                GROUP BY CAST(strftime('%w', start_datetime) AS INTEGER)
                ORDER BY CAST(strftime('%w', start_datetime) AS INTEGER)
            """
        },
        {
            'title': '2. Member Join Trends by Month',
            'sql': """
                SELECT
                    strftime('%Y-%m', membership_start_date) as month,
                    COUNT(*) as new_members
                FROM members
                WHERE membership_start_date IS NOT NULL
                GROUP BY month
                ORDER BY month DESC
                LIMIT 12
            """
        },
        {
            'title': '3. Busiest Hours by Day of Week',
            'sql': """
                SELECT
                    CASE CAST(strftime('%w', date) AS INTEGER)
                        WHEN 0 THEN 'Sunday'
                        WHEN 1 THEN 'Monday'
                        WHEN 2 THEN 'Tuesday'
                        WHEN 3 THEN 'Wednesday'
                        WHEN 4 THEN 'Thursday'
                        WHEN 5 THEN 'Friday'
                        WHEN 6 THEN 'Saturday'
                    END as day_of_week,
                    time_slot,
                    AVG(utilization_pct) as avg_utilization
                FROM court_utilization
                WHERE utilization_pct IS NOT NULL
                GROUP BY CAST(strftime('%w', date) AS INTEGER), time_slot
                ORDER BY avg_utilization DESC
                LIMIT 10
            """
        },
    ]

    for example in examples:
        print(f"\n{example['title']}:")
        print(f"```sql")
        print(example['sql'].strip())
        print(f"```")


# ============================================================================
# Main
# ============================================================================

def main():
    """Run all summary queries."""
    print("\n" + "=" * 80)
    print("COURTRESERVE DATABASE SUMMARY")
    print(f"Database: {DB_PATH}")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    try:
        get_table_counts()
        get_date_ranges()
        get_member_summary()
        get_pay_per_use_summary()
        get_shadow_market_summary()
        get_top_activity_types()
        example_custom_queries()

        print("\n" + "=" * 80)
        print("To run custom queries:")
        print("=" * 80)
        print(f"\nPython:")
        print(f"   from scripts.query_database import run_query")
        print(f"   df = run_query('SELECT * FROM members LIMIT 10')")
        print(f"   print(df)")

        print(f"\nSQLite CLI:")
        print(f"   sqlite3 {DB_PATH}")
        print(f"   .tables")
        print(f"   SELECT COUNT(*) FROM reservations;")

        print(f"\nPandas:")
        print(f"   import pandas as pd")
        print(f"   import sqlite3")
        print(f"   conn = sqlite3.connect('{DB_PATH}')")
        print(f"   df = pd.read_sql_query('SELECT * FROM members', conn)")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"\nMake sure to run 'python3 scripts/create_database.py' first!")


if __name__ == '__main__':
    main()
