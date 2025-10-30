# CourtReserve Data Dictionary

**Database:** courtreserve.db (SQLite)
**Last Updated:** October 29, 2025
**Purpose:** Complete schema documentation and usage guidelines

---

## Table of Contents

1. [Overview](#overview)
2. [Financial Truth Sources](#financial-truth-sources)
3. [Table Schemas](#table-schemas)
4. [Data Lineage](#data-lineage)
5. [Usage Guidelines](#usage-guidelines)
6. [Common Pitfalls](#common-pitfalls)

---

## Overview

### Database Structure

| Table | Records | Purpose | Source Report | Financial Data? |
|-------|---------|---------|---------------|-----------------|
| **transactions** | 29,752 | **Financial system of record** | Transactions*.csv | ✓ YES - SOURCE OF TRUTH |
| **reservations** | 4,609 | Booking history | ReservationReport_*.csv | ⚠️ Fee amounts (reference only) |
| **checkins** | 17,250 | Attendance tracking | CheckinReports*.csv | ❌ NO - Attendance only |
| **members** | 4,484 | Member roster | MembersReport_*.csv | ⚠️ Amount due (current balance) |
| **court_utilization** | ~6,000 | Hourly capacity usage | CourtUtilization*.csv | ❌ NO - Utilization % |
| **cancellations** | 3,894 | Cancelled bookings | Cancellation_Report_*.csv | ⚠️ Refund amounts |
| **event_registrants** | 13,165 | Event participation | EventRegistrantsReports*.csv | ⚠️ Event prices (reference) |
| **event_summary** | 1,326 | Event metrics | Event_Summary*.csv | ⚠️ Aggregated stats |
| **event_list** | 76 | Event catalog | Event_List.csv | ❌ NO - Event definitions |
| **instructors** | 14 | Instructor roster | InstructorReport_*.csv | ❌ NO - Staff info |
| **sales_summary** | 75 | Sales breakdown | SalesReport*.csv | ⚠️ Aggregated only |

---

## Financial Truth Sources

### ✅ PRIMARY: Transactions Table

**USE THIS FOR:**
- ✓ Revenue calculations
- ✓ Customer spending analysis
- ✓ Payment verification
- ✓ Financial projections
- ✓ Conversion opportunity sizing

**Why:** This is CourtReserve's billing/payment system. Every actual payment is recorded here.

**Coverage:**
- Total payments: $634,036
- Non-member payments: $423,547 (7,517 transactions)
- Member payments: $210,489 (5,584 transactions)

### ❌ SECONDARY: Check-Ins Table

**DO NOT USE FOR:**
- ❌ Revenue calculations
- ❌ Customer spending totals
- ❌ Financial analysis
- ❌ Conversion opportunity sizing

**USE THIS FOR:**
- ✓ Attendance counts
- ✓ Activity type analysis
- ✓ Behavioral patterns
- ✓ Time-of-day preferences

**Why:** Check-ins is an attendance/access control system. It only captures prices for a small subset of transactions (walk-in drop-ins, event registrations).

**Coverage:**
- Only 60 non-members have price data
- Missing 99% of non-member revenue
- Shows Full event prices multiple times (duplication issue)

### ⚠️ REFERENCE ONLY: Other Tables

**Use with caution:**
- Members: `amount_due` = current balance, not total spending
- Reservations: `fee_amount` = reservation fee, not payment
- Event Registrants: `event_price` = registration price, may not match payment
- Cancellations: `refund_amount` = refunds issued

---

## Table Schemas

### 1. transactions ✅ FINANCIAL TRUTH

**Source:** Transactions_*.csv (multiple date range files)
**Purpose:** Complete financial transaction history
**Record Count:** 29,752 transactions

#### Key Columns

| Column | Type | Description | Usage |
|--------|------|-------------|-------|
| `transaction_id` | REAL | Unique transaction ID | Primary key |
| `trans_date` | TEXT | Transaction date | Filtering, trending |
| `trans_type` | TEXT | Payment, Fee, Refund, Credit | **Filter by 'Payment'** for revenue |
| `member_#` | TEXT | Customer ID | Join to members table |
| `player` | TEXT | Customer name | Display, searching |
| `subtotal` | TEXT | Amount before tax | Parse to REAL |
| `tax` | TEXT | Tax amount | Parse to REAL |
| `total` | TEXT | Total amount | **PRIMARY REVENUE FIELD** |
| `unpaid_amt` | TEXT | Outstanding balance | Accounts receivable |
| `paid_date` | TEXT | Date payment received | Actual payment date |
| `payment_type` | TEXT | Credit Card, Cash, etc | Payment method analysis |
| `category` | TEXT | Revenue category/description | Categorizing revenue types |
| `session` | TEXT | Event/program session | Program tracking |
| `date_time` | TEXT | Event date/time | Event details |
| `user` | TEXT | Who processed transaction | Staff tracking |
| `ispaid` | INTEGER | Payment status flag | 1 = paid, 0 = unpaid |
| `instructors` | TEXT | Instructor(s) if applicable | Program attribution |

#### Important Notes

**Revenue Calculation:**
```sql
-- CORRECT way to calculate revenue:
SELECT SUM(CAST(REPLACE(REPLACE(REPLACE(REPLACE(total, '$', ''), ',', ''), '(', ''), ')', '') AS REAL))
FROM transactions
WHERE trans_type LIKE '%Payment%';
```

**Member vs Non-Member:**
```sql
-- Join to members table to identify membership status:
SELECT t.*,
       CASE WHEN m.membership_status = 'Currently Active' THEN 'Member'
            ELSE 'Non-Member'
       END as customer_type
FROM transactions t
LEFT JOIN members m ON t."member_#" = m."member_#"
WHERE t.trans_type LIKE '%Payment%';
```

**Date Range:** Transaction files are split by date range. Current database includes:
- 2025-01-01 to 2025-04-30
- 2025-05-01 to 2025-08-31
- 2025-09-01 to 2025-10-27

---

### 2. reservations

**Source:** ReservationReport_*.csv
**Purpose:** Booking history and reservation details
**Record Count:** 4,609 reservations

#### Key Columns

| Column | Type | Description | Usage |
|--------|------|-------------|-------|
| `confirmation_#` | TEXT | Unique reservation ID | Primary key |
| `reservation_type` | TEXT | Singles, Doubles, Event, etc | Booking type analysis |
| `start_datetime` | TIMESTAMP | Reservation start time | **Parsed from start_date___time** |
| `end_datetime` | TIMESTAMP | Reservation end time | **Parsed from end_date___time** |
| `is_event?` | INTEGER | 1 = event, 0 = regular booking | Event filtering |
| `event_name` | TEXT | Event name if applicable | Event analysis |
| `courts` | TEXT | Court number(s) | Court utilization |
| `player_name` | TEXT | Primary player | Customer identification |
| `player_#` | TEXT | Player ID | **Join key** |
| `members` | TEXT | All members on reservation | Party size calculation |
| `members_count` | INTEGER | Number of members | **Parsed from members field** |
| `guests` | TEXT | Guest list | Guest analysis |
| `payment_status` | TEXT | Paid, Unpaid, Waived | Payment tracking |
| `fee_amount` | REAL | Reservation fee | ⚠️ Reference only, not payment |
| `created_on` | TIMESTAMP | When booked | Lead time analysis |
| `created_by` | TEXT | Who created booking | Staff vs customer |

#### Important Notes

**⚠️ fee_amount vs Actual Payment:**
- `fee_amount` is the reservation fee charged, NOT the actual payment amount
- For actual revenue, use transactions table
- Use reservations for behavioral analysis (when/what they book)

**Date Parsing:**
- Original: `start_date___time` (TEXT)
- Parsed: `start_datetime` (TIMESTAMP) - use this for queries

**Party Size Calculation:**
```sql
-- Calculate party size from members field:
SELECT confirmation_#,
       LENGTH(members) - LENGTH(REPLACE(members, ',', '')) + 1 as party_size
FROM reservations
WHERE members IS NOT NULL AND members != '';
```

---

### 3. checkins ❌ NOT FOR REVENUE

**Source:** CheckinReports_*.csv
**Purpose:** Attendance tracking and access control
**Record Count:** 17,250 check-ins

#### Key Columns

| Column | Type | Description | Usage |
|--------|------|-------------|-------|
| `player__#` | INTEGER | Player ID | Join key |
| `player_first_name` | TEXT | First name | Display |
| `player_last_name` | TEXT | Last name | Display |
| `check_in_date_time` | TEXT | Check-in timestamp | Attendance date |
| `checkin_datetime` | TIMESTAMP | **Parsed timestamp** | Use for queries |
| `registration_type` | TEXT | **CRITICAL** | Full, Drop-In, Reservation |
| `event_name` | TEXT | Event attended | Activity tracking |
| `check_in_status` | TEXT | Checked-In, No-Show, etc | Attendance verification |
| `price` | TEXT | Price shown (TEXT) | ⚠️ Reference only |
| `price_amount` | REAL | **Parsed price** | ⚠️ **DO NOT USE FOR REVENUE** |
| `is_paid` | TEXT | Payment status | Verification flag |
| `paid_amount` | REAL | Amount paid | ⚠️ Incomplete data |
| `membership_name` | TEXT | Membership type | Member classification |
| `category` | TEXT | Activity category | Activity analysis |

#### ⚠️ CRITICAL: Registration Type Values

| Value | Meaning | Revenue Impact |
|-------|---------|----------------|
| **"Full"** | Multi-session program registration | **DUPLICATED** - Shows full program price on EACH attendance |
| **"Drop-In"** | Walk-in single visit | Usually accurate |
| **"Reservation"** | Pre-booked visit | Usually accurate |
| **Other** | Various | Case by case |

#### Why NOT To Use For Revenue

**Problem #1: Missing Data**
- Only 60 non-members have price data
- Transactions table has 7,517 non-member payments
- **99% of non-member revenue is missing from check-ins**

**Problem #2: Full Event Duplication**
```
Example: 6-week program costing $660
- Customer pays $660 once (transaction table shows 1 payment)
- Customer attends 6 sessions (check-ins shows 6 records)
- Each check-in shows price_amount = $660
- Check-ins total = $3,960 (6 × $660) ❌ WRONG
- Transactions total = $660 ✓ CORRECT
```

#### Correct Usage

**✓ DO use check-ins for:**
```sql
-- Attendance counts:
SELECT COUNT(*) as total_visits,
       COUNT(DISTINCT player__#) as unique_visitors
FROM checkins
WHERE check_in_status = 'Checked-In';

-- Activity preferences:
SELECT event_name, COUNT(*) as visits
FROM checkins
WHERE event_name IS NOT NULL
GROUP BY event_name;

-- Time patterns:
SELECT strftime('%H', checkin_datetime) as hour,
       COUNT(*) as checkins
FROM checkins
GROUP BY hour;
```

**❌ DON'T use check-ins for:**
```sql
-- WRONG - Revenue from check-ins:
SELECT SUM(price_amount) FROM checkins; -- ❌ Inflated by Full events

-- WRONG - Customer spending:
SELECT player__#, SUM(price_amount) FROM checkins GROUP BY player__#; -- ❌ Missing 99% of data

-- RIGHT - Use transactions instead:
SELECT "member_#", SUM(CAST(...total AS REAL)) FROM transactions WHERE trans_type LIKE '%Payment%';
```

---

### 4. members

**Source:** MembersReport_*.csv
**Purpose:** Customer roster and membership details
**Record Count:** 4,484 members

#### Key Columns

| Column | Type | Description | Usage |
|--------|------|-------------|-------|
| `member_#` | TEXT | Unique member ID | **Primary key / join key** |
| `first_name` | TEXT | First name | Display |
| `last_name` | TEXT | Last name | Display |
| `email` | TEXT | Email address | Communication |
| `membership_status` | TEXT | **"Currently Active", "No Membership", "Suspended"** | Filtering |
| `current_membership` | TEXT | Membership type name | Tier analysis |
| `membership_start_date` | TIMESTAMP | When membership started | **Parsed field** |
| `amount_due` | REAL | Current balance owed | ⚠️ NOT total spending |
| `total_paid` | REAL | Historical total paid | ⚠️ May be incomplete |
| `phone_number` | TEXT | Phone | Contact |
| `zip_code` | TEXT | ZIP code | Geographic analysis |
| `date_of_birth` | TIMESTAMP | DOB | Age calculation |
| `first_visit_date` | TEXT | First visit | Tenure |
| `last_visit_date` | TEXT | Most recent visit | Recency |
| `#_﻿of_reservations` | INTEGER | Total reservations made | Activity level |
| `#_﻿of_event_registrations` | INTEGER | Events registered | Engagement |
| `pickleball_rating` | TEXT | Skill rating | Skill level |
| `referral_source` | TEXT | How they found facility | Marketing attribution |

#### Important Notes

**Membership Status Values:**
- `"Currently Active"` - Active paying member
- `"No Membership"` - Non-member/visitor
- `"Suspended"` - Temporarily inactive

**⚠️ Financial Fields:**
- `amount_due` = Current balance, NOT total lifetime spending
- `total_paid` = Historical total, but may not match transactions table
- For accurate spending: Use transactions table joined to members

**Active Member Query:**
```sql
SELECT * FROM members
WHERE membership_status = 'Currently Active';
-- Returns 4,342 active members
```

---

### 5. court_utilization ✓ ACCURATE

**Source:** CourtUtilization*.csv
**Purpose:** Hourly court capacity utilization percentages
**Record Count:** ~6,000 (299 days × 20 hours)

#### Schema

| Column | Type | Description |
|--------|------|-------------|
| `time_slot` | TEXT | Hour range (e.g., "9:00 AM - 10:00 AM") |
| `date` | TIMESTAMP | Date of measurement |
| `utilization_pct` | REAL | Percentage of courts utilized (0-100) |

#### Usage

**✓ Perfect for:**
- Shadow market analysis (empty capacity identification)
- Peak vs off-peak patterns
- Day-of-week utilization
- Hourly demand curves

**Example:**
```sql
-- Find lowest utilization periods:
SELECT
    time_slot,
    CASE CAST(strftime('%w', date) AS INTEGER)
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        -- etc
    END as day,
    AVG(utilization_pct) as avg_util
FROM court_utilization
WHERE CAST(strftime('%w', date) AS INTEGER) BETWEEN 1 AND 5
GROUP BY time_slot, day
ORDER BY avg_util ASC
LIMIT 10;
```

---

### 6. cancellations

**Source:** Cancellation_Report_*.csv
**Purpose:** Cancelled booking history
**Record Count:** 3,894 cancellations

#### Key Columns

| Column | Type | Description |
|--------|------|-------------|
| `canceled_on` | TEXT | When cancelled |
| `canceled_by` | TEXT | Who cancelled |
| `canceled_reason` | TEXT | Reason provided |
| `type` | TEXT | Reservation or Event |
| `start_datetime` | TIMESTAMP | Original start time |
| `event_name` | TEXT | Event name if applicable |
| `refund_amount` | REAL | Refund issued |

⚠️ **Data Quality Note:** User reported potential integrity concerns. Use with caution.

---

### 7. event_registrants

**Source:** EventRegistrantsReports*.csv
**Purpose:** Event registration details
**Record Count:** 13,165 registrations

#### Key Columns

| Column | Type | Description |
|--------|------|-------------|
| `member_number` | TEXT | Member ID |
| `event_name` | TEXT | Event name |
| `event_date` | TIMESTAMP | Event date |
| `registration_status` | TEXT | Registered, Cancelled, etc |
| `event_price` | TEXT | Registration price |
| `paid_amount` | REAL | Amount paid |
| `payment_date` | TEXT | When paid |
| `is_paid` | TEXT | Payment status |

⚠️ **For Revenue:** Use transactions table. `event_price` is registration price, may not match actual payment.

---

## Data Lineage

### Transaction Flow: CourtReserve → SQLite → Analysis

```
CourtReserve.com (SaaS Platform)
    ↓
Manual Export (Reports section)
    ↓
CSV Files → _to_process/ directory
    ↓
scripts/create_database.py
    ↓
courtreserve.db (SQLite)
    ↓
scripts/analyze_*.py
    ↓
Deliverables (reports, visualizations, insights)
```

### Table-to-Report Mapping

| SQLite Table | Source Report | Download Location | Frequency |
|--------------|---------------|-------------------|-----------|
| **transactions** | Transactions_[dates].csv | Reports → Transactions → Transactions List | Split by date range |
| **reservations** | ReservationReport_[date].csv | Reports → Reservations → Reservation Report | Single file, all dates |
| **checkins** | CheckinReports[date].csv | Reports → Check-ins → Check-in Reports | Single file, all dates |
| **members** | MembersReport_[date].csv | Reports → Members → Members Report | Current snapshot |
| **court_utilization** | CourtUtilization*.csv | Reports → Court Utilization → By Date | Single file, all dates |
| **cancellations** | Cancellation_Report_[date].csv | Reports → Reservations → Cancellation Report | Single file, all dates |
| **event_registrants** | EventRegistrantsReports[date].csv | Reports → Events → Registrant Detail | Single file, all dates |
| **event_summary** | Event_Summary*.csv | Reports → Events → Event Summary | Single file |
| **event_list** | Event_List.csv | Reports → Events → Event List | Current events |
| **instructors** | InstructorReport_[date].csv | Reports → Instructor Time | Single file |
| **sales_summary** | SalesReport[date].csv | Reports → Financial → Sales Summary | By period |

---

## Usage Guidelines

### For Revenue Analysis

**✅ DO:**
```sql
-- Calculate total revenue from transactions:
SELECT
    SUM(CAST(REPLACE(REPLACE(REPLACE(REPLACE(total, '$', ''), ',', ''), '(', ''), ')', '') AS REAL)) as revenue
FROM transactions
WHERE trans_type LIKE '%Payment%';

-- Customer spending from transactions:
SELECT
    "member_#",
    player,
    COUNT(*) as num_payments,
    SUM(CAST(...)) as total_spent
FROM transactions
WHERE trans_type LIKE '%Payment%'
GROUP BY "member_#";
```

**❌ DON'T:**
```sql
-- WRONG - Using check-ins for revenue:
SELECT SUM(price_amount) FROM checkins; -- Missing 99% of data

-- WRONG - Using member.total_paid:
SELECT SUM(total_paid) FROM members; -- May not match transactions
```

### For Attendance Analysis

**✅ DO:**
```sql
-- Count visits:
SELECT
    COUNT(*) as total_visits,
    COUNT(DISTINCT player__#) as unique_visitors
FROM checkins
WHERE check_in_status = 'Checked-In';

-- Activity preferences:
SELECT
    event_name,
    COUNT(*) as visits,
    COUNT(DISTINCT player__#) as unique_players
FROM checkins
WHERE event_name IS NOT NULL
GROUP BY event_name;
```

### For Utilization Analysis

**✅ DO:**
```sql
-- Shadow market (weekday 9 AM-4 PM):
SELECT
    AVG(utilization_pct) as avg_util,
    100 - AVG(utilization_pct) as empty_pct
FROM court_utilization
WHERE CAST(strftime('%w', date) AS INTEGER) BETWEEN 1 AND 5
  AND time_slot BETWEEN '9:00 AM - 10:00 AM' AND '3:00 PM - 4:00 PM';
```

---

## Common Pitfalls

### Pitfall #1: Using Check-Ins for Revenue

**Problem:** Check-ins only has 60 non-member records with prices, but transactions has 7,517 non-member payments.

**Solution:** Always use transactions table for revenue calculations.

### Pitfall #2: Full Event Duplication

**Problem:** Each attendance at a multi-week program shows the full program price in check-ins.

**Solution:** If using check-ins for any price analysis, exclude `registration_type = 'Full'`.

### Pitfall #3: Membership Status Values

**Problem:** Status is `"Currently Active"`, not `"Active"`.

**Solution:**
```sql
WHERE membership_status = 'Currently Active' -- Correct
-- NOT: WHERE membership_status = 'Active' -- Wrong, returns 0 rows
```

### Pitfall #4: String Currency Parsing

**Problem:** Transaction amounts are stored as TEXT with "$" and "," characters.

**Solution:**
```sql
CAST(REPLACE(REPLACE(REPLACE(REPLACE(total, '$', ''), ',', ''), '(', ''), ')', '') AS REAL)
```

### Pitfall #5: Date Format Inconsistencies

**Problem:** Some date fields are TEXT, some are TIMESTAMP.

**Solution:** Use the parsed `*_datetime` fields:
- `start_datetime` (not `start_date___time`)
- `checkin_datetime` (not `check_in_date_time`)
- `membership_start_date` (not `current_membership_start_date`)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-29 | Initial data dictionary created after comprehensive audit |

---

**See Also:**
- `validation_checklist.md` - Reports needed from CourtReserve
- `scripts/validate_data_import.py` - Automated validation
- `docs/COMPREHENSIVE_AUDIT_REPORT.md` - Audit findings
