# PCC CourtReserve Analysis - Project Structure

**Last Updated:** October 30, 2025
**Status:** Post-Audit Reorganization Complete

---

## Directory Structure

```
pcc-courtreserve-analysis/
├── data/                           # SQLite database (source of truth)
│   └── courtreserve.db            # 35MB, 11 tables, 29K+ transactions
│
├── scripts/
│   ├── active/                    # ✅ SAFE - Production-ready scripts
│   │   ├── analyze_shadow_market_heatmap.py
│   │   ├── analyze_frequency_distribution.py
│   │   ├── analyze_corrected_segments.py
│   │   ├── analyze_transaction_details.py
│   │   ├── analyze_courtreserve_jtbd.py
│   │   ├── db_loader.py           # Database connection helper
│   │   ├── create_database.py     # Database schema creation
│   │   ├── query_database.py      # Ad-hoc query interface
│   │   ├── validate_data_import.py # Monthly validation (17 checks)
│   │   └── audit_full_event_bug.py # Historical audit tool
│   │
│   ├── archive/                   # 📦 Needs inspection before use
│   │   ├── analyze_activation_journey.py
│   │   ├── analyze_cohort_retention.py
│   │   ├── analyze_daypart_patterns.py
│   │   ├── analyze_engagement_friction.py
│   │   ├── analyze_event_fill_rates.py
│   │   ├── analyze_party_size_guests.py
│   │   ├── analyze_rule_based_segments.py
│   │   └── regenerate_all_analysis.py # Needs updating
│   │
│   └── _deprecated/               # ⚠️ UNSAFE - Do not use
│       └── analyze_pay_per_use_segment.py # Uses check-ins prices (99% incomplete)
│
├── deliverables/
│   ├── data/
│   │   ├── verified/              # ✅ Oct 30, 2025 - Verified outputs
│   │   │   ├── *.csv (11 files)   # Fresh, post-audit CSVs
│   │   │   └── *.png (6 images)   # Presentation-ready visuals
│   │   └── _old/                  # Pre-audit outputs (do not use)
│   │
│   ├── docs/                      # Final reports & presentations
│   │   ├── OUTPUT_MANIFEST_FOR_PRESENTATION.md
│   │   ├── partner-presentation-v2.html
│   │   ├── partner-presentation.html
│   │   ├── presentation-refactor-context.md
│   │   ├── README-JTBD-ANALYSIS.md
│   │   └── README.md
│   │
│   ├── charts/                    # Generated charts (Google Sheets style)
│   ├── reports/                   # Historical reports
│   ├── visualizations/            # All visualization outputs
│   └── archive/                   # Old deliverables (pre-database)
│
├── docs/
│   ├── audit/                     # Post-audit findings
│   │   ├── AUDIT_EXECUTIVE_SUMMARY.md
│   │   ├── COMPREHENSIVE_AUDIT_REPORT.md
│   │   ├── mark_tomlinson_spending_analysis.md
│   │   ├── corrected_segmentation_report.md
│   │   └── CORRECTED_FIGURES_FOR_PRESENTATION.md
│   │
│   ├── analysis/                  # Technical analysis docs
│   │   ├── SCRIPT_INVENTORY.md    # Script quality audit
│   │   ├── how-to_maps-populartimes.md
│   │   ├── _New_Reports_to_Consider(Claude).md
│   │   ├── pcc_brand.md
│   │   └── PG_Writing_Styles.md
│   │
│   └── reference/                 # Schema & validation docs
│       ├── DATA_DICTIONARY.md     # Complete schema reference
│       ├── VALIDATION_CHECKLIST.md # Monthly validation workflow
│       └── DATA_VALIDATION_FRAMEWORK_SUMMARY.md
│
├── _to_process/                   # Raw CourtReserve CSV exports
├── z_processed_csv_files/         # Archived CSV files
├── tmp/                           # Temporary analysis outputs
├── archive/                       # Historical project snapshots
│
├── CLAUDE.md                      # Project guide for Claude Code
├── DATA_RESET_COMPLETE_SUMMARY.md # Post-audit summary
├── README.md                      # Project README
└── .gitignore                     # Ignore patterns
```

---

## File Inventory

### ✅ Verified Data (Oct 30, 2025)

**Location:** `deliverables/data/verified/`

**CSV Files (11):**
- `customer_classification.csv` - 2,302 customers segmented
- `pay_per_use_spending_corrected.csv` - 1,870 PPU customers
- `high_value_conversion_targets.csv` - 1,163 high-value targets
- `frequency_distribution_members.csv` - 2,259 members
- `frequency_distribution_nonmembers.csv` - 26 non-members
- `frequency_summary_members.csv`
- `frequency_summary_nonmembers.csv`
- `frequency_summary_members_corrected.csv`
- `frequency_summary_nonmembers_corrected.csv`
- `dau_wau_mau_members.csv`
- `dau_wau_mau_nonmembers.csv`

**Visualizations (6):**
- `shadow_market_heatmap.png` - PRIMARY - 74.7% empty capacity
- `transaction_wtp.png` - Willingness-to-pay distribution
- `frequency-comparison.png` - Member vs non-member frequency
- `membership-gap.png` - Value gap analysis
- `party-size-distribution.png` - Group size patterns
- `segment-distribution.png` - Customer segment breakdown

**JSON/TXT:**
- `corrected_segmentation_summary.json` - Segment metrics
- `wtp_analysis.json` - Transaction WTP data
- `shadow_market_insights.txt` - Narrative insights

---

## Script Classification

### ✅ SAFE (Active - Use for Production)

**Shadow Market Analysis:**
- `analyze_shadow_market_heatmap.py`
- Data source: `court_utilization` table
- Output: 74.7% empty capacity, $85K opportunity

**Frequency Distribution:**
- `analyze_frequency_distribution.py`
- Data source: `checkins` (counts only, NOT prices)
- Output: DAU/MAU, engagement metrics

**Corrected Segmentation:**
- `analyze_corrected_segments.py`
- Data sources: `checkins` (behavior) + `transactions` (revenue)
- Output: 1,870 PPU, 1,163 high-value, 219 program participants

**Transaction Details:**
- `analyze_transaction_details.py`
- Data source: `transactions` table (source of truth)
- Output: WTP distribution, LTV analysis

**JTBD Analysis:**
- `analyze_courtreserve_jtbd.py`
- Data sources: Multiple (uses transactions for revenue)
- Output: Behavioral clustering, personas

### ⚠️ UNSAFE (Deprecated)

**Pay-Per-Use Segment (OLD):**
- `analyze_pay_per_use_segment.py`
- Problem: Uses check-ins prices (99% incomplete)
- Status: Superseded by `analyze_corrected_segments.py`

### 📦 Needs Inspection (Archived)

7 scripts in `scripts/archive/` need review:
- Check if they use check-ins prices vs. counts
- Verify data sources before use
- See `docs/analysis/SCRIPT_INVENTORY.md` for details

---

## Data Sources (Truth Table)

| Purpose | Use Table | Do NOT Use |
|---------|-----------|------------|
| **Revenue** | `transactions` ✅ | `checkins.price_amount` ❌ |
| **Capacity** | `court_utilization` ✅ | - |
| **Attendance** | `checkins` (counts) ✅ | `checkins` (prices) ❌ |
| **Customer Roster** | `members` ✅ | - |
| **Reservations** | `reservations` ✅ | - |

**Key Rule:** For financial analysis, ALWAYS use `transactions` table.

---

## Key Metrics (Verified)

### Market Opportunity
- Weekday daytime empty: **74.7%**
- Wednesday 2-3 PM: **87.1% empty**
- Revenue opportunity: **$85,652/year**

### Financial
- Total revenue: **$634,036** (13,101 payments)
- Non-member: **66.8%**
- Member: **33.2%**

### Customer Segments
- Unique customers: **2,285**
- True pay-per-use: **1,870** ($236K revenue)
- High-value targets: **1,163** ($955/month avg)
- Program participants: **219** ($26K revenue)

### Engagement
- Avg check-ins/day: **64.8**
- DAU/MAU: **10.2%**
- Daily users (members): **1,171** (51.8%)

---

## Monthly Workflow

### 1. Export from CourtReserve
See `docs/reference/VALIDATION_CHECKLIST.md`

### 2. Import to Database
```bash
python3 scripts/active/db_loader.py
```

### 3. Validate Data
```bash
python3 scripts/active/validate_data_import.py
# Should show: ✓ ALL CHECKS PASSED
```

### 4. Run Analysis
```bash
# Shadow market
python3 scripts/active/analyze_shadow_market_heatmap.py

# Frequency patterns
python3 scripts/active/analyze_frequency_distribution.py

# Customer segmentation
python3 scripts/active/analyze_corrected_segments.py

# Transaction analysis
python3 scripts/active/analyze_transaction_details.py
```

### 5. Verify Outputs
Check `deliverables/data/verified/` for fresh CSVs and PNGs

---

## Documentation Map

**For New Users:**
1. Start with `README.md`
2. Read `CLAUDE.md` for project guide
3. Review `DATA_RESET_COMPLETE_SUMMARY.md` for context

**For Data Questions:**
- Schema: `docs/reference/DATA_DICTIONARY.md`
- Validation: `docs/reference/VALIDATION_CHECKLIST.md`
- Framework: `docs/reference/DATA_VALIDATION_FRAMEWORK_SUMMARY.md`

**For Script Questions:**
- Audit: `docs/analysis/SCRIPT_INVENTORY.md`
- Findings: `docs/audit/AUDIT_EXECUTIVE_SUMMARY.md`
- Details: `docs/audit/COMPREHENSIVE_AUDIT_REPORT.md`

**For Presentation:**
- Manifest: `deliverables/docs/OUTPUT_MANIFEST_FOR_PRESENTATION.md`
- Corrected figures: `docs/audit/CORRECTED_FIGURES_FOR_PRESENTATION.md`

---

## What Changed (Post-Audit)

### Before
- Flat structure, scripts mixed with data
- Check-ins table used for revenue (99% incomplete)
- Outputs not clearly verified

### After
- Organized by function (active/archive/deprecated)
- Transactions table established as source of truth
- Verified outputs clearly separated from old data
- Comprehensive documentation structure

### Impact
- Clearer data quality standards
- Easy to identify safe vs unsafe scripts
- Fresh outputs clearly marked
- Historical context preserved

---

## Quick Reference

**Database:** `data/courtreserve.db` (35MB, 11 tables)
**Safe Scripts:** `scripts/active/` (10 scripts)
**Verified Data:** `deliverables/data/verified/` (11 CSVs + 6 PNGs)
**Documentation:** `docs/` (audit, analysis, reference)
**Validation:** `python3 scripts/active/validate_data_import.py`

---

**Project Status:** Reorganized and Validated ✅
**Last Audit:** October 30, 2025
**Next Review:** After next monthly data import
