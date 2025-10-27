# Analysis Scripts

**Project:** PCC Customer Intelligence Center - JTBD Analysis
**Last Updated:** October 27, 2025

---

## Overview

This directory contains Python analysis scripts used to generate the Jobs-to-be-Done customer segmentation insights. All scripts are designed to be reproducible and can be re-run with updated CourtReserve data exports.

---

## Scripts

### 1. **analyze_courtreserve_jtbd.py** (Primary Analysis)

**Purpose:** Main JTBD segmentation analysis using K-Means clustering

**Inputs Required:**
- `ReservationReport_*.csv` (reservation data)
- `MembersReport_*.csv` (member roster)

**Outputs Generated:**
- `jtbd_analysis_results.json` (machine-readable results)
- `jtbd_segment_visualization.png` (cluster scatter plot)
- `jtbd_feature_distribution.png` (box plots by cluster)
- `jtbd_insights.txt` (narrative summary)

**Key Functions:**
- `extract_member_features()` - Engineers 31 behavioral features
- `perform_clustering()` - K-Means with k=5, elbow method validation
- `identify_context_switchers()` - Finds multi-job customers
- `generate_jtbd_profiles()` - Maps clusters to JTBD framework
- `calculate_revenue_opportunities()` - Quantifies addressable market

**Runtime:** ~4.2 seconds (2,227 reservations)

**Usage:**
```bash
python3 analyze_courtreserve_jtbd.py
```

**Dependencies:**
```bash
pip install pandas numpy matplotlib seaborn scikit-learn
```

---

### 2. **analyze_shadow_market_heatmap.py**

**Purpose:** Quantify weekday daytime empty capacity (the "shadow market")

**Inputs Required:**
- `CourtUtilization-by-date.csv` (299 days of hourly utilization)

**Outputs Generated:**
- `shadow_market_heatmap.png` (hour × day-of-week visualization)
- `shadow_market_insights.txt` (narrative-ready findings)

**Key Functions:**
- `load_utilization_data()` - Parse 299 days × 20 hours of data
- `parse_time_slot()` - Convert time strings to hour numbers
- `analyze_shadow_market()` - Calculate weekday 9 AM-4 PM stats
- `generate_heatmap()` - Create publication-quality visualization

**Key Findings:**
- 25.3% average utilization (74.7% empty)
- Wednesday 2-3 PM lowest at 12.9% (87.1% empty!)
- 183.1 empty court-hours/week
- $85,678/year revenue opportunity (30% fill rate)

**Runtime:** ~3.2 seconds

**Usage:**
```bash
python3 analyze_shadow_market_heatmap.py
```

**Dependencies:**
```bash
pip install pandas numpy matplotlib seaborn
```

---

### 3. **analyze_pay_per_use_segment.py**

**Purpose:** Profile non-member check-ins for conversion opportunity

**Inputs Required:**
- `CheckinReports*.csv` (15,513 check-in records)

**Outputs Generated:**
- `pay_per_use_segment.png` (4-panel analysis)
- `pay_per_use_insights.txt` (conversion strategy)

**Key Functions:**
- `parse_price()` - Extract numeric prices from check-in records
- `analyze_pay_per_use_segment()` - Profile 6,470 non-member check-ins
- `identify_high_value_targets()` - Find players spending >$80/month
- `calculate_conversion_opportunity()` - Model membership conversion

**Key Findings:**
- 1,849 unique pay-per-use players
- 6,470 check-ins (42% of ALL facility usage!)
- Mark Tomlinson: $1,081/month in drop-in fees
- 173 high-value targets spending >$80/month
- $439,322/year conversion opportunity

**Runtime:** ~4.8 seconds

**Usage:**
```bash
python3 analyze_pay_per_use_segment.py
```

**Dependencies:**
```bash
pip install pandas numpy matplotlib seaborn
```

**Technical Note:** Fixed f-string syntax error (backslash in expression) by moving string building outside f-string.

---

## Running All Scripts

To regenerate all analysis outputs:

```bash
# Install dependencies
pip install pandas numpy matplotlib seaborn scikit-learn

# Run scripts in order
python3 analyze_courtreserve_jtbd.py
python3 analyze_shadow_market_heatmap.py
python3 analyze_pay_per_use_segment.py

# Total runtime: ~12 seconds
```

---

## Data Requirements

### Input Files (CourtReserve Exports)

Place these files in the repository root:

1. **ReservationReport_*.csv**
   - Date range: Jan 29 - Oct 26, 2025 (271 days)
   - Records: 4,609 reservations
   - Fields: Start Date/Time, Player, Court, Activity Type, etc.

2. **MembersReport_*.csv**
   - Current as of: Oct 26, 2025
   - Records: 4,477 members
   - Fields: Member ID, Join Date, Status, Zip Code, etc.

3. **CourtUtilization-by-date.csv**
   - Date range: Jan 1 - Oct 26, 2025 (299 days)
   - Format: Time slots × Date columns (hourly utilization %)

4. **CheckinReports*.csv**
   - Date range: Mar 1 - Oct 26, 2025 (240 days)
   - Records: 15,513 check-ins
   - Fields: Player ID, Event Name, Price, Registration Type, etc.

### Output Files

All scripts generate outputs in the repository root:

**Images (PNG):**
- `jtbd_segment_visualization.png` (342KB)
- `jtbd_feature_distribution.png` (456KB)
- `shadow_market_heatmap.png` (251KB)
- `pay_per_use_segment.png` (501KB)

**Data (JSON):**
- `jtbd_analysis_results.json` (18KB, machine-readable)

**Insights (Text):**
- `jtbd_insights.txt`
- `shadow_market_insights.txt`
- `pay_per_use_insights.txt`

---

## Python Version

**Required:** Python 3.7+
**Tested:** Python 3.9

---

## Troubleshooting

### Import Errors

```bash
# If you see "ModuleNotFoundError"
pip install pandas numpy matplotlib seaborn scikit-learn
```

### File Not Found Errors

Ensure CourtReserve CSV files are in the repository root (one level up from scripts/):
```bash
cd ../
ls *.csv  # Should show CourtUtilization-by-date.csv, etc.
cd scripts/
python3 analyze_shadow_market_heatmap.py
```

### f-string Syntax Error (analyze_pay_per_use_segment.py)

This error was fixed in the current version. If you see it:
- Error: "f-string expression part cannot include a backslash"
- Fix: String building moved outside f-string (already applied)

### Memory Errors

If analyzing very large datasets (>100,000 records):
```python
# Add to script:
df = pd.read_csv('file.csv', low_memory=False)
```

---

## Code Quality

All scripts include:
- ✅ Docstrings for functions
- ✅ Type hints where appropriate
- ✅ Error handling for file I/O
- ✅ Clear variable naming
- ✅ Modular function design

---

## Future Enhancements

### Pending Scripts (Not Yet Implemented)

**Script 4: Geographic Distribution Mapping**
- Extract Zip Codes from MembersReport
- Identify hot zones (60614, 60657, 60622 likely)
- Map to public court locations
- Generate choropleth visualization

**Script 5: Churn Pattern Analysis**
- Filter Suspended/Expired members
- Calculate booking frequency drop-offs
- Segment churned members by prior JTBD
- Identify "Firing Criteria" patterns

---

## Integration with CIC Dashboard

All script outputs are designed for dashboard integration:

```javascript
// Load segmentation data
fetch('jtbd_analysis_results.json')
  .then(response => response.json())
  .then(data => {
    // data.segments = 9 JTBD segments
    // data.revenue_opportunities = Tier 1/2/3
    // data.context_switchers = 79 multi-job customers
  });
```

---

## Changelog

**October 27, 2025:**
- Moved all scripts to scripts/ directory
- Created README.md documentation
- Fixed f-string error in analyze_pay_per_use_segment.py

**October 26, 2025:**
- Initial script creation
- Primary JTBD analysis (analyze_courtreserve_jtbd.py)
- Shadow market analysis (analyze_shadow_market_heatmap.py)
- Pay-per-use analysis (analyze_pay_per_use_segment.py)

---

**Maintained By:** Claude Code (Anthropic)
**Project:** PCC Customer Intelligence Center
**Repository:** https://github.com/petergiordano/pcc-courtreserve-analysis
