#!/usr/bin/env python3
"""
Database Loader Utility for CourtReserve Analysis
Provides standardized access to SQLite database for all analysis scripts.

Purpose: Replace direct CSV reads with database queries
Benefits: Faster, more reliable, easier to maintain
Author: Claude Code (Anthropic)
Date: October 27, 2025
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

# Default database path (relative to repository root)
DEFAULT_DB_PATH = 'courtreserve.db'


class CourtReserveDB:
    """
    Wrapper class for CourtReserve SQLite database.
    Provides clean API for loading data into pandas DataFrames.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Database not found: {self.db_path}\n"
                f"Run 'python3 scripts/create_database.py' first to create it."
            )
        self.conn = None

    def __enter__(self):
        """Context manager entry - open connection."""
        self.conn = sqlite3.connect(self.db_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connection."""
        if self.conn:
            self.conn.close()

    def _execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame.

        Args:
            query: SQL query string
            params: Optional query parameters for parameterized queries

        Returns:
            DataFrame with query results
        """
        if not self.conn:
            self.conn = sqlite3.connect(self.db_path)

        if params:
            return pd.read_sql_query(query, self.conn, params=params)
        else:
            return pd.read_sql_query(query, self.conn)

    def get_reservations(self,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Load reservations data with optional date filtering.

        Args:
            start_date: Filter reservations >= this date (YYYY-MM-DD)
            end_date: Filter reservations <= this date (YYYY-MM-DD)

        Returns:
            DataFrame with reservation records
        """
        query = "SELECT * FROM reservations"

        filters = []
        params = []

        if start_date:
            filters.append("start_datetime >= ?")
            params.append(start_date)
        if end_date:
            filters.append("start_datetime <= ?")
            params.append(end_date)

        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " ORDER BY start_datetime"

        df = self._execute_query(query, tuple(params) if params else None)

        # Parse datetime columns
        date_cols = ['start_datetime', 'end_datetime', 'created_on']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        return df

    def get_members(self, status: Optional[str] = None) -> pd.DataFrame:
        """
        Load members data with optional status filtering.

        Args:
            status: Filter by membership_status (e.g., 'Active', 'Suspended', 'Expired')

        Returns:
            DataFrame with member records
        """
        query = "SELECT * FROM members"

        if status:
            query += f" WHERE membership_status = ?"
            df = self._execute_query(query, (status,))
        else:
            df = self._execute_query(query)

        # Parse date columns
        if 'membership_start_date' in df.columns:
            df['membership_start_date'] = pd.to_datetime(df['membership_start_date'], errors='coerce')

        return df

    def get_checkins(self,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Load check-in data with optional date filtering.

        Args:
            start_date: Filter check-ins >= this date (YYYY-MM-DD)
            end_date: Filter check-ins <= this date (YYYY-MM-DD)

        Returns:
            DataFrame with check-in records
        """
        query = "SELECT * FROM checkins"

        filters = []
        params = []

        if start_date:
            filters.append("checkin_datetime >= ?")
            params.append(start_date)
        if end_date:
            filters.append("checkin_datetime <= ?")
            params.append(end_date)

        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " ORDER BY checkin_datetime"

        df = self._execute_query(query, tuple(params) if params else None)

        # Parse datetime column
        if 'checkin_datetime' in df.columns:
            df['checkin_datetime'] = pd.to_datetime(df['checkin_datetime'], errors='coerce')

        return df

    def get_transactions(self,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Load transaction data with optional date filtering.

        Args:
            start_date: Filter transactions >= this date (YYYY-MM-DD)
            end_date: Filter transactions <= this date (YYYY-MM-DD)

        Returns:
            DataFrame with transaction records
        """
        query = "SELECT * FROM transactions"

        filters = []
        params = []

        if start_date:
            filters.append("trans_datetime >= ?")
            params.append(start_date)
        if end_date:
            filters.append("trans_datetime <= ?")
            params.append(end_date)

        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " ORDER BY trans_datetime"

        df = self._execute_query(query, tuple(params) if params else None)

        # Parse datetime columns
        date_cols = ['trans_datetime', 'paid_datetime']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        return df

    def get_cancellations(self,
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Load cancellation data with optional date filtering.

        Args:
            start_date: Filter cancellations >= this date (YYYY-MM-DD)
            end_date: Filter cancellations <= this date (YYYY-MM-DD)

        Returns:
            DataFrame with cancellation records
        """
        query = "SELECT * FROM cancellations"

        filters = []
        params = []

        if start_date:
            filters.append("start_datetime >= ?")
            params.append(start_date)
        if end_date:
            filters.append("start_datetime <= ?")
            params.append(end_date)

        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " ORDER BY start_datetime"

        df = self._execute_query(query, tuple(params) if params else None)

        # Parse datetime columns
        date_cols = ['start_datetime', 'end_datetime', 'cancelled_on']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        return df

    def get_court_utilization(self) -> pd.DataFrame:
        """
        Load court utilization data.

        Returns:
            DataFrame with utilization records
        """
        df = self._execute_query("SELECT * FROM court_utilization ORDER BY date, time_slot")

        # Parse date column
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

        return df

    def get_event_registrants(self,
                             start_date: Optional[str] = None,
                             end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Load event registrant data with optional date filtering.

        Args:
            start_date: Filter events >= this date (YYYY-MM-DD)
            end_date: Filter events <= this date (YYYY-MM-DD)

        Returns:
            DataFrame with event registrant records
        """
        query = "SELECT * FROM event_registrants"

        filters = []
        params = []

        if start_date:
            filters.append("event_date >= ?")
            params.append(start_date)
        if end_date:
            filters.append("event_date <= ?")
            params.append(end_date)

        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " ORDER BY event_date"

        df = self._execute_query(query, tuple(params) if params else None)

        # Parse date column
        if 'event_date' in df.columns:
            df['event_date'] = pd.to_datetime(df['event_date'], errors='coerce')

        return df

    def get_event_summary(self) -> pd.DataFrame:
        """
        Load event summary data.

        Returns:
            DataFrame with event summary records
        """
        return self._execute_query("SELECT * FROM event_summary")

    def get_instructors(self) -> pd.DataFrame:
        """
        Load instructor data.

        Returns:
            DataFrame with instructor records
        """
        return self._execute_query("SELECT * FROM instructors")

    def get_sales_summary(self) -> pd.DataFrame:
        """
        Load sales summary data.

        Returns:
            DataFrame with sales summary records
        """
        return self._execute_query("SELECT * FROM sales_summary")

    def get_table_info(self) -> Dict[str, int]:
        """
        Get record counts for all tables.

        Returns:
            Dictionary mapping table names to record counts
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        counts = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]

        return counts


# Convenience functions for quick access
def get_reservations(**kwargs) -> pd.DataFrame:
    """Load reservations. See CourtReserveDB.get_reservations() for args."""
    with CourtReserveDB() as db:
        return db.get_reservations(**kwargs)


def get_members(**kwargs) -> pd.DataFrame:
    """Load members. See CourtReserveDB.get_members() for args."""
    with CourtReserveDB() as db:
        return db.get_members(**kwargs)


def get_checkins(**kwargs) -> pd.DataFrame:
    """Load check-ins. See CourtReserveDB.get_checkins() for args."""
    with CourtReserveDB() as db:
        return db.get_checkins(**kwargs)


def get_transactions(**kwargs) -> pd.DataFrame:
    """Load transactions. See CourtReserveDB.get_transactions() for args."""
    with CourtReserveDB() as db:
        return db.get_transactions(**kwargs)


def get_cancellations(**kwargs) -> pd.DataFrame:
    """Load cancellations. See CourtReserveDB.get_cancellations() for args."""
    with CourtReserveDB() as db:
        return db.get_cancellations(**kwargs)


def get_court_utilization() -> pd.DataFrame:
    """Load court utilization data."""
    with CourtReserveDB() as db:
        return db.get_court_utilization()


def get_event_registrants(**kwargs) -> pd.DataFrame:
    """Load event registrants. See CourtReserveDB.get_event_registrants() for args."""
    with CourtReserveDB() as db:
        return db.get_event_registrants(**kwargs)


if __name__ == '__main__':
    """Test database connection and show summary."""
    print("=" * 80)
    print("COURTRESERVE DATABASE SUMMARY")
    print("=" * 80)

    with CourtReserveDB() as db:
        info = db.get_table_info()

        print("\nTable Record Counts:")
        print("-" * 80)
        for table, count in info.items():
            print(f"  {table:25s} {count:>10,} records")

        print("\n" + "=" * 80)
        print(f"Total records across all tables: {sum(info.values()):,}")
        print("=" * 80)

        # Show date ranges for key tables
        print("\nDate Ranges:")
        print("-" * 80)

        reservations = db.get_reservations()
        if not reservations.empty and 'start_datetime' in reservations.columns:
            print(f"  Reservations: {reservations['start_datetime'].min()} to {reservations['start_datetime'].max()}")

        checkins = db.get_checkins()
        if not checkins.empty and 'checkin_datetime' in checkins.columns:
            print(f"  Check-ins:    {checkins['checkin_datetime'].min()} to {checkins['checkin_datetime'].max()}")

        transactions = db.get_transactions()
        if not transactions.empty and 'trans_datetime' in transactions.columns:
            print(f"  Transactions: {transactions['trans_datetime'].min()} to {transactions['trans_datetime'].max()}")

        print("=" * 80)
