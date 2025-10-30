# CourtReserve Data Validation Checklist

**Purpose:** Monthly data export and validation workflow
**Frequency:** Run monthly or when new data is imported
**Owner:** Data Analysis Team

---

## Quick Reference

### 📊 Core Reports (Must Download Monthly)

| Priority | Report Type | CourtReserve Location | Purpose |
|----------|-------------|----------------------|---------|
| **🔴 CRITICAL** | Transactions | Reports → Transactions → Transactions List | Financial source of truth |
| **🔴 CRITICAL** | Reservations | Reports → Reservations → Reservation Report | Booking behavior |
| **🔴 CRITICAL** | Check-Ins | Reports → Check-ins → Check-in Reports | Attendance tracking |
| **🟡 HIGH** | Members | Reports → Members → Members Report | Customer roster |
| **🟡 HIGH** | Court Utilization | Reports → Court Utilization → By Date | Capacity analysis |
| **🟢 MEDIUM** | Event Registrants | Reports → Events → Registrant Detail | Program participation |
| **🟢 MEDIUM** | Cancellations | Reports → Reservations → Cancellation Report | Churn signals |

---

## Monthly Export Workflow

### Step 1: Prepare for Export (5 minutes)

**Before You Begin:**
- [ ] Determine date range (typically: first day of previous month to yesterday)
- [ ] Create timestamped directory: `_to_process/YYYY-MM-DD_export/`
- [ ] Clear any old files from `_to_process/` main directory

**Date Range Reference:**
- **Full Historical:** January 1, 2025 to [Current Date]
- **Monthly Update:** First of last month to yesterday
- **Example:** For November 1 export, use October 1 - October 31

---

### Step 2: Download Core Reports (20 minutes)

#### 🔴 CRITICAL #1: Transactions Report

**Location:** CourtReserve.com → Reports → Transactions → Transactions List

**Settings:**
- **Date Range:** Split by quarters for large datasets:
  - Q1: January 1 - March 31
  - Q2: April 1 - June 30
  - Q3: July 1 - September 30
  - Q4: October 1 - December 31
- **Transaction Types:** ALL (include Payments, Fees, Credits, Refunds)
- **Format:** CSV

**Expected Output:**
- `Transactions_2025-01-01-to-2025-03-31.csv`
- `Transactions_2025-04-01-to-2025-06-30.csv`
- `Transactions_2025-07-01-to-2025-09-30.csv`
- `Transactions_2025-10-01-to-2025-[DATE].csv`

**Validation Check:**
```
Total file size: ~2-3 MB per quarter
Record count: ~7,000-10,000 per quarter
Critical field: "Total" column should have dollar amounts
```

**Why Critical:** This is the ONLY reliable source of actual revenue data.

---

#### 🔴 CRITICAL #2: Reservation Report

**Location:** CourtReserve.com → Reports → Reservations → Reservation Report

**Settings:**
- **Date Range:** January 1, 2025 to [Current Date]
- **Reservation Types:** ALL
- **Include:** Paid, Unpaid, Cancelled reservations
- **Format:** CSV

**Expected Output:**
- `ReservationReport_[YYYY-MM-DD]_[HH-MM-AM/PM].csv`
- Example: `ReservationReport_2025-11-01_09-30-AM.csv`

**Validation Check:**
```
File size: ~1-2 MB
Record count: ~5,000-6,000 for 10 months
Critical fields: Start Date/Time, Player #, Confirmation #
```

**Why Critical:** Primary source for booking behavior and customer activity patterns.

---

#### 🔴 CRITICAL #3: Check-In Reports

**Location:** CourtReserve.com → Reports → Check-ins → Check-in Reports

**Settings:**
- **Date Range:** January 1, 2025 to [Current Date]
- **Include:** All check-in types (Member, Non-Member, Drop-In, Reservation, Full)
- **Format:** CSV

**Expected Output:**
- `CheckinReports_[YYYY-MM-DD]_[HH-MM-AM/PM].csv`
- Example: `CheckinReports_2025-11-01_09-35-AM.csv`

**Validation Check:**
```
File size: ~6-8 MB
Record count: ~17,000-20,000 for 10 months
Critical fields: Player #, Check-in Date/Time, Registration Type
```

**Why Critical:** Attendance tracking and activity type analysis.

⚠️ **IMPORTANT:** Do NOT use "Price" column for revenue calculations. Use transactions table instead.

---

#### 🟡 HIGH PRIORITY: Members Report

**Location:** CourtReserve.com → Reports → Members → Members Report

**Settings:**
- **Report Date:** [Current Date] (snapshot)
- **Include:** All member statuses (Active, Suspended, Expired, No Membership)
- **Fields:** Ensure all fields selected (especially Zip Code)
- **Format:** CSV

**Expected Output:**
- `MembersReport_[YYYY-MM-DD]_[HH-MM-AM/PM].csv`
- Example: `MembersReport_2025-11-01_09-40-AM.csv`

**Validation Check:**
```
File size: ~1-2 MB
Record count: ~4,500-5,000 members
Critical fields: Member #, Membership Status, Email
```

**Why Important:** Customer roster for identifying members vs non-members.

---

#### 🟡 HIGH PRIORITY: Court Utilization by Date

**Location:** CourtReserve.com → Reports → Court Utilization → By Date

**Settings:**
- **Date Range:** January 1, 2025 to [Current Date]
- **Reservation Types:** ALL
- **Event Categories:** ALL
- **Court Types:** ALL
- **Computed By:** Utilized Courts
- **View:** By Date
- **Format:** CSV

**Expected Output:**
- `Court_Util_[YYYY-MM-DD]-[YYYY-MM-DD]-Group-by_Date-Calc-by-Court-util.csv`
- Example: `Court_Util_2025-01-01-2025-11-01-Group-by_Date-Calc-by-Court-util.csv`

**Validation Check:**
```
File size: ~40-50 KB
Format: Time slots (rows) × Date columns
Values: Percentage strings (e.g., "45.2 %")
```

**Why Important:** Shadow market analysis and capacity planning.

---

#### 🟢 MEDIUM PRIORITY: Event Registrants

**Location:** CourtReserve.com → Reports → Events → Registrant Detail

**Settings:**
- **Date Range:** January 1, 2025 to [Current Date]
- **Include:** All event types
- **Format:** CSV

**Expected Output:**
- `EventRegistrantsReports_[YYYY-MM-DD]_[HH-MM-AM/PM].csv`
- Example: `EventRegistrantsReports_2025-11-01_09-45-AM.csv`

**Validation Check:**
```
File size: ~5-6 MB
Record count: ~13,000-15,000 registrations
```

---

#### 🟢 MEDIUM PRIORITY: Cancellation Report

**Location:** CourtReserve.com → Reports → Reservations → Cancellation Report

⚠️ **Important:** CourtReserve names this `ReservationReport_*.xlsx` when downloaded. You must rename it to `Cancellation_Report_*.csv`.

**Settings:**
- **Date Range:** January 1, 2025 to [Current Date]
- **Include:** All cancellation reasons
- **Format:** CSV (after renaming)

**Expected Output:**
- `Cancellation_Report_[YYYY-MM-DD]_[HH-MM-AM/PM].csv`
- Example: `Cancellation_Report_2025-11-01_09-50-AM.csv`

**Validation Check:**
```
File size: ~700 KB
Record count: ~4,000-5,000 cancellations
```

⚠️ **Data Quality Note:** User reported potential integrity concerns. Use for trends, not precise calculations.

---

### Step 3: File Organization (5 minutes)

**After Download:**

1. **Verify File Names:**
   ```bash
   ls _to_process/*.csv | wc -l  # Should show 7-10 files
   ```

2. **Check File Sizes:**
   ```bash
   ls -lh _to_process/*.csv
   # Transactions: 2-3 MB per file
   # Check-ins: 6-8 MB
   # Reservations: 1-2 MB
   # Members: 1-2 MB
   # Others: <1 MB each
   ```

3. **Verify Date Ranges in Filenames:**
   - Transactions: Should have clear date ranges
   - Others: Should have download timestamp

4. **Rename Cancellation Report if needed:**
   ```bash
   # If downloaded as ReservationReport_*.xlsx:
   mv "ReservationReport_2025-11-01_09-50-AM.xlsx" "Cancellation_Report_2025-11-01_09-50-AM.csv"
   ```

---

### Step 4: Database Import (2 minutes)

**Run Database Creation Script:**

```bash
python3 scripts/create_database.py
```

**Expected Output:**
```
Creating new database: courtreserve.db
Importing CSV files...
  ✓ Reservations: 4,609 records
  ✓ Members: 4,484 records
  ✓ Check-ins: 17,250 records
  ✓ Transactions: 29,752 records
  ✓ Court Utilization: 5,980 records
  ✓ Cancellations: 3,894 records
  ✓ Event Registrants: 13,165 records
Database created successfully: 50.2 MB
```

**If Import Fails:**
- Check CSV file encoding (should be UTF-8)
- Verify column headers match expected format
- Check for special characters in filenames
- Review error message for specific table/column issues

---

### Step 5: Run Validation Script (3 minutes)

**Execute Automated Validation:**

```bash
python3 scripts/validate_data_import.py
```

**Expected Output:**
```
================================================================================
DATA VALIDATION REPORT
================================================================================

✓ PASS: Transaction totals within 5% of previous month
✓ PASS: Member count matches expected range
✓ PASS: Check-in counts reasonable for date range
⚠️  WARNING: Non-member check-ins only 60 records (expected low)
✓ PASS: Court utilization data complete
✓ PASS: No major date gaps detected

Validation complete: 6 passed, 0 failed, 1 warning
```

**If Validation Fails:**
- Review specific error messages
- Check for incomplete downloads
- Verify date ranges are continuous
- Re-download affected reports

---

## Validation Queries

### Financial Validation

#### 1. Total Revenue Check

```sql
-- Compare to previous month:
SELECT
    strftime('%Y-%m', trans_date) as month,
    COUNT(*) as num_payments,
    SUM(CAST(REPLACE(REPLACE(REPLACE(REPLACE(total, '$', ''), ',', ''), '(', ''), ')', '') AS REAL)) as revenue
FROM transactions
WHERE trans_type LIKE '%Payment%'
  AND trans_date >= '2025-01-01'
GROUP BY month
ORDER BY month;
```

**Expected Pattern:** Gradual growth or stability month-over-month.
**Flag if:** Any month deviates >20% from average without known cause.

#### 2. Member vs Non-Member Revenue

```sql
SELECT
    CASE WHEN m.membership_status = 'Currently Active' THEN 'Member'
         ELSE 'Non-Member'
    END as customer_type,
    COUNT(*) as num_payments,
    SUM(CAST(REPLACE(REPLACE(REPLACE(REPLACE(t.total, '$', ''), ',', ''), '(', ''), ')', '') AS REAL)) as revenue
FROM transactions t
LEFT JOIN members m ON t."member_#" = m."member_#"
WHERE t.trans_type LIKE '%Payment%'
GROUP BY customer_type;
```

**Expected Ratio:** Non-members typically 60-70% of revenue.
**Flag if:** Ratio shifts dramatically without explanation.

---

### Attendance Validation

#### 3. Check-In Counts by Month

```sql
SELECT
    strftime('%Y-%m', checkin_datetime) as month,
    COUNT(*) as total_checkins,
    COUNT(DISTINCT player__#) as unique_players,
    AVG(COUNT(*)) OVER () as avg_checkins
FROM checkins
WHERE check_in_status = 'Checked-In'
  AND checkin_datetime >= '2025-01-01'
GROUP BY month
ORDER BY month;
```

**Expected Pattern:** Stable or growing attendance.
**Flag if:** Any month <80% of average without known cause (weather, closures, etc.).

---

### Membership Validation

#### 4. Active Member Count

```sql
SELECT
    membership_status,
    COUNT(*) as member_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as pct
FROM members
GROUP BY membership_status
ORDER BY member_count DESC;
```

**Expected:**
- Currently Active: 4,300-4,500 (97%)
- No Membership: ~100 (2%)
- Suspended/Others: <1%

**Flag if:** Active member count drops >10% from previous month.

---

### Data Completeness Checks

#### 5. Date Range Coverage

```sql
SELECT
    'Transactions' as table_name,
    MIN(trans_date) as earliest,
    MAX(trans_date) as latest,
    COUNT(*) as record_count
FROM transactions
WHERE trans_type LIKE '%Payment%'

UNION ALL

SELECT
    'Check-Ins',
    MIN(checkin_datetime),
    MAX(checkin_datetime),
    COUNT(*)
FROM checkins
WHERE check_in_status = 'Checked-In'

UNION ALL

SELECT
    'Reservations',
    MIN(start_datetime),
    MAX(start_datetime),
    COUNT(*)
FROM reservations;
```

**Expected:** All date ranges should be continuous from Jan 1, 2025 to current date.
**Flag if:** Any gaps >7 days or end date is not recent.

---

### Cross-Table Validation

#### 6. Customer ID Consistency

```sql
-- Check for customers in transactions but not in members:
SELECT
    COUNT(DISTINCT t."member_#") as trans_customers,
    COUNT(DISTINCT m."member_#") as member_records,
    COUNT(DISTINCT t."member_#") - COUNT(DISTINCT m."member_#") as missing_from_members
FROM transactions t
LEFT JOIN members m ON t."member_#" = m."member_#"
WHERE t.trans_type LIKE '%Payment%';
```

**Expected:** Missing count should be small (<5% of transaction customers).
**Flag if:** >10% of transaction customers not in members table.

---

## Monthly Validation Checklist

### Pre-Import Checklist

- [ ] All CSV files downloaded (7 core reports minimum)
- [ ] Files in `_to_process/` directory
- [ ] File sizes within expected ranges
- [ ] Cancellation report renamed if needed
- [ ] Date ranges are continuous (no gaps)

### Post-Import Checklist

- [ ] Database created successfully (courtreserve.db exists)
- [ ] All tables imported (11 tables minimum)
- [ ] Record counts reasonable (see expected ranges above)
- [ ] No major import errors in console output
- [ ] Database file size 50-100 MB

### Validation Script Checklist

- [ ] Total revenue within 5% of expected
- [ ] Member count within expected range (4,300-4,500)
- [ ] Check-in count reasonable for date range
- [ ] No date gaps >7 days
- [ ] Cross-table customer IDs consistent
- [ ] All critical fields populated (not NULL)

### Analysis Readiness Checklist

- [ ] Transactions table has payment records
- [ ] Members table has active members
- [ ] Check-ins table has recent records
- [ ] Court utilization has continuous dates
- [ ] Previous month's data included
- [ ] Ready to run analysis scripts

---

## Troubleshooting

### Issue: Import Fails with Encoding Error

**Solution:**
```bash
# Check file encoding:
file -I _to_process/*.csv

# If not UTF-8, convert:
iconv -f ISO-8859-1 -t UTF-8 input.csv > output.csv
```

### Issue: Validation Shows 99% Missing Non-Member Revenue

**Expected Behavior:** This is normal. Check-ins table only captures ~60 non-member records. Verify actual revenue from transactions table.

### Issue: Transaction Totals Don't Match Previous Month

**Investigation Steps:**
1. Check if date range includes all days
2. Verify transaction type filter (should include Payments only)
3. Check for currency parsing errors
4. Review for any major refunds/credits
5. Compare against CourtReserve dashboard

### Issue: Member Count Drops Significantly

**Investigation Steps:**
1. Verify membership status filter (should be "Currently Active")
2. Check if members were archived/deleted in CourtReserve
3. Review for bulk status changes
4. Compare against CourtReserve membership dashboard
5. Check export settings (ensure all statuses included)

---

## Advanced: Custom Validation Queries

### Revenue by Category Validation

```sql
SELECT
    category,
    COUNT(*) as num_transactions,
    SUM(CAST(REPLACE(REPLACE(REPLACE(REPLACE(total, '$', ''), ',', ''), '(', ''), ')', '') AS REAL)) as revenue
FROM transactions
WHERE trans_type LIKE '%Payment%'
  AND trans_date >= date('now', '-30 days')
GROUP BY category
ORDER BY revenue DESC
LIMIT 10;
```

Compare to CourtReserve Sales Summary report.

### Top Customers Validation

```sql
SELECT
    player,
    "member_#",
    COUNT(*) as num_payments,
    SUM(CAST(REPLACE(REPLACE(REPLACE(REPLACE(total, '$', ''), ',', ''), '(', ''), ')', '') AS REAL)) as total_spent
FROM transactions
WHERE trans_type LIKE '%Payment%'
  AND trans_date >= '2025-01-01'
GROUP BY "member_#"
ORDER BY total_spent DESC
LIMIT 20;
```

Verify top spenders match CourtReserve customer profiles.

---

## Export Schedule

**Recommended Frequency:**

| Report Type | Frequency | Timing |
|-------------|-----------|--------|
| **Full Export** | Monthly | 1st business day of month |
| **Quick Check** | Weekly | Every Monday |
| **Transactions** | Bi-weekly | Payroll sync |
| **Members** | Weekly | Monitor growth |

**Annual Full Refresh:** January (complete historical re-export)

---

## Contacts & Support

**For Report Access Issues:**
- CourtReserve Support: support@courtreserve.com
- Admin Account: [Facility Manager]

**For Data Questions:**
- Analysis Team Lead: [Contact]
- Data Validation Owner: [Contact]

**For Technical Issues:**
- Database Admin: [Contact]
- Script Maintenance: See `scripts/README.md`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-29 | Initial validation checklist created |

---

**See Also:**
- `DATA_DICTIONARY.md` - Complete schema documentation
- `scripts/validate_data_import.py` - Automated validation script
- `_courtreserve_reports_download_guide.md` - Detailed download instructions
