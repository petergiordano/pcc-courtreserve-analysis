# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Pickleball Clubhouse Chicago - Customer Intelligence Center**

This repository contains Jobs-to-be-Done (JTBD) customer segmentation analysis for a pickleball facility. The analysis uses CourtReserve data exports to identify customer segments, quantify revenue opportunities, and generate strategic insights.

**Key Outputs:**
- 9 JTBD customer segments (behavioral clustering, not demographics)
- $1.41M/year revenue opportunity quantified across 3 implementation tiers
- Pay-per-use segment discovery (1,849 players, $439K conversion opportunity)
- Shadow market analysis (74.7% weekday daytime empty capacity)

## Data Architecture

### Data Flow

```
CourtReserve.com (SaaS)
  → CSV Exports (manual download)
  → _to_process/ directory
  → create_database.py → courtreserve.db (SQLite)
  → Analysis Scripts (analyze_*.py)
  → Deliverables (reports/ + visualizations/)
```

### Database (SQLite)

**Location:** `courtreserve.db` (root directory, 50-100MB, not in git)

**Create/Update Database:**
```bash
# Place fresh CSV files in _to_process/ directory
python3 scripts/create_database.py
```

**Tables:**
- `reservations` (4,609 records) - Booking history, primary data source for JTBD clustering
- `members` (4,477 records) - Member roster with membership types and zip codes
- `checkins` (15,513 records) - Check-in activity, used for pay-per-use segment analysis
- `court_utilization` (~6,000 records) - Hourly utilization percentages, used for shadow market
- `cancellations` (3,894 records) - Cancelled bookings, churn signals
- `event_registrants` (13,165 records) - Event participation data
- `transactions` (366 records) - Financial transactions (sparse data)
- Additional tables: `event_summary`, `event_list`, `instructors`, `sales_summary`

**Query Database:**
```bash
python3 scripts/query_database.py  # Summary statistics
```

**Access Pattern:** Most analysis scripts use `db_loader.py` module to access database:
```python
from db_loader import CourtReserveDB

with CourtReserveDB() as db:
    reservations = db.get_reservations()
    members = db.get_members()
    checkins = db.get_checkins()
```

### CSV File Management

**Fresh Downloads:** `_to_process/` - Place new CSV exports here
**Processed Files:** `z_processed_csv_files/` - Archive after database creation
**Download Guide:** `_courtreserve_reports_download_guide.md` - Complete instructions for downloading reports from CourtReserve.com

**Required CSV Reports:**
1. Court Utilization by Date (299 days × 20 hours)
2. Reservation Report (4,609 records, Jan-Oct 2025)
3. Check-in Reports (15,513 records)
4. Members Report (4,477 members)
5. Event Registrants Reports (13,165 registrations)
6. Cancellation Report (3,894 cancellations)
7. Transactions Report (366 transactions)

## Running Analysis

### Full Analysis Regeneration

Regenerate all deliverables with fresh data:
```bash
python3 scripts/regenerate_all_analysis.py
```

This master script runs all analysis scripts in order and generates visualizations, reports, and JSON outputs.

### Individual Analysis Scripts

Run specific analyses independently:

```bash
# Core JTBD clustering (K-Means, context switching)
python3 scripts/analyze_courtreserve_jtbd.py
# Outputs: segment_clusters.png, segment_distribution.png,
#          booking_time_heatmaps.png, jtbd_analysis_results.json

# Shadow market analysis (weekday daytime capacity)
python3 scripts/analyze_shadow_market_heatmap.py
# Outputs: shadow_market_heatmap.png, shadow_market_insights.txt

# Pay-per-use segment (non-member conversion opportunity)
python3 scripts/analyze_pay_per_use_segment.py
# Outputs: pay_per_use_segment.png, pay_per_use_insights.txt
```

**Additional analyses available:**
- `analyze_activation_journey.py` - New member onboarding patterns
- `analyze_cohort_retention.py` - Month-over-month retention
- `analyze_daypart_patterns.py` - Time-of-day usage patterns
- `analyze_engagement_friction.py` - Drop-off and friction points
- `analyze_event_fill_rates.py` - Programming capacity utilization
- `analyze_frequency_distribution.py` - Booking frequency patterns
- `analyze_party_size_guests.py` - Group size analysis
- `analyze_rule_based_segments.py` - Business rule segmentation
- `analyze_transaction_details.py` - Revenue pattern analysis

### Dependencies

```bash
pip install pandas numpy matplotlib seaborn scikit-learn sqlite3
```

## Key Analysis Concepts

### JTBD Framework

Segments customers by **what job they're hiring the facility to do**, not demographics:

1. **Competitive Improver** - League players, high engagement
2. **Social Connector** - Large party sizes, diverse activities
3. **Weekend Warrior** - 85%+ weekend bookings
4. **Weekend Morning Enthusiast** - Family-oriented
5. **Context Switcher** - Multi-job behavior (79 customers)
6. **Pay-Per-Use Fence-Sitter** - 1,849 non-members (42% of facility usage!)
7. **Corporate Event Planner** - B2B segment
8. **Pickle-Curious Beginner** - Non-players, awareness phase
9. **Frustrated Public Court Player** - Adjacent market

### Behavioral Clustering

**Algorithm:** K-Means with k=5 clusters (elbow method + silhouette validation)

**Feature Engineering:** 31 behavioral features extracted from reservation data:
- Booking frequency and recency
- Time preferences (weekday/weekend, morning/evening)
- Activity type diversity (Open Play, Drills, Leagues, Tournaments)
- Advance booking patterns
- Party size and guest behavior
- Cancellation patterns
- Payment behavior

**Location:** `scripts/analyze_courtreserve_jtbd.py:extract_member_features()`

### Context Switching

Identifies customers who exhibit multiple JTBD behaviors (e.g., competitive player during week, social connector on weekends). These 79 customers represent opportunities for specialized programming.

**Location:** `scripts/analyze_courtreserve_jtbd.py:identify_context_switchers()`

## Deliverables Structure

```
deliverables/
├── README.md                    # Partner-facing guide (START HERE)
├── README-JTBD-ANALYSIS.md      # Technical usage guide
├── reports/
│   ├── PARTNER_NARRATIVE_Customer_Intelligence_Strategy.md  ⭐ Primary deliverable
│   ├── jtbd-analysis-report-enhanced.md                    # Technical report
│   └── ENHANCEMENT_SUMMARY.md                              # Project changes log
└── visualizations/              # Publication-quality PNG files (300 DPI)
    ├── shadow_market_heatmap.png
    ├── pay_per_use_segment.png
    ├── segment_clusters.png
    ├── segment_distribution.png
    └── booking_time_heatmaps.png
```

**Partner Narrative** is the primary stakeholder document (9,461 words, story-driven, non-technical).

## Output Locations

**Analysis outputs** are generated in root directory during script execution, then manually moved to `deliverables/` after review:

- Images: `*.png` files (root) → `deliverables/visualizations/`
- Data: `*.json` files (root) → `deliverables/data/`
- Insights: `*_insights.txt` files (root) → used for report writing

## Common Development Tasks

### Adding a New Analysis Script

1. Create `scripts/analyze_[feature_name].py`
2. Import database loader: `from db_loader import CourtReserveDB`
3. Follow existing script pattern (load data → analyze → visualize → export)
4. Add to `scripts/regenerate_all_analysis.py` if part of standard deliverables
5. Document in `scripts/README.md`

### Updating Database Schema

Modify `scripts/create_database.py`:
- Add new CSV pattern to `CSV_PATTERNS` dict
- Add import logic in `create_database()` function
- Add indexes for commonly filtered fields
- Update `scripts/DATABASE_README.md` with new table documentation

### Querying Database

Use utility module or direct SQL:

```python
# Option 1: Use db_loader module
from scripts.db_loader import CourtReserveDB
with CourtReserveDB() as db:
    df = db.get_reservations(start_date='2025-01-01')

# Option 2: Direct SQL
from scripts.query_database import run_query
df = run_query("SELECT * FROM members WHERE membership_status = 'Active'")
```

## Data Quality Notes

**Sparse Data:**
- Transactions table has only 366 records for 4,477 members (use as supplementary only)
- Cancellation data has integrity concerns (validated caution advised)

**Date Ranges:**
- Court Utilization: Jan 1 - Oct 26, 2025 (299 days comprehensive)
- Reservations: Jan 29 - Oct 26, 2025 (271 days)
- Check-ins: Mar 1 - Oct 26, 2025 (240 days)
- Members: Current snapshot as of Oct 26, 2025

**Data Cleaning:** Scripts handle missing values, parse dates, convert currency strings to numeric, and standardize field names.

## Project Context

**Client:** Pickleball Clubhouse Chicago (PCC)
**Business Goal:** Increase revenue through customer intelligence and targeted programming
**Analysis Period:** January - October 2025 (10 months)
**Total Records:** 23,000+ data points analyzed
**Revenue Opportunity:** $1.41M/year across 3 implementation tiers

**Key Finding:** 1,849 pay-per-use players paying drop-in fees (many paying MORE than membership costs). Mark Tomlinson example: $1,081/month in drop-ins vs. $120 membership. This represents a $439K/year conversion opportunity.

## Testing

No formal test suite. Analysis validation done through:
- Data quality checks in each script (record counts, date ranges)
- Silhouette scores and Davies-Bouldin index for clustering quality
- Manual review of visualizations and narrative outputs
- Cross-validation against business knowledge (stakeholder feedback)

## Git Workflow

**Tracked:** Source code, documentation, deliverables (markdown reports, visualizations)
**Ignored:** `courtreserve.db`, CSV files, `*.log` files, `__pycache__`, `.DS_Store`

**Archive Strategy:** Old reports and visualizations moved to `deliverables/archive/[date]/` when regenerated.

## Performance Notes

- Database creation: ~10-15 seconds
- JTBD clustering analysis: ~4.2 seconds
- Shadow market analysis: ~3.2 seconds
- Pay-per-use analysis: ~4.8 seconds
- Full regeneration: ~60 seconds total

Large result sets (>10,000 rows) should use pandas chunking or SQL LIMIT clauses.
