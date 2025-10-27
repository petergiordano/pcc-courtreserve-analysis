# CourtReserve Reports - Download Guide

**Purpose:** Instructions for downloading reports from CourtReserve.com to run JTBD analysis

**Target System:** CourtReserve.com (Facility Management System)

**Last Updated:** October 27, 2025

---

## Overview

This analysis requires 7 core reports from CourtReserve. Download these reports with the settings specified below, then place the CSV files in the repository root directory.

**Recommended Download Frequency:** Monthly (to capture trends over time)

---

## Core Reports (Required)

### 1. **Court Utilization by Date** ⭐ CRITICAL

**Report Location:** CourtReserve.com → Reports → Court Utilization

**Settings:**
- **Start Date:** January 1, [Current Year]
- **End Date:** [Current Date]
- **Reservation Types:** ALL
- **Event Categories:** ALL
- **Court Types:** ALL
- **Courts:** ALL
- **Computed By:** Utilized Courts
- **View:** By Date

**Expected Output:** `CourtUtilization-by-date.csv`
- e.g. `Court_Util_2025-01-01-2025-10-26-Group-by_Date-Calc-by-Court-util.csv`
- Format: Time slots (rows) × Date columns (5:00 AM - 12:00 AM)
- Values: Utilization percentages (e.g., "45.2 %")
- Example records: 299 days × 20 hourly time slots = ~6,000 data points

**Purpose:**
- Shadow market analysis (weekday 9 AM-4 PM empty capacity)
- Heatmap visualization (hour × day-of-week)
- Revenue opportunity calculation

**Analysis Script:** `scripts/analyze_shadow_market_heatmap.py`

---

### 2. **Reservation Report** ⭐ CRITICAL

**Report Location:** CourtReserve.com → Reports → Reservations → Reservation Report

**Settings:**
- **Start Date:** January 1, [Current Year] (or earliest available)
- **End Date:** [Current Date]
- **Filters:** None (include all reservation types)
- **Include:** Paid, Unpaid, Cancelled reservations

**Expected Output:** `ReservationReport_[YYYY-MM-DD]_[HH-MM-AM/PM].csv`
- e.g. `ReservationReport_2025-01-01-to-2025-10-27_04-43-PM.csv`
- Records: 4,000-5,000+ reservations (depends on facility size)
- Date Range: 271+ days recommended

**Key Fields:**
- Confirmation_#
- Reservation Type
- Start Date / Time
- End Date / Time
- Is Event?
- Event Name
- Courts
- Player Name, Player Email, Player _#
- Members (comma-separated list)
- Created On, Created By
- Payment Status
- Fee Amount
- Revenue Category

**Purpose:**
- Primary JTBD segmentation (K-Means clustering)
- Behavioral feature engineering (31 features)
- Context switching analysis
- Booking pattern analysis

**Analysis Script:** `scripts/analyze_courtreserve_jtbd.py`

---

### 3. **Check-in Reports** ⭐ CRITICAL

**Report Location:** CourtReserve.com → Reports → Check-ins → Check-in Reports

**Settings:**
- **Start Date:** January 1, [Current Year] (or earliest available)
- **End Date:** [Current Date]
- **Include:** All check-in types (Member, Non-Member/Visitor, Drop-In)

**Expected Output:** `CheckinReports[YYYY-MM-DD]_[HH-MM-AM/PM].csv`
- e.g. `CheckinReports_2025-01-01-to-2025-10-27_04-47-PM.csv`
- Records: 15,000+ check-ins (depends on facility traffic)
- Date Range: 240+ days recommended

**Key Fields:**
- Player _#
- Player First Name, Player Last Name
- Check-in Date/Time
- Registration Type (e.g., "Drop-In", "Non-Member/Visitor", "Reservation")
- Event Name
- Date/Time (event start/end)
- Check-in Type (Staff, Self)
- Checked-in By
- Check-In Status
- Pickleball Rating
- Membership Name (e.g., "Individual Membership", "Non-Member/Visitor")
- Price (e.g., "(Drop-in) $16.00")

**Purpose:**
- **Pay-per-use segment discovery** (1,849 non-members identified)
- Activity type analysis (Open Play, Drills, Leagues)
- Time-of-day preference patterns
- High-value conversion target identification (>$80/month)

**Analysis Script:** `scripts/analyze_pay_per_use_segment.py`

---

### 4. **Members Report**

**Report Location:** CourtReserve.com → Reports → Members → Members Report

**Settings:**
- **Report Date:** [Current Date]
- **Include:** All member statuses (Active, Suspended, Expired)
- **Fields:** Include all available fields (especially Zip Code)

**Expected Output:** `MembersReport_[YYYY-MM-DD]_[HH-MM-AM/PM].csv`
- e.g. `MembersReport_2025-10-27_11-52-AM.csv`
- Records: 4,000-5,000+ member records
- Snapshot: Current membership roster as of download date

**Key Fields:**
- Member _#
- First Name, Last Name
- Email
- Membership Type (e.g., "Individual", "Family", "Corporate")
- Membership Status (Active, Suspended, Expired)
- Current Membership Start Date
- Zip Code (for geographic analysis)
- Phone
- Date of Birth
- Join Date

**Purpose:**
- Member profile enrichment
- Geographic distribution mapping (pending: Script 4)
- Churn analysis (pending: Script 5)
- Membership tier analysis

**Analysis Script:** `scripts/analyze_courtreserve_jtbd.py` (primary), future geographic/churn scripts

---

### 5. **Event Registrants Reports**

**Report Location:** CourtReserve.com → Reports → Events → Registrant Detail

**Settings:**
- **Start Date:** January 1, [Current Year]
- **End Date:** [Current Date]
- **Include:** All event types (Clinics, Drills, Tournaments, Leagues, Social)

**Expected Output:** `EventRegistrantsReports[YYYY-MM-DD]_[HH-MM-AM/PM].csv`
- e.g. `EventRegistrantsReports_2025-01-01-to-2025-10-27_04-56-PM.csv`
- Records: 13,000+ registrations
- Date Range: 264+ days

**Key Fields:**
- Event Date
- Event Name
- Event Type
- Player Name, Player _#
- Registration Status
- Payment Status
- Fee Amount

**Purpose:**
- Programming participation analysis
- Event type preference by segment
- Revenue per event type

**Analysis Script:** Currently used for validation, not primary analysis

---

### 6. **Cancellation Report**

**Report Location:** CourtReserve.com → Reports → Reservations → Cancellation Report
**NOTE** When the report is downloaded, courtreserve.com names it `ReservationReport_[YYYY-MM-DD]_[HH-MM-AM/PM].xlsx` 
The user needs to rename it to `Cancellation_Report_[YYYY-MM-DD]_[HH-MM-AM/PM].xlsx`

**Settings:**
- **Start Date:** January 1, [Current Year]
- **End Date:** [Current Date]
- **Include:** All cancellation reasons

**Expected Output:** `Cancellation_Report_[YYYY-MM-DD]_[HH-MM-AM/PM].csv`
- Records: 3,000-4,000 cancellations
- Date Range: 265+ days

**Key Fields:**
- Confirmation_#
- Start Date / Time
- Player Name, Player _#
- Cancellation Reason
- Cancelled On, Cancelled By

**Purpose:**
- Churn signal analysis
- "Firing criteria" identification (future: Script 5)
- Customer dissatisfaction patterns

**⚠️ Data Quality Note:** User advised caution - potential integrity concerns. Do not make deep assumptions without validation.

**Analysis Script:** Future churn analysis (pending)

---

### 7. **Transactions Report**

**Report Location:** CourtReserve.com → Transactions → Transactions List

**Settings:**
- **Start Date:** January 1, [Current Year]
- **End Date:** [Current Date]
- **Transaction Types:** ALL (Charges, Payments, Refunds)

**Expected Output:** `Transactions-2025.csv` or `Transactions_report.csv`
- Records: 300-400+ transactions (may be sparse)
- Date Range: 274+ days

**Key Fields:**
- Trans. Date
- Member _#
- Member Name
- Amount
- Transaction Type
- Payment Method
- Description

**Purpose:**
- Revenue validation
- Willingness-to-pay (WTP) proxy
- Membership tier spending patterns

**⚠️ Data Quality Note:** Sparse data (366 records for 4,477 members). Used as supplementary only.

**Analysis Script:** Supporting data for `scripts/analyze_courtreserve_jtbd.py`

---

## Supplementary Reports (Optional)

### 8. **Sales Report**

**Report Location:** CourtReserve.com → Reports → Financial → Sales Summary

**Settings:**
- **Report Period:** Month-to-date or custom range
- **Include:** All revenue categories

**Expected Output:** `SalesReport[YYYY-MM-DD]_[HH-MM-AM/PM].csv`
- Records: 60-75 summary rows (by revenue category)

**Purpose:**
- Revenue breakdown validation
- Category-level financial analysis

**Analysis Script:** Not currently used in primary analysis

---

### 9. **Instructor Report**

**Report Location:** CourtReserve.com → Reports → Instructor Time

**Expected Output:** `InstructorReport_[YYYY-MM-DD]_[HH-MM-AM/PM].csv`
- Downloadas e.g. `InstructorReport_2025-10-27_05-30-PM.csv` 
- need to rename to have data range, `InstructorReport_2025-01-01-to-2025-10-27_05-30-PM.csv`
- Records: 10-20 instructors

**Purpose:**
- Programming capacity analysis
- Instructor utilization

**Analysis Script:** Not currently used in primary analysis

---

### 10. **Event List**

**Report Location:** CourtReserve.com → Reports → Events → Event Summary

**Expected Output:** `Event_Summary.csv`
- Downloads as `Event_Summary.xlsx`
- Rename to `Event_Summary_2025-01-01-to-2025-10-27.xlsx`
- Records: 75+ event types offered

**Purpose:**
- Programming mix analysis
- Event type catalog

**Analysis Script:** Not currently used in primary analysis

---

### 11. **Event Registrant Summary**

**Report Location:** CourtReserve.com → Reports → Events → Registrant Summary

**Expected Output:** `Event_Registrant_Summary.csv`
- Downloads as `Event_Registrant_Summary.xlsx`
- Rename to `Event_Registrant_Summary_2025-01-01-to-2025-10-27.xlsx`

**Purpose:**
- Event-level metrics (attendance, revenue)
- Programming performance analysis

**Analysis Script:** Not currently used in primary analysis

---
### 12. **Events Registrant Detail**
**Report Location:** CourtReserve.com → Reports → Events → Registrant Detail
- Downloads as `EventRegistrantsReports2025-10-27_05-39-PM.xlsx`
- Rename to `EventRegistrantReports_2025-01-01-to-2025-10-27.csv`
**Expected Output:** `EventRegistrantReports_2025-01-01-to-2025-10-27.csv`


---
### 13. **Court Sheet Reports**

**Report Location:** CourtReserve.com → Reports → Court Sheet

**Variants:**
- Calendar View: `CourtSheet-calendarview.csv`
- Utilization by Number of Courts: `CourtSheet-utilization-by-number-of-courts.csv`

**Purpose:**
- Alternative utilization views
- Court-specific analysis

**Analysis Script:** Not currently used (Court Utilization by Date is primary)

---

## Download Checklist

Use this checklist when downloading reports:

### Core Reports (Required for Analysis)
- [ ] **Court Utilization by Date** (Jan 1 - Current, ALL filters)
- [ ] **Reservation Report** (Jan 1 - Current, all types)
- [ ] **Check-in Reports** (Jan 1 - Current, all check-ins)
- [ ] **Members Report** (Current roster, include Zip Code)
- [ ] **Event Registrants** (Jan 1 - Current)
- [ ] **Cancellation Report** (Jan 1 - Current)
- [ ] **Transactions Report** (Jan 1 - Current)

### Optional Reports
- [ ] Sales Report
- [ ] Instructor Report
- [ ] Event List
- [ ] Event Summary
- [ ] Events Registrant Detail
- [ ] Court Sheet variants

---

## File Naming Conventions

CourtReserve auto-generates filenames with this pattern:
```
[ReportType][YYYY-MM-DD]_[HH-MM-AM/PM].csv
```

**Examples:**
- `ReservationReport_2025-10-27_04-10-AM.csv`
- `CheckinReports2025-10-26_09-55-PM.csv`
- `MembersReport_2025-10-26_04-58-PM.csv`

**Keep the original filenames** - they contain useful metadata (download date/time).

---

## After Downloading

### 1. Place Files in _to_process/ Directory

```bash
pcc-courtreserve-analysis/
├── _to_process/                    ⭐ PUT NEW CSV FILES HERE
│   ├── CourtUtilization-by-date.csv
│   ├── ReservationReport_2025-10-27_04-10-AM.csv
│   ├── CheckinReports2025-10-26_09-55-PM.csv
│   ├── MembersReport_2025-10-26_04-58-PM.csv
│   ├── EventRegistrantsReports2025-10-27_04-14-AM.csv
│   ├── Cancellation_Report_2025-10-27_04-22-AM.csv
│   └── Transactions-2025.csv
├── z_processed_csv_files/          (old CSV files, already analyzed)
└── scripts/                        (analysis scripts)
```

### 2. Run Analysis Scripts

```bash
# Install dependencies (first time only)
pip install pandas numpy matplotlib seaborn scikit-learn

# Run analysis scripts
python3 scripts/analyze_courtreserve_jtbd.py
python3 scripts/analyze_shadow_market_heatmap.py
python3 scripts/analyze_pay_per_use_segment.py

# Total runtime: ~12 seconds
```

### 3. Check Outputs

Generated files (in repository root):
- `jtbd_segment_visualization.png` (cluster plot)
- `jtbd_feature_distribution.png` (box plots)
- `shadow_market_heatmap.png` (utilization heatmap)
- `pay_per_use_segment.png` (4-panel analysis)
- `jtbd_insights.txt` (narrative summary)
- `shadow_market_insights.txt` (capacity findings)
- `pay_per_use_insights.txt` (conversion strategy)
- `jtbd_analysis_results.json` (machine-readable)

### 4. Review Deliverables

Check `deliverables/` directory for generated reports:
- `deliverables/README.md` (partner guide)
- `deliverables/reports/` (3 finalized reports)
- `deliverables/visualizations/` (5 charts)

---

## Data Quality Checks

### Expected Record Counts (10-Month Analysis)

| Report | Expected Records | Our Analysis |
|--------|------------------|--------------|
| Court Utilization | 299 days × 20 hours | ✅ 299 days |
| Reservations | 4,000-5,000+ | ✅ 4,609 |
| Check-ins | 15,000+ | ✅ 15,513 |
| Members | 4,000-5,000+ | ✅ 4,477 |
| Event Registrants | 13,000+ | ✅ 13,165 |
| Cancellations | 3,000-4,000+ | ✅ 3,894 |
| Transactions | 300-400+ | ⚠️ 366 (sparse) |

### Date Range Validation

Ensure reports cover overlapping periods:
- **Minimum:** 3-6 months (quarterly analysis)
- **Recommended:** 10-12 months (seasonal patterns)
- **Ideal:** 12+ months (full year trends)

---

## Troubleshooting

### Report Not Available
**Issue:** Some reports may be restricted by user permissions.
**Solution:** Contact CourtReserve admin or use Facility Manager account.

### Date Range Too Large
**Issue:** CourtReserve may timeout on very large date ranges.
**Solution:** Split into 3-month chunks, then combine CSV files manually.

### Missing Fields
**Issue:** Downloaded CSV missing key fields (e.g., Zip Code).
**Solution:** Check CourtReserve report settings - ensure "All Fields" is selected.

### Duplicate Downloads
**Issue:** Multiple versions of same report with different timestamps.
**Solution:** Keep the most recent version (largest file size). Archive older versions to `archive/csv-duplicates/`.

---

## Monthly Update Process

To update analysis with latest data:

1. **Download Latest Reports** (use checklist above)
2. **Replace Old CSV Files** in repository root
3. **Re-run Analysis Scripts**
   ```bash
   python3 scripts/analyze_courtreserve_jtbd.py
   python3 scripts/analyze_shadow_market_heatmap.py
   python3 scripts/analyze_pay_per_use_segment.py
   ```
4. **Review Updated Deliverables** in `deliverables/` directory
5. **Compare Trends** (month-over-month changes in segments, utilization, conversion targets)

---

## Questions?

**For report access issues:** Contact CourtReserve Support (support@courtreserve.com)

**For analysis questions:** See `scripts/README.md` or `deliverables/README.md`

**For data quality concerns:** Reference `deliverables/reports/jtbd-analysis-report-enhanced.md` Appendix C

---

**Document Version:** 1.0
**Last Updated:** October 27, 2025
**Maintained By:** PCC Customer Intelligence Team
