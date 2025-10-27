# SQLite Database for CourtReserve Analysis

**Purpose:** Create a local SQLite database from CourtReserve CSV exports for easier querying and analysis.

**Benefits:**
- ✅ SQL queries instead of pandas filtering
- ✅ Complex joins across tables
- ✅ Fast aggregations and analytics
- ✅ Persistent data (loads once, query many times)
- ✅ Standard database tools (DB Browser, DBeaver, etc.)
- ✅ No server setup needed (single file database)

---

## Quick Start

### 1. Create Database (One-Time Setup)

```bash
# Make sure you have CSV files in _to_process/ directory
ls _to_process/*.csv

# Run the database creation script
python3 scripts/create_database.py
```

**Output:** `courtreserve.db` (50-100MB SQLite database file)

**Time:** ~10-15 seconds to import all CSV files

---

### 2. Query the Database

#### Option A: Python Script (Recommended)

```bash
# Run the query utility to see summary stats
python3 scripts/query_database.py
```

**Output:**
- Table record counts
- Date ranges for each dataset
- Member status breakdown
- Pay-per-use segment summary
- Shadow market utilization stats
- Top activity types
- Custom query examples

#### Option B: Python Code

```python
from scripts.query_database import run_query

# Simple query
df = run_query("SELECT * FROM members WHERE membership_status = 'Active'")
print(df.head())

# Complex query with joins
sql = """
    SELECT
        m.member__,
        m.first_name || ' ' || m.last_name as name,
        m.membership_type,
        COUNT(r.confirmation_) as total_reservations
    FROM members m
    LEFT JOIN reservations r ON m.member__ = r.player__
    WHERE m.membership_status = 'Active'
    GROUP BY m.member__
    ORDER BY total_reservations DESC
    LIMIT 10
"""
df = run_query(sql)
print(df)
```

#### Option C: SQLite CLI

```bash
# Open database in SQLite command-line tool
sqlite3 courtreserve.db

# List all tables
.tables

# Show table schema
.schema members

# Run queries
SELECT COUNT(*) FROM reservations;

SELECT membership_type, COUNT(*) as count
FROM members
WHERE membership_status = 'Active'
GROUP BY membership_type;

# Export to CSV
.mode csv
.output query_results.csv
SELECT * FROM members WHERE membership_status = 'Active';
.output stdout

# Quit
.quit
```

#### Option D: GUI Tools

**DB Browser for SQLite** (Free, cross-platform)
- Download: https://sqlitebrowser.org/
- Open: `courtreserve.db`
- Browse data, run queries, export results

**DBeaver** (Free, universal database tool)
- Download: https://dbeaver.io/
- Connect to SQLite database
- Visual query builder, ER diagrams

---

## Database Schema

### Tables Created

| Table | Records | Source CSV | Purpose |
|-------|---------|------------|---------|
| `reservations` | 4,609 | ReservationReport_*.csv | Booking history |
| `members` | 4,477 | MembersReport_*.csv | Member roster |
| `checkins` | 15,513 | CheckinReports*.csv | Check-in activity |
| `court_utilization` | ~6,000 | CourtUtilization-by-date.csv | Hourly utilization |
| `cancellations` | 3,894 | Cancellation_Report_*.csv | Cancelled bookings |
| `event_registrants` | 13,165 | EventRegistrantsReports*.csv | Event registrations |
| `transactions` | 366 | Transactions*.csv | Financial transactions |
| `event_summary` | 1,326 | Event_Summary*.csv | Event metrics |
| `event_list` | 76 | Event_List.csv | Event catalog |
| `instructors` | 14 | InstructorReport_*.csv | Instructor roster |
| `sales_summary` | 75 | SalesReport*.csv | Sales breakdown |

---

### Key Fields by Table

#### `reservations`
- `confirmation_` (unique ID)
- `reservation_type`
- `start_datetime`, `end_datetime` (parsed dates)
- `is_event_`
- `event_name`
- `courts`
- `player_name`, `player_email`, `player__`
- `members` (comma-separated list)
- `payment_status`
- `fee_amount`
- `created_on`, `created_by`

#### `members`
- `member__` (unique ID)
- `first_name`, `last_name`, `email`
- `membership_type` (Individual, Family, Corporate)
- `membership_status` (Active, Suspended, Expired)
- `membership_start_date` (parsed date)
- `zip_code` (for geographic analysis)
- `phone`, `date_of_birth`

#### `checkins`
- `player__`, `player_first_name`, `player_last_name`
- `checkin_datetime` (parsed date)
- `registration_type` (Drop-In, Reservation, etc.)
- `event_name`
- `membership_name` (e.g., "Individual Membership", "Non-Member/Visitor")
- `price` (original string), `price_amount` (parsed numeric)
- `pickleball_rating`

#### `court_utilization`
- `time_slot` (e.g., "9:00 AM - 10:00 AM")
- `date` (parsed date)
- `utilization_pct` (numeric percentage)

---

### Indexes Created

For fast queries, indexes are automatically created on:
- `reservations(player__)` - Player lookups
- `reservations(start_datetime)` - Date range filters
- `members(member__)` - Member lookups
- `members(membership_status)` - Status filters
- `checkins(player__)` - Player activity
- `checkins(checkin_datetime)` - Date filters
- `checkins(registration_type)` - Registration type filters
- `court_utilization(date)` - Date lookups
- `cancellations(player__)` - Cancellation analysis

---

## Common Queries

### Member Analysis

```sql
-- Active members by type
SELECT membership_type, COUNT(*) as count
FROM members
WHERE membership_status = 'Active'
GROUP BY membership_type
ORDER BY count DESC;

-- Member growth by month
SELECT
    strftime('%Y-%m', membership_start_date) as month,
    COUNT(*) as new_members
FROM members
WHERE membership_start_date IS NOT NULL
GROUP BY month
ORDER BY month DESC
LIMIT 12;

-- Top 10 most active members (by reservations)
SELECT
    m.member__,
    m.first_name || ' ' || m.last_name as name,
    m.membership_type,
    COUNT(r.confirmation_) as reservations
FROM members m
LEFT JOIN reservations r ON m.member__ = r.player__
GROUP BY m.member__
ORDER BY reservations DESC
LIMIT 10;
```

### Pay-Per-Use Segment

```sql
-- Pay-per-use summary
SELECT
    COUNT(DISTINCT player__) as unique_players,
    COUNT(*) as total_checkins,
    AVG(price_amount) as avg_price,
    SUM(price_amount) as total_revenue
FROM checkins
WHERE membership_name LIKE '%Non-Member%'
   OR membership_name LIKE '%Visitor%'
   OR registration_type = 'Drop-In';

-- Top spenders (conversion targets)
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
ORDER BY total_spent DESC;
```

### Shadow Market Analysis

```sql
-- Weekday daytime utilization (9 AM-4 PM)
SELECT
    AVG(utilization_pct) as avg_utilization,
    MIN(utilization_pct) as min_utilization,
    MAX(utilization_pct) as max_utilization,
    100 - AVG(utilization_pct) as empty_capacity_pct
FROM court_utilization
WHERE CAST(strftime('%w', date) AS INTEGER) BETWEEN 1 AND 5  -- Mon-Fri
  AND time_slot BETWEEN '9:00 AM - 10:00 AM' AND '3:00 PM - 4:00 PM'
  AND utilization_pct IS NOT NULL;

-- Lowest utilization time slots
SELECT
    time_slot,
    CASE CAST(strftime('%w', date) AS INTEGER)
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END as day_of_week,
    AVG(utilization_pct) as avg_utilization
FROM court_utilization
WHERE utilization_pct IS NOT NULL
GROUP BY time_slot, CAST(strftime('%w', date) AS INTEGER)
ORDER BY avg_utilization ASC
LIMIT 10;
```

### Activity Analysis

```sql
-- Top activities by check-ins
SELECT
    event_name,
    COUNT(*) as checkins,
    COUNT(DISTINCT player__) as unique_players,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as pct
FROM checkins
WHERE event_name IS NOT NULL AND event_name != ''
GROUP BY event_name
ORDER BY checkins DESC
LIMIT 10;

-- Member vs. Non-Member activity
SELECT
    CASE
        WHEN membership_name LIKE '%Non-Member%' THEN 'Non-Member'
        WHEN membership_name LIKE '%Visitor%' THEN 'Visitor'
        ELSE 'Member'
    END as player_type,
    COUNT(*) as checkins,
    COUNT(DISTINCT player__) as unique_players
FROM checkins
GROUP BY player_type
ORDER BY checkins DESC;
```

### Time-Based Analysis

```sql
-- Reservations by day of week
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
    COUNT(*) as reservations,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as pct
FROM reservations
WHERE start_datetime IS NOT NULL
GROUP BY CAST(strftime('%w', start_datetime) AS INTEGER)
ORDER BY CAST(strftime('%w', start_datetime) AS INTEGER);

-- Busiest hours
SELECT
    CAST(strftime('%H', start_datetime) AS INTEGER) as hour,
    COUNT(*) as reservations
FROM reservations
WHERE start_datetime IS NOT NULL
GROUP BY hour
ORDER BY reservations DESC;
```

---

## Updating the Database

### When to Refresh

Refresh the database monthly (or when you download new CSV files):

```bash
# 1. Download latest CSV files from CourtReserve
# 2. Place new CSV files in _to_process/ directory
# 3. Recreate database
python3 scripts/create_database.py

# The script will:
# - Delete old courtreserve.db
# - Import all CSV files from _to_process/
# - Create indexes
# - Show summary statistics

# 4. Move processed CSVs to archive
mv _to_process/*.csv z_processed_csv_files/
```

**Time:** ~10-15 seconds

---

## Advanced Usage

### Export Query Results

```python
from scripts.query_database import run_query

# Run query and save to CSV
df = run_query("""
    SELECT * FROM members
    WHERE membership_status = 'Active'
""")
df.to_csv('active_members.csv', index=False)
print(f"Exported {len(df)} active members")
```

### Multiple Queries

```python
from scripts.query_database import connect_db
import pandas as pd

# Keep connection open for multiple queries
conn = connect_db()

df1 = pd.read_sql_query("SELECT COUNT(*) FROM reservations", conn)
df2 = pd.read_sql_query("SELECT COUNT(*) FROM members", conn)
df3 = pd.read_sql_query("SELECT COUNT(*) FROM checkins", conn)

conn.close()
```

### Complex Joins

```python
sql = """
    SELECT
        m.member__,
        m.first_name || ' ' || m.last_name as member_name,
        m.membership_type,
        COUNT(DISTINCT r.confirmation_) as reservations,
        COUNT(DISTINCT c.check_in_date_time) as checkins,
        SUM(t.amount) as total_spent
    FROM members m
    LEFT JOIN reservations r ON m.member__ = r.player__
    LEFT JOIN checkins c ON m.member__ = c.player__
    LEFT JOIN transactions t ON m.member__ = t.member__
    WHERE m.membership_status = 'Active'
    GROUP BY m.member__
    HAVING reservations > 10
    ORDER BY reservations DESC
    LIMIT 20
"""

df = run_query(sql)
print(df)
```

---

## Troubleshooting

### Database Not Found

**Error:** `sqlite3.OperationalError: unable to open database file`

**Solution:** Run `python3 scripts/create_database.py` first to create the database.

### Table Missing

**Error:** `sqlite3.OperationalError: no such table: reservations`

**Solution:** CSV file was missing during database creation. Check that all CSV files are in repository root and recreate database.

### Slow Queries

**Issue:** Queries taking >1 second

**Solutions:**
- Check if indexes exist: `.schema reservations` (should show CREATE INDEX statements)
- Add more indexes if needed:
  ```sql
  CREATE INDEX idx_reservations_event ON reservations(event_name);
  ```
- Use EXPLAIN QUERY PLAN to debug:
  ```sql
  EXPLAIN QUERY PLAN
  SELECT * FROM reservations WHERE event_name = 'Open Play';
  ```

### Memory Issues

**Issue:** Python crashes with large result sets

**Solution:** Use chunking:
```python
# Instead of loading entire table
# df = pd.read_sql_query("SELECT * FROM checkins", conn)

# Load in chunks
chunk_size = 10000
for chunk in pd.read_sql_query("SELECT * FROM checkins", conn, chunksize=chunk_size):
    process(chunk)
```

---

## Benefits Over CSV Analysis

| Feature | CSV (pandas) | SQLite Database |
|---------|-------------|-----------------|
| Load time | ~5-10 sec per file | ~1 sec (already loaded) |
| Memory usage | Full dataset in RAM | Only query results in RAM |
| Complex joins | Multiple merge operations | Single JOIN query |
| Aggregations | GroupBy operations | Fast indexed aggregations |
| Filtering | Boolean indexing | WHERE clauses with indexes |
| Reusability | Re-read CSV each time | Query many times, load once |
| Tools | Python pandas only | Python, CLI, GUI tools |
| Sharing | Send CSV files | Send single .db file |

---

## Database File Info

**Location:** `courtreserve.db` (repository root)
**Format:** SQLite 3
**Size:** 50-100MB (depends on data volume)
**Compatibility:** SQLite 3.x (universal)

**Tracked in Git:** ❌ No (in .gitignore)
**Reason:** Generated from CSV files, can be recreated anytime

**To share database:**
1. Upload to Google Drive / Dropbox
2. Share link with team
3. Recipient runs queries without needing CSV files

---

## Next Steps

1. **Create database:**
   ```bash
   python3 scripts/create_database.py
   ```

2. **Run summary queries:**
   ```bash
   python3 scripts/query_database.py
   ```

3. **Try custom queries:** Open `scripts/query_database.py` and add your own queries

4. **Install GUI tool:** Download DB Browser for SQLite for visual exploration

5. **Integrate into analysis:** Update `scripts/analyze_*.py` to use database instead of CSV

---

**Documentation Version:** 1.0
**Last Updated:** October 27, 2025
**Maintained By:** PCC Customer Intelligence Team
