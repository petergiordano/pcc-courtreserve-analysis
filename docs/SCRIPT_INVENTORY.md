# Script Inventory - Data Quality Audit

**Date:** October 30, 2025
**Status:** Post-Audit Classification

---

## Classification Legend

- **✅ SAFE** - Uses correct data sources (transactions, court_utilization, attendance counts)
- **⚠️ UNSAFE** - Uses check-ins prices/revenue (99% incomplete for non-members)
- **📦 ARCHIVE** - Superseded by corrected versions or obsolete
- **🔧 UTILITY** - Infrastructure scripts (database, validation)

---

## Analysis Scripts

### ✅ SAFE - Ready for Production

#### 1. analyze_shadow_market_heatmap.py
**Status:** ✅ SAFE - VERIFIED CORRECT
**Data Source:** `court_utilization` table
**Purpose:** Quantifies weekday 9 AM-4 PM empty capacity
**Output:**
- `deliverables/visualizations/shadow_market_heatmap.png`
- `deliverables/data/shadow_market_summary.json`

**Key Metrics:**
- 74.7% weekday daytime empty
- Wednesday 2-3 PM: 87.1% empty
- $85K/year revenue opportunity (30% fill rate)

**Why Safe:** Uses utilization percentages, not financial data

**Action:** ✅ RE-RUN to regenerate outputs

---

#### 2. analyze_transaction_details.py
**Status:** ✅ SAFE - USES CORRECT SOURCE
**Data Source:** `transactions` table (source of truth)
**Purpose:** Willingness-to-pay analysis from actual payments
**Output:**
- Transaction value distributions
- LTV calculations
- Revenue concentration metrics

**Why Safe:** Uses transactions table (29,752 records), the ONLY reliable financial source

**Action:** ✅ RE-RUN to regenerate outputs

---

#### 3. analyze_frequency_distribution.py
**Status:** ✅ SAFE - USES ATTENDANCE COUNTS
**Data Source:** `checkins` table (COUNT only, not prices)
**Purpose:** Segment customers by usage intensity
**Output:**
- `deliverables/data/frequency_summary.csv`
- DAU/WAU/MAU metrics
- Churn risk flagging

**Why Safe:** Uses check-in counts, not price_amount field

**Action:** ✅ RE-RUN to regenerate outputs

---

#### 4. analyze_corrected_segments.py
**Status:** ✅ SAFE - POST-AUDIT VERSION
**Data Source:** `checkins` (behavior), `transactions` (revenue)
**Purpose:** Properly segment customers excluding Full event duplication
**Output:**
- True pay-per-use: 1,870 customers
- Program participants: 219 customers
- High-value targets: 1,163 customers (>$80/month)

**Why Safe:**
- Excludes `registration_type='Full'` from calculations
- Cross-validates against transactions table

**Action:** ✅ RE-RUN to regenerate outputs

---

#### 5. analyze_courtreserve_jtbd.py
**Status:** ✅ SAFE - COMPLEX BEHAVIORAL ANALYSIS
**Data Source:** Multiple tables (reservations, checkins, members, transactions)
**Purpose:** K-Means clustering for JTBD behavioral segmentation
**Output:**
- 31-feature behavioral clusters
- Customer personas
- Context switcher identification

**Why Safe:** Uses transactions for revenue, check-ins for behavioral patterns (counts)

**Note:** Complex script, uses 31 engineered features. Outputs may need refresh but methodology is sound.

**Action:** ⏸️ REVIEW outputs, may need re-run depending on persona needs

---

### ⚠️ UNSAFE - DO NOT USE FOR PRESENTATION

#### 6. analyze_pay_per_use_segment.py
**Status:** ⚠️ UNSAFE - USES CHECK-INS PRICES
**Data Source:** `checkins` table price_amount field
**Purpose:** Profile pay-per-use segment
**Problem:** Check-ins missing 99% of non-member revenue

**Why Unsafe:**
- Relies on `price_amount` from check-ins
- Only captures 60 non-member records with prices
- Missing 7,457+ non-member transactions
- Revenue calculations are 99% incomplete

**Action:** 📦 ARCHIVE - Superseded by `analyze_corrected_segments.py`

---

#### 7. analyze_engagement_friction.py
**Status:** ⚠️ NEEDS REVIEW
**Data Source:** Multiple (needs inspection)
**Purpose:** Identify friction points in customer journey

**Why Uncertain:** Need to verify if it uses check-ins prices or just behavioral metrics

**Action:** 🔍 INSPECT before use - May be safe if only uses counts

---

### 📋 NEEDS INSPECTION

#### 8. analyze_activation_journey.py
**Status:** 📋 NEEDS INSPECTION
**Purpose:** First-visit to active-user progression
**Action:** 🔍 Check if uses check-ins prices or just timestamps

---

#### 9. analyze_cohort_retention.py
**Status:** 📋 NEEDS INSPECTION
**Purpose:** Cohort-based retention analysis
**Action:** 🔍 Check if uses check-ins prices or just visit counts

---

#### 10. analyze_daypart_patterns.py
**Status:** 📋 NEEDS INSPECTION
**Purpose:** Time-of-day activity patterns
**Action:** 🔍 Likely safe (behavioral), verify no price usage

---

#### 11. analyze_event_fill_rates.py
**Status:** 📋 NEEDS INSPECTION
**Purpose:** Event capacity utilization
**Action:** 🔍 Check if uses check-ins for counting or pricing

---

#### 12. analyze_party_size_guests.py
**Status:** 📋 NEEDS INSPECTION
**Purpose:** Group size analysis
**Action:** 🔍 Likely safe (behavioral), verify no price usage

---

#### 13. analyze_rule_based_segments.py
**Status:** 📋 NEEDS INSPECTION
**Purpose:** Rule-based customer classification
**Action:** 🔍 Check segmentation criteria - prices vs behavior

---

### 🔧 UTILITY SCRIPTS

#### 14. db_loader.py
**Status:** 🔧 UTILITY - INFRASTRUCTURE
**Purpose:** Database connection and query helpers
**Action:** ✅ KEEP - Core infrastructure

---

#### 15. create_database.py
**Status:** 🔧 UTILITY - INFRASTRUCTURE
**Purpose:** Database schema creation
**Action:** ✅ KEEP - Core infrastructure

---

#### 16. query_database.py
**Status:** 🔧 UTILITY - INFRASTRUCTURE
**Purpose:** Ad-hoc query interface
**Action:** ✅ KEEP - Useful for exploration

---

#### 17. validate_data_import.py
**Status:** 🔧 UTILITY - VALIDATION
**Purpose:** Automated data quality checks
**Action:** ✅ KEEP - Run monthly after imports

---

#### 18. audit_full_event_bug.py
**Status:** 🔧 UTILITY - AUDIT TOOL
**Purpose:** Documented data quality issues
**Action:** ✅ KEEP - Historical record of findings

---

#### 19. regenerate_all_analysis.py
**Status:** 🔧 UTILITY - BATCH RUNNER
**Purpose:** Run multiple analyses in sequence
**Action:** 🔍 UPDATE - Should only run SAFE scripts

---

## Summary Statistics

**Total Scripts:** 19
- ✅ SAFE (verified correct): 5
- ⚠️ UNSAFE (uses check-ins prices): 1
- 📋 NEEDS INSPECTION: 7
- 🔧 UTILITY: 6

---

## Priority Actions

### IMMEDIATE (For Presentation)

1. **RE-RUN SAFE SCRIPTS:**
```bash
python3 scripts/analyze_shadow_market_heatmap.py
python3 scripts/analyze_transaction_details.py
python3 scripts/analyze_frequency_distribution.py
python3 scripts/analyze_corrected_segments.py
```

2. **VERIFY OUTPUTS:**
- `deliverables/data/*.csv` files are fresh
- `deliverables/visualizations/*.png` are current
- All outputs timestamped after October 30, 2025

### NEXT (Complete Audit)

3. **INSPECT UNCERTAIN SCRIPTS:**
```bash
# Check each for check-ins price usage:
grep -n "price_amount\|SUM.*price" scripts/analyze_activation_journey.py
grep -n "price_amount\|SUM.*price" scripts/analyze_cohort_retention.py
grep -n "price_amount\|SUM.*price" scripts/analyze_daypart_patterns.py
grep -n "price_amount\|SUM.*price" scripts/analyze_event_fill_rates.py
grep -n "price_amount\|SUM.*price" scripts/analyze_party_size_guests.py
grep -n "price_amount\|SUM.*price" scripts/analyze_rule_based_segments.py
grep -n "price_amount\|SUM.*price" scripts/analyze_engagement_friction.py
```

4. **UPDATE BATCH RUNNER:**
- Edit `regenerate_all_analysis.py` to only run SAFE scripts

---

## Data Source Reference

### ✅ SAFE Data Sources

**For Financial Analysis:**
- **transactions** table - ONLY reliable revenue source
  - 29,752 records
  - $634K total revenue
  - Complete member and non-member payments

**For Behavioral Analysis:**
- **checkins** table (COUNTS only, not prices)
  - 17,250 check-ins
  - 2,285 unique customers
  - Attendance patterns, registration types
  - ⚠️ Do NOT use `price_amount` field

**For Capacity Analysis:**
- **court_utilization** table
  - 6,060 hourly utilization records
  - 300 unique dates
  - Verified accurate for shadow market analysis

**For Customer Roster:**
- **members** table
  - 4,484 members
  - 4,342 currently active
  - Membership status, demographics

### ❌ UNSAFE Data Sources

**Do NOT Use for Revenue:**
- **checkins.price_amount** - Missing 99% of non-member revenue
- **checkins.paid_amount** - Incomplete
- **event_registrants.paid_amount** - May have duplication

---

## Output Manifest

### Current Verified Outputs

**From Shadow Market Analysis:**
- ✅ `deliverables/visualizations/shadow_market_heatmap.png`
- ✅ `deliverables/data/shadow_market_summary.json`

**From Corrected Segments:**
- ✅ `deliverables/data/corrected_ppu_customer_spending.csv`
- ✅ `deliverables/data/corrected_frequency_summary.csv`

**From Audit:**
- ✅ `docs/AUDIT_EXECUTIVE_SUMMARY.md`
- ✅ `docs/COMPREHENSIVE_AUDIT_REPORT.md`
- ✅ `docs/mark_tomlinson_spending_analysis.md`

### Outputs to Regenerate

**From Transaction Details:**
- ⏳ `deliverables/data/transaction_summary.csv`
- ⏳ `deliverables/visualizations/wtp_distribution.png`

**From Frequency Distribution:**
- ⏳ `deliverables/data/frequency_summary.csv`
- ⏳ `deliverables/data/dau_wau_mau.csv`

**From JTBD Analysis (if needed):**
- ⏳ `deliverables/data/behavioral_clusters.csv`
- ⏳ `deliverables/data/persona_profiles.json`

---

## Recommended Workflow

### Step 1: Clean Slate
```bash
# Archive old deliverables
mkdir -p archive/pre-audit-outputs-$(date +%Y%m%d)
cp -r deliverables/* archive/pre-audit-outputs-$(date +%Y%m%d)/
```

### Step 2: Validate Database
```bash
python3 scripts/validate_data_import.py
# Should show: ✓ ALL CHECKS PASSED
```

### Step 3: Regenerate Safe Outputs
```bash
# Shadow market (verified correct)
python3 scripts/analyze_shadow_market_heatmap.py

# Transaction-based revenue (source of truth)
python3 scripts/analyze_transaction_details.py

# Frequency patterns (counts, not prices)
python3 scripts/analyze_frequency_distribution.py

# Corrected segmentation (post-audit)
python3 scripts/analyze_corrected_segments.py
```

### Step 4: Verify Outputs
```bash
# Check timestamps
ls -lh deliverables/data/*.csv
ls -lh deliverables/visualizations/*.png

# Verify file sizes (should be non-zero)
find deliverables -name "*.csv" -size 0
```

### Step 5: Document for Claude
```bash
# Create output manifest for presentation architect
ls -R deliverables/ > deliverables/OUTPUT_MANIFEST.txt
```

---

## Notes for Claude (Presentation Architect)

**SAFE TO USE:**
- Shadow market metrics: 74.7% empty, $85K opportunity
- Transaction revenue: $634K total, 66.8% non-member
- Frequency patterns: 2,285 unique customers, 64.8 avg check-ins/day
- Corrected segments: 1,870 true PPU, 1,163 high-value targets

**DO NOT USE:**
- Any revenue figures from `analyze_pay_per_use_segment.py`
- Check-ins table `price_amount` for non-member revenue
- Old $439K conversion opportunity number

**PENDING REVIEW:**
- Persona profiles from JTBD analysis (may need refresh)
- Engagement friction analysis (verify data sources first)

---

**Document Status:** Complete - Ready for script re-runs
**Last Updated:** October 30, 2025
**Next Review:** After safe scripts regenerated
