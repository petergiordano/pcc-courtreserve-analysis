#!/usr/bin/env python3
"""
Create SQLite database from CourtReserve CSV exports.

This script imports all CourtReserve CSV files into a local SQLite database
for easier querying and analysis.

Usage:
    python3 scripts/create_database.py

Output:
    courtreserve.db (SQLite database file in repository root)

Tables created:
    - reservations
    - members
    - checkins
    - court_utilization
    - cancellations
    - event_registrants
    - transactions
    - events
    - instructors
    - sales_summary

Database file size: ~50-100MB (depending on data volume)
"""

import sqlite3
import pandas as pd
import os
import glob
from datetime import datetime

# Database file location
DB_PATH = 'courtreserve.db'

# CSV file patterns (finds most recent versions)
CSV_PATTERNS = {
    'reservations': 'ReservationReport_*.csv',
    'members': 'MembersReport_*.csv',
    'checkins': 'CheckinReports*.csv',
    'court_utilization': 'CourtUtilization-by-date.csv',
    'cancellations': 'Cancellation_Report_*.csv',
    'event_registrants': 'EventRegistrantsReports*.csv',
    'transactions': 'Transactions*.csv',
    'events': 'Event_Summary*.csv',
    'event_list': 'Event_List.csv',
    'instructors': 'InstructorReport_*.csv',
    'sales_summary': 'SalesReport*.csv',
}


def find_latest_csv(pattern):
    """Find the most recent CSV file matching the pattern."""
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by file size (larger = more comprehensive) and modification time
    files.sort(key=lambda x: (os.path.getsize(x), os.path.getmtime(x)), reverse=True)
    return files[0]


def create_database():
    """Create SQLite database and import all CSV files."""

    # Remove existing database
    if os.path.exists(DB_PATH):
        print(f"Removing existing database: {DB_PATH}")
        os.remove(DB_PATH)

    # Create new database connection
    print(f"\nCreating new database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)

    tables_created = 0
    total_records = 0

    print("\n" + "=" * 80)
    print("IMPORTING CSV FILES TO DATABASE")
    print("=" * 80)

    # Import Reservations
    csv_file = find_latest_csv(CSV_PATTERNS['reservations'])
    if csv_file:
        print(f"\n1. Importing Reservations from: {csv_file}")
        df = pd.read_csv(csv_file, encoding='utf-8-sig', low_memory=False)

        # Clean column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('/', '_')

        # Parse dates
        if 'start_date___time' in df.columns:
            df['start_datetime'] = pd.to_datetime(df['start_date___time'], errors='coerce')
        if 'end_date___time' in df.columns:
            df['end_datetime'] = pd.to_datetime(df['end_date___time'], errors='coerce')
        if 'created_on' in df.columns:
            df['created_on'] = pd.to_datetime(df['created_on'], errors='coerce')

        df.to_sql('reservations', conn, if_exists='replace', index=False)
        print(f"   ✓ Imported {len(df):,} reservations")
        tables_created += 1
        total_records += len(df)
    else:
        print(f"\n1. ⚠️  Reservations CSV not found (pattern: {CSV_PATTERNS['reservations']})")

    # Import Members
    csv_file = find_latest_csv(CSV_PATTERNS['members'])
    if csv_file:
        print(f"\n2. Importing Members from: {csv_file}")
        df = pd.read_csv(csv_file, encoding='utf-8-sig', low_memory=False)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('/', '_')

        # Parse dates
        if 'current_membership_start_date' in df.columns:
            df['membership_start_date'] = pd.to_datetime(df['current_membership_start_date'], errors='coerce')
        if 'date_of_birth' in df.columns:
            df['date_of_birth'] = pd.to_datetime(df['date_of_birth'], errors='coerce')

        df.to_sql('members', conn, if_exists='replace', index=False)
        print(f"   ✓ Imported {len(df):,} members")
        tables_created += 1
        total_records += len(df)
    else:
        print(f"\n2. ⚠️  Members CSV not found (pattern: {CSV_PATTERNS['members']})")

    # Import Check-ins
    csv_file = find_latest_csv(CSV_PATTERNS['checkins'])
    if csv_file:
        print(f"\n3. Importing Check-ins from: {csv_file}")
        df = pd.read_csv(csv_file, encoding='utf-8-sig', low_memory=False)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('/', '_').str.replace('-', '_')

        # Parse dates
        if 'check_in_date_time' in df.columns:
            df['checkin_datetime'] = pd.to_datetime(df['check_in_date_time'], errors='coerce')

        # Parse price from strings like "(Drop-in) $16.00"
        if 'price' in df.columns:
            df['price_amount'] = df['price'].str.extract(r'\$(\d+\.?\d*)')[0].astype(float)

        df.to_sql('checkins', conn, if_exists='replace', index=False)
        print(f"   ✓ Imported {len(df):,} check-ins")
        tables_created += 1
        total_records += len(df)
    else:
        print(f"\n3. ⚠️  Check-ins CSV not found (pattern: {CSV_PATTERNS['checkins']})")

    # Import Court Utilization
    csv_file = find_latest_csv(CSV_PATTERNS['court_utilization'])
    if csv_file:
        print(f"\n4. Importing Court Utilization from: {csv_file}")
        df = pd.read_csv(csv_file, encoding='utf-8-sig', low_memory=False, skiprows=1)

        # Rename first column to time_slot
        df.columns = [df.columns[0]] + list(df.columns[1:])
        df = df.rename(columns={df.columns[0]: 'time_slot'})

        # Melt to long format (time_slot, date, utilization_pct)
        id_vars = ['time_slot']
        value_vars = [col for col in df.columns if col != 'time_slot']

        df_long = df.melt(id_vars=id_vars, value_vars=value_vars,
                         var_name='date', value_name='utilization_pct')

        # Parse utilization percentage
        df_long['utilization_pct'] = df_long['utilization_pct'].str.replace(' %', '').str.replace('%', '')
        df_long['utilization_pct'] = pd.to_numeric(df_long['utilization_pct'], errors='coerce')

        # Parse date
        df_long['date'] = pd.to_datetime(df_long['date'], errors='coerce')

        df_long.to_sql('court_utilization', conn, if_exists='replace', index=False)
        print(f"   ✓ Imported {len(df_long):,} utilization records ({len(df)} time slots × {len(value_vars)} dates)")
        tables_created += 1
        total_records += len(df_long)
    else:
        print(f"\n4. ⚠️  Court Utilization CSV not found (pattern: {CSV_PATTERNS['court_utilization']})")

    # Import Cancellations
    csv_file = find_latest_csv(CSV_PATTERNS['cancellations'])
    if csv_file:
        print(f"\n5. Importing Cancellations from: {csv_file}")
        df = pd.read_csv(csv_file, encoding='utf-8-sig', low_memory=False)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('/', '_')

        # Parse dates
        if 'start_date___time' in df.columns:
            df['start_datetime'] = pd.to_datetime(df['start_date___time'], errors='coerce')
        if 'cancelled_on' in df.columns:
            df['cancelled_on'] = pd.to_datetime(df['cancelled_on'], errors='coerce')

        df.to_sql('cancellations', conn, if_exists='replace', index=False)
        print(f"   ✓ Imported {len(df):,} cancellations")
        tables_created += 1
        total_records += len(df)
    else:
        print(f"\n5. ⚠️  Cancellations CSV not found (pattern: {CSV_PATTERNS['cancellations']})")

    # Import Event Registrants
    csv_file = find_latest_csv(CSV_PATTERNS['event_registrants'])
    if csv_file:
        print(f"\n6. Importing Event Registrants from: {csv_file}")
        df = pd.read_csv(csv_file, encoding='utf-8-sig', low_memory=False)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('/', '_')

        # Parse dates
        if 'event_date' in df.columns:
            df['event_date'] = pd.to_datetime(df['event_date'], errors='coerce')

        df.to_sql('event_registrants', conn, if_exists='replace', index=False)
        print(f"   ✓ Imported {len(df):,} event registrations")
        tables_created += 1
        total_records += len(df)
    else:
        print(f"\n6. ⚠️  Event Registrants CSV not found (pattern: {CSV_PATTERNS['event_registrants']})")

    # Import Transactions
    csv_file = find_latest_csv(CSV_PATTERNS['transactions'])
    if csv_file:
        print(f"\n7. Importing Transactions from: {csv_file}")
        df = pd.read_csv(csv_file, encoding='utf-8-sig', low_memory=False)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('/', '_').str.replace('.', '')

        # Parse dates
        if 'trans_date' in df.columns:
            df['trans_date'] = pd.to_datetime(df['trans_date'], errors='coerce')

        df.to_sql('transactions', conn, if_exists='replace', index=False)
        print(f"   ✓ Imported {len(df):,} transactions")
        tables_created += 1
        total_records += len(df)
    else:
        print(f"\n7. ⚠️  Transactions CSV not found (pattern: {CSV_PATTERNS['transactions']})")

    # Import Event Summary
    csv_file = find_latest_csv(CSV_PATTERNS['events'])
    if csv_file:
        print(f"\n8. Importing Event Summary from: {csv_file}")
        df = pd.read_csv(csv_file, encoding='utf-8-sig', low_memory=False)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('/', '_')

        # Parse dates
        if 'date' in df.columns:
            df['event_date'] = pd.to_datetime(df['date'], errors='coerce')

        df.to_sql('event_summary', conn, if_exists='replace', index=False)
        print(f"   ✓ Imported {len(df):,} event summary records")
        tables_created += 1
        total_records += len(df)
    else:
        print(f"\n8. ⚠️  Event Summary CSV not found (pattern: {CSV_PATTERNS['events']})")

    # Import Event List
    csv_file = find_latest_csv(CSV_PATTERNS['event_list'])
    if csv_file:
        print(f"\n9. Importing Event List from: {csv_file}")
        df = pd.read_csv(csv_file, encoding='utf-8-sig', low_memory=False)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('/', '_')

        df.to_sql('event_list', conn, if_exists='replace', index=False)
        print(f"   ✓ Imported {len(df):,} event types")
        tables_created += 1
        total_records += len(df)
    else:
        print(f"\n9. ⚠️  Event List CSV not found (pattern: {CSV_PATTERNS['event_list']})")

    # Import Instructors
    csv_file = find_latest_csv(CSV_PATTERNS['instructors'])
    if csv_file:
        print(f"\n10. Importing Instructors from: {csv_file}")
        df = pd.read_csv(csv_file, encoding='utf-8-sig', low_memory=False)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('/', '_')

        df.to_sql('instructors', conn, if_exists='replace', index=False)
        print(f"   ✓ Imported {len(df):,} instructors")
        tables_created += 1
        total_records += len(df)
    else:
        print(f"\n10. ⚠️  Instructors CSV not found (pattern: {CSV_PATTERNS['instructors']})")

    # Import Sales Summary
    csv_file = find_latest_csv(CSV_PATTERNS['sales_summary'])
    if csv_file:
        print(f"\n11. Importing Sales Summary from: {csv_file}")
        df = pd.read_csv(csv_file, encoding='utf-8-sig', low_memory=False)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('/', '_')

        df.to_sql('sales_summary', conn, if_exists='replace', index=False)
        print(f"   ✓ Imported {len(df):,} sales records")
        tables_created += 1
        total_records += len(df)
    else:
        print(f"\n11. ⚠️  Sales Summary CSV not found (pattern: {CSV_PATTERNS['sales_summary']})")

    # Create indexes for common queries
    print("\n" + "=" * 80)
    print("CREATING INDEXES")
    print("=" * 80)

    cursor = conn.cursor()

    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_reservations_player ON reservations(player__)",
        "CREATE INDEX IF NOT EXISTS idx_reservations_start ON reservations(start_datetime)",
        "CREATE INDEX IF NOT EXISTS idx_members_id ON members(member__)",
        "CREATE INDEX IF NOT EXISTS idx_members_status ON members(membership_status)",
        "CREATE INDEX IF NOT EXISTS idx_checkins_player ON checkins(player__)",
        "CREATE INDEX IF NOT EXISTS idx_checkins_datetime ON checkins(checkin_datetime)",
        "CREATE INDEX IF NOT EXISTS idx_checkins_registration ON checkins(registration_type)",
        "CREATE INDEX IF NOT EXISTS idx_court_util_date ON court_utilization(date)",
        "CREATE INDEX IF NOT EXISTS idx_cancellations_start ON cancellations(start_datetime)",
    ]

    for idx_sql in indexes:
        cursor.execute(idx_sql)
        print(f"   ✓ {idx_sql.split('idx_')[1].split(' ON')[0]}")

    conn.commit()

    # Get database size
    db_size = os.path.getsize(DB_PATH) / (1024 * 1024)  # MB

    # Print summary
    print("\n" + "=" * 80)
    print("DATABASE CREATION COMPLETE")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"   • Tables created: {tables_created}")
    print(f"   • Total records: {total_records:,}")
    print(f"   • Database file: {DB_PATH}")
    print(f"   • Database size: {db_size:.1f} MB")

    # Show table info
    print(f"\n📋 Tables:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"   • {table[0]}: {count:,} records")

    conn.close()

    print(f"\n✅ Database ready! Use SQLite client or Python to query.")
    print(f"\nExample query:")
    print(f"   sqlite3 {DB_PATH}")
    print(f"   SELECT COUNT(*) FROM reservations;")

    return DB_PATH


if __name__ == '__main__':
    create_database()
