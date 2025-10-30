# Mark Tomlinson Spending Analysis - Discrepancy Resolution

**Date:** October 29, 2025
**Customer ID:** 7336003
**Status:** Non-Member/Visitor (Currently Active)
**Analysis Period:** September 1 - October 27, 2025

---

## Executive Summary

**The correct spending figure is $925.40** (from CourtReserve transaction records).

The presentation figure of $1,081 and the user-mentioned $925 both appear to be estimates or calculations from different time periods. The actual transaction records show **$925.40 in payments** from Sept 1 to Oct 27, 2025.

---

## Detailed Findings

### 1. Transaction Record Analysis (SOURCE OF TRUTH)

From CourtReserve Transaction Reports (`Transactions_2025-09-01-to-2025-10-27.csv`):

| Date | Type | Amount | Description |
|------|------|--------|-------------|
| 9/1/2025 | Payment | $660.00 | Advanced Beginner Drills and Skills (6-week session) |
| 9/22/2025 | Payment | $35.00 | Private Group reservation |
| 10/12/2025 | Payment | $165.00 | Intermediate Drills and Skills (6-week session) |
| 10/16/2025 | Payment | $65.40 | Whole Court reservation ($60 + $5.40 tax) |

**Total Payments: $925.40**

**Time Period:** September 1 - October 27, 2025 (57 days)

---

### 2. Check-in Records Analysis (MISLEADING DATA)

The check-ins table shows a TOTAL of $4,325.00, but this is **incorrect for calculating monthly spending** because:

**Problem: "Full Event" prices are 6-week session totals, not per-visit charges**

| Check-ins | Event | Price Shown | What It Actually Is |
|-----------|-------|-------------|---------------------|
| 6 checkins | Advanced Beginner Drills | $660.00 each | **WRONG**: This is the full 6-week session price ($660 total), NOT per-visit |
| 2 checkins | Intermediate Drills | $165.00 each | **WRONG**: This is the full 6-week session price ($165 total), NOT per-visit |
| 1 checkin | Private Group | $35.00 | **CORRECT**: Single reservation |
| 1 checkin | Reservation | blank | Likely complimentary |

**Database Calculation:** $4,325.00 (6×$660 + 2×$165 + $35)
**Reality:** Mark paid only once for each session, NOT every time he checked in

---

### 3. Root Cause of Discrepancy

#### Database Issue:
The `checkins` table duplicates the "Full Event" price for every check-in when someone attends a multi-week program:

- **Advanced Beginner Drills & Skills**: $660 for 6 weeks
  - Mark attended 6 sessions → Database shows 6 × $660 = $3,960 ❌
  - He paid once → Transaction shows 1 × $660 = $660 ✓

- **Intermediate Drills & Skills**: $165 for 6 weeks
  - Mark attended 2 sessions (so far) → Database shows 2 × $165 = $330 ❌
  - He paid once → Transaction shows 1 × $165 = $165 ✓

#### Why This Happens:
CourtReserve's check-in system associates the "Full Event" price with every check-in for multi-session programs, even though customers only pay once upfront for the entire series.

---

### 4. Breakdown of Actual Spending

| Category | Amount | Details |
|----------|--------|---------|
| **Drills & Skills Programs** | $825.00 | Two 6-week sessions |
| • Advanced Beginner (6 weeks) | $660.00 | Paid 9/1/2025 |
| • Intermediate (6 weeks) | $165.00 | Paid 10/12/2025 |
| **Court Reservations** | $100.40 | Drop-in bookings |
| • Private Group | $35.00 | 9/22/2025 |
| • Whole Court | $65.40 | 10/16/2025 |
| **TOTAL** | **$925.40** | Sept 1 - Oct 27, 2025 |

---

### 5. Monthly Spending Calculation

**Time Period:** 57 days (Sept 1 - Oct 27, 2025)
**Monthly Average:** $925.40 × (30/57) = **$487/month**

**NOTE:** This is still significantly higher than membership costs:
- Individual Membership: ~$120/month
- Mark's current spending: $487/month (4× membership cost!)

**Conversion Opportunity Confirmed:** Mark is a prime conversion target.

---

### 6. Where Did $1,081 Come From?

Possible sources of the $1,081 figure in the presentation:

1. **Different time period**: May have included July-August data
2. **Projection**: $925 over 57 days projected to 60 days = $974; rounded up with estimates
3. **Including future commitments**: If he stays enrolled in Intermediate Drills for all 6 weeks
4. **Manual calculation error**: Using check-in data instead of transaction data

**Recommendation:** Update presentation to use **$925** (round down from $925.40) as the verified amount for the Sept 1 - Oct 27 period.

---

### 7. Data Quality Issues Identified

#### For Future Analysis:

1. **Never use `checkins.price_amount` for spend calculations on multi-session events**
   - Use `transactions` table as source of truth
   - Check-in prices inflate totals for program participants

2. **Filter logic needed:**
   ```sql
   -- WRONG (inflates totals):
   SELECT SUM(price_amount) FROM checkins WHERE player__# = 7336003;

   -- RIGHT (actual payments):
   SELECT SUM(total) FROM transactions WHERE member_# = '7336003' AND trans_type = 'Payment';
   ```

3. **Pay-per-use analysis should exclude full event registrations**
   - Only count drop-in fees: Reservation, Drop-In, Private Group
   - Exclude: Full Event registrations (these are programs, not drop-ins)

---

### 8. Corrected Customer Profile

**Mark Tomlinson (ID: 7336003)**
- **Status:** Non-Member/Visitor
- **Actual Spending:** $925.40 (Sept 1 - Oct 27, 2025)
- **Monthly Rate:** ~$487/month
- **Membership Cost:** ~$120/month
- **Savings Potential:** $367/month ($4,400/year)
- **Segment:** **Program Participant** (not pure pay-per-use)
- **Behavior:** Enrolls in 6-week drills programs + occasional drop-in reservations

**Conversion Strategy:**
- Emphasize drills program access included in membership
- Show $4,400/year savings
- Offer "upgrade path" since he's already committed to programming

---

## Recommendations

### 1. Update Presentation Materials
- Change $1,081 to **$925** (verified amount)
- Add timeframe: "Sept 1 - Oct 27, 2025"
- Note: "Based on CourtReserve transaction records"

### 2. Fix Database Query Logic
Update `scripts/analyze_pay_per_use_segment.py` to:
```python
# Exclude "Full" registrations (multi-session programs)
pay_per_use_df = checkins[
    (checkins['membership_name'].str.contains('Non-Member|Visitor')) &
    (checkins['registration_type'] != 'Full')  # ADD THIS LINE
]
```

### 3. Segment Refinement
Mark should be recategorized:
- **Not:** Pay-Per-Use Fence-Sitter
- **Actually:** Program Enthusiast (Non-Member)

### 4. Re-run Pay-Per-Use Analysis
With corrected logic, recalculate:
- True pay-per-use players (exclude program enrollees)
- Accurate spending totals per customer
- Revised conversion targets

---

## Verification Checklist

- [x] Queried database transactions table
- [x] Verified against CSV transaction files
- [x] Analyzed check-in records
- [x] Identified date range discrepancies
- [x] Checked for duplicate entries (none found in transactions)
- [x] Explained inflation in check-in data
- [x] Calculated correct monthly average
- [x] Documented data quality issues

---

## Files Analyzed

1. Database: `courtreserve.db` (transactions, checkins, members tables)
2. CSV: `_to_process/Transactions_2025-09-01-to-2025-10-27.csv`
3. CSV: `_to_process/CheckinReports_2025-01-01-to-2025-10-27_04-47-PM.csv`
4. CSV: `_to_process/MembershipStatusReport_25-10-30.csv` (membership status only)

---

**Conclusion:** Use $925 as Mark Tomlinson's verified spending amount. The discrepancy arose from using check-in data (which duplicates event prices) instead of transaction data (which shows actual payments).
