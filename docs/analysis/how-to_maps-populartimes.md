# Maps-PopularTimes Heatmap Implementation Guide

**Project**: PCC Yield Optimizer - Competitive Intelligence Module
**Repository**: `maps-populartimes` (separate repo)
**Purpose**: Generate Google Maps popular times heatmaps for competitive analysis
**Last Updated**: October 27, 2025

---

## Overview

This document explains how we use the **Google Maps Popular Times API** (via the `populartimes` Python library) to generate competitive intelligence heatmaps for Chicago-area pickleball facilities. The system fetches hourly crowd data (0-100 popularity scores) for PCC (Pickleball Clubhouse Chicago) and competitor facilities, enabling strategic scheduling and competitive analysis.

**Key Capability**: Identify time slots where competitors are busy/empty to inform programming decisions and find market opportunities.

---

## Architecture

### Technology Stack

- **Python 3.11+** with virtual environment
- **populartimes library** (GitHub: m-wrzr/populartimes) - unofficial Google Maps scraper
- **Google Maps Places API** - requires API key (free tier: 5,000 requests/month)
- **Visualization**: matplotlib, seaborn, pandas
- **Data Format**: JSON for facility lists and output data

### Data Pipeline Flow

```
1. Facility Address List (JSON)
   ├─> addresses_full.json (50+ facilities)
   └─> addresses_test.json (smaller test set)

2. Geocoding (converts addresses → lat/lng + place_id)
   ├─> Script: geocode_addresses.py
   └─> Output: geocoded_test.json, geocoded_full.json

3. Popular Times Fetching (API calls to Google Maps)
   ├─> Script: batch_popular_times.py
   └─> Output: facilities_final.json (enriched with populartimes data)

4. Visualization (heatmaps, line charts, dashboards)
   ├─> visualizer.py (library)
   └─> chicago_lookup.py (CLI tool)
```

---

## Key Files in maps-populartimes Repository

### 1. **Competitor Facility Configuration**

**File**: `addresses_full.json` (primary facility list)
**Location**: `/Users/petergiordano/Documents/GitHub/maps-populartimes/addresses_full.json`

**Format**:
```json
[
  {
    "name": "Facility Name",
    "address": "123 Main St, Chicago, IL 60618",
    "type": "public|private",
    "location": "City of Chicago|Suburban"
  }
]
```

**Key Facilities Currently Tracked**:
- **PCC (Pickleball Clubhouse)**: 4242 N Elston Ave, Chicago, IL 60618 *(YOUR facility - baseline)*
- **Grant Park Pickleball Courts**: 1000 S Columbus Dr *(downtown public courts)*
- **SPF Chicago**: 2121 N Clybourn Ave *(closest private competitor, 3 miles)*
- **Big City Pickle - Fulton Market**: 170 N Green St *(Fulton Market competitor)*
- **Slate Pickleball Club**: 569 S Waukegan Rd, Northbrook *(suburban premium)*
- **Horner Park**: 2741 W Montrose Ave *(public park with courts)*
- **Union Park**: 1501 W Randolph St *(public park)*
- **Lovelace Park**: Evanston *(suburban public)*

**How to Add New Competitors**:
1. Add new entry to `addresses_full.json`
2. Run geocoding: `python geocode_addresses.py addresses_full.json geocoded_full.json`
3. Fetch popular times: `python batch_popular_times.py geocoded_full.json facilities_final.json`

---

### 2. **Popular Times Data Fetcher**

**File**: `batch_popular_times.py`
**Purpose**: Batch fetch Google Maps popular times data for all facilities

**Key Functions**:
```python
def fetch_popular_times(facility, api_key):
    """
    Fetch popular times data for a single facility.

    Tries Place ID first (most reliable), falls back to coordinates.
    Returns dict with populartimes, rating, current_popularity.
    """

def process_facilities(input_file, output_file, delay=0.5):
    """
    Process all facilities from input JSON and fetch popular times data.

    Args:
        input_file: Path to geocoded JSON file
        output_file: Path to output JSON file with popular times data
        delay: Delay between API calls in seconds (default 0.5s)
    """
```

**Usage Examples**:
```bash
# Test run (small dataset)
python batch_popular_times.py geocoded_test.json facilities_test.json

# Full production run
python batch_popular_times.py geocoded_full.json facilities_final.json

# Slower rate limiting (safer for API limits)
python batch_popular_times.py geocoded_full.json facilities_final.json --delay 1.0
```

**API Rate Limiting**:
- Default: 0.5 seconds between requests
- Google Maps API free tier: 5,000 requests/month
- Each facility = 1 API call
- 50 facilities ≈ 25 seconds with default delay

**Success Metrics from Latest Run**:
- Total facilities: 8 tracked
- ✅ With popular times data: 8/8 (100%)
- Current popularity available: 7/8 facilities
- Data freshness: Fetched October 5, 2025

---

### 3. **Output Data Structure**

**File**: `facilities_final.json`
**Location**: `/Users/petergiordano/Documents/GitHub/maps-populartimes/facilities_final.json`

**Complete Example**:
```json
[
  {
    "id": "facility-1",
    "name": "Grant Park Pickleball Courts",
    "address": "1000 S Columbus Dr, Chicago, IL 60605, United States",
    "formatted_address": "1000 S Columbus Dr, Chicago, IL 60605, USA",
    "type": "public",
    "lat": 41.8713522,
    "lng": -87.621184,
    "place_id": "ChIJIxGjPTktDogRM5yhmstLT7g",
    "rating": 4.4,
    "rating_n": 31,
    "current_popularity": 70,
    "time_spent": [180, 180],
    "populartimes": [
      {
        "name": "Monday",
        "data": [0, 0, 0, 0, 0, 0, 12, 17, 12, 17, 18, 32, 34, 31, 29, 39, 53, 55, 67, 53, 62, 56, 56, 0]
      },
      {
        "name": "Tuesday",
        "data": [0, 0, 0, 0, 0, 0, 44, 41, 41, 48, 50, 44, 37, 44, 53, 68, 58, 55, 50, 62, 56, 56, 50, 0]
      },
      // ... 7 days total (Monday-Sunday)
    ],
    "fetched_at": "2025-10-05T17:29:35.416342Z",
    "has_popular_times": true
  }
]
```

**Field Descriptions**:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique facility identifier (e.g., "facility-1") |
| `name` | string | Facility name |
| `address` | string | Full street address |
| `formatted_address` | string | Google Maps formatted address |
| `type` | string | "public" or "private" |
| `lat` | float | Latitude coordinate |
| `lng` | float | Longitude coordinate |
| `place_id` | string | Google Maps Place ID (unique identifier) |
| `rating` | float | Google Maps rating (1.0-5.0) |
| `rating_n` | int | Number of reviews |
| `current_popularity` | int\|null | **Real-time** current busyness (0-100), often null |
| `time_spent` | array\|null | [min, max] typical visit duration in minutes |
| `populartimes` | array | **7-day array of hourly traffic patterns** (see below) |
| `fetched_at` | string | ISO 8601 timestamp of data fetch |
| `has_popular_times` | boolean | Whether this facility has historical traffic data |

**PopularTimes Array Structure**:
```json
{
  "name": "Monday",  // Day name
  "data": [0, 0, 0, 0, 0, 0, 12, 17, ..., 0]  // 24 hours (0-100 scale)
}
```

**Data Interpretation**:
- **Index**: `populartimes[day].data[hour]`
  - Days: 0=Monday, 1=Tuesday, ..., 6=Sunday
  - Hours: 0=midnight, 1=1am, ..., 23=11pm
- **Values**: 0-100 popularity score
  - `0`: Closed or no data
  - `1-30`: Low traffic
  - `31-60`: Moderate traffic
  - `61-85`: Busy
  - `86-100`: Peak busy (relative to that location's max)
- **Scores are relative**: 100 = busiest time *for that specific location*, not absolute capacity

**Example Data Query**:
```python
# Get Grant Park's Saturday 10am traffic
facility = facilities[0]  # Grant Park
saturday_data = facility['populartimes'][5]  # Saturday = index 5
traffic_at_10am = saturday_data['data'][10]  # 10am = index 10
print(f"Traffic: {traffic_at_10am}")  # Output: 50
```

---

### 4. **Visualization Module**

**File**: `visualizer.py`
**Purpose**: Generate matplotlib heatmaps and charts from popular times data

**Key Functions**:

```python
def create_heatmap(place, days_range=None, save_path=None):
    """
    Create a heatmap showing popular times across the week.

    Args:
        place: Place data from facilities_final.json
        days_range: Tuple of (start_day, end_day) where 0=Monday, 6=Sunday
                   None means show all days
        save_path: Optional path to save the figure (PNG)

    Returns:
        matplotlib figure object
    """

def create_line_chart(place, days_range=None, save_path=None):
    """Create line graphs comparing different days of the week."""

def create_dashboard(place, days_range=None, save_path=None):
    """Comprehensive view: heatmap + weekday/weekend comparison + peak hours."""

def create_comparison(places, day=None, hour_range=None, save_path=None):
    """Bar chart comparing multiple facilities at specific times."""
```

**Visualization Types**:
1. **Heatmap**: 7 days × 24 hours color-coded grid (YlOrRd colormap)
2. **Line Chart**: Hourly traffic curves for each day overlaid
3. **Dashboard**: Multi-panel view with heatmap, comparisons, and statistics
4. **Comparison**: Side-by-side bar chart of multiple facilities

**Example Usage**:
```python
import json
from visualizer import create_heatmap

# Load data
with open('facilities_final.json', 'r') as f:
    facilities = json.load(f)

# Generate heatmap for PCC
pcc = facilities[4]  # Pickleball Clubhouse
create_heatmap(pcc, save_path='pcc_heatmap.png')

# Generate weekday-only heatmap
create_heatmap(pcc, days_range=(0, 4), save_path='pcc_weekdays.png')
```

---

## Setup Instructions for Another Developer

### 1. Environment Setup

```bash
# Clone or create project directory
cd /path/to/new-project
mkdir maps-populartimes
cd maps-populartimes

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Dependencies

**File**: `requirements.txt`
```
git+https://github.com/m-wrzr/populartimes.git
python-dotenv
matplotlib
pandas
seaborn
```

**Installation**:
```bash
pip install -r requirements.txt
```

### 3. Google Maps API Key Setup

**Step 1: Get API Key**
1. Go to https://developers.google.com/maps
2. Create a project in Google Cloud Console
3. Enable **Places API**
4. Create credentials → API key
5. (Optional) Restrict key to Places API only

**Step 2: Configure Environment**
```bash
# Create .env file
cat > .env << EOF
GOOGLE_MAPS_API_KEY=your_actual_api_key_here
EOF

# Add .env to .gitignore
echo ".env" >> .gitignore
```

**Important**: Keep API key secret, never commit to git

### 4. Create Facility List

**File**: `your_facilities.json`
```json
[
  {
    "name": "Your Main Facility",
    "address": "123 Main St, City, ST 12345",
    "type": "private",
    "location": "Primary Market"
  },
  {
    "name": "Competitor A",
    "address": "456 Oak Ave, City, ST 12345",
    "type": "private",
    "location": "Direct Competitor"
  },
  {
    "name": "Public Courts Nearby",
    "address": "789 Park Rd, City, ST 12345",
    "type": "public",
    "location": "Substitute Competition"
  }
]
```

**Competitor Selection Strategy** (based on PCC implementation):
- **Direct Competitors**: Private clubs within 5 miles
- **Substitutes**: Public parks with pickleball courts
- **Aspirational**: High-rated premium facilities
- **Geographic Coverage**: Cover all relevant market areas

### 5. Run Data Pipeline

```bash
# Step 1: Geocode addresses (get lat/lng + place_id)
python geocode_addresses.py your_facilities.json geocoded_facilities.json

# Step 2: Fetch popular times data (will take ~30 seconds for 50 facilities)
python batch_popular_times.py geocoded_facilities.json facilities_with_data.json

# Step 3: Verify output
cat facilities_with_data.json | jq '.[0]'  # View first facility

# Step 4: Generate test visualization (optional)
python chicago_lookup.py --place-id ChIJe3YgG8XND4gRyeiM-KHzKj8 --viz dashboard
```

---

## Integration with Frontend

The React frontend (`/frontend` directory in main repo) consumes `facilities_final.json`:

### Frontend Data Flow

```
1. Build Time
   ├─> Load facilities_final.json as static asset
   └─> Parse populartimes arrays

2. Runtime
   ├─> Transform data for Recharts/D3.js
   ├─> Render comparison grid with mini heatmaps
   └─> Modal view for detailed facility analysis
```

### Sample Frontend Code (TypeScript)

```typescript
// Type definitions
interface PopularTimesDay {
  name: string;
  data: number[];  // 24 hours
}

interface Facility {
  id: string;
  name: string;
  type: 'public' | 'private';
  lat: number;
  lng: number;
  rating: number;
  rating_n: number;
  current_popularity: number | null;
  populartimes: PopularTimesDay[];
  has_popular_times: boolean;
}

// Load data
import facilitiesData from './data/facilities_final.json';
const facilities: Facility[] = facilitiesData;

// Transform for heatmap (flatten to x/y/value format)
const transformForHeatmap = (facility: Facility) => {
  return facility.populartimes.flatMap((day, dayIdx) =>
    day.data.map((popularity, hour) => ({
      day: dayIdx,        // 0=Monday, 6=Sunday
      hour: hour,         // 0=midnight, 23=11pm
      value: popularity,  // 0-100
      dayName: day.name,
      hourLabel: `${hour}:00`
    }))
  );
};

// Get peak hours for a facility
const getPeakHours = (facility: Facility) => {
  const allHours = facility.populartimes.flatMap((day, dayIdx) =>
    day.data.map((value, hour) => ({ dayIdx, hour, value }))
  );

  return allHours
    .sort((a, b) => b.value - a.value)
    .slice(0, 5);  // Top 5 busiest hours
};

// Compare facilities at specific time
const compareAtTime = (facilities: Facility[], dayIdx: number, hour: number) => {
  return facilities.map(f => ({
    name: f.name,
    popularity: f.populartimes[dayIdx]?.data[hour] || 0
  }));
};
```

---

## Competitive Intelligence Use Cases

### 1. **Opportunity Gap Analysis**

**Goal**: Find time slots where competitors are empty but market has demand

**Method**:
```python
# Pseudo-code
for hour in range(24):
    for day in range(7):
        competitor_avg = avg([f.populartimes[day].data[hour] for f in competitors])
        pcc_traffic = pcc.populartimes[day].data[hour]

        if competitor_avg > 60 and pcc_traffic < 40:
            print(f"Opportunity: {day_names[day]} {hour}:00 - competitors busy, PCC low")
```

**Real Example from PCC Data**:
- **Wednesday 2-6pm**: Grant Park 50-65%, SPF 57-81%, PCC only 22-52%
  - **Insight**: Mid-afternoon weekday demand exists
  - **Action**: Launch "Ladies League" Wednesday 2-4pm
  - **Expected Impact**: +$800/week revenue

### 2. **Peak Avoidance Scheduling**

**Goal**: Avoid competing directly with saturated time slots

**Method**:
- Identify when ALL competitors are at 90%+ capacity
- Schedule special events during competitor off-peak times
- Capture underserved demand segments

**Real Example from PCC Data**:
- **Saturday 10am-1pm**: Horner Park 96-100%, SPF 75-87%, Grant Park 50-65%
- **PCC Pattern**: 40-64% during same time
- **Action**: Market Saturday morning tournaments to families (public parks full)

### 3. **Benchmarking & Market Position**

**Goal**: Understand PCC's competitive standing

**Method**:
```python
# Calculate market share by time slot
def market_share(facilities, day, hour):
    total_traffic = sum(f.populartimes[day].data[hour] for f in facilities)
    return {f.name: (f.populartimes[day].data[hour] / total_traffic) * 100
            for f in facilities}

# Find PCC's strengths
pcc_dominant_hours = []
for day in range(7):
    for hour in range(24):
        share = market_share(facilities, day, hour)
        if share['Pickleball Clubhouse'] > 30:  # PCC has >30% market share
            pcc_dominant_hours.append((day, hour))
```

**Real Insights from PCC Data**:
- **Strengths**: Weeknight evenings 6-9pm (PCC 67-100%, competitors 50-85%)
- **Weaknesses**: Weekend mornings (PCC 33-66%, public parks 70-100%)
- **Rating Advantage**: PCC 4.9/5 (72 reviews) vs SPF 4.5/5 (131 reviews)

---

## Key Implementation Insights

### 1. **Rate Limiting is Critical**

- Google doesn't officially support popular times API
- Use `--delay 0.5` minimum (default in `batch_popular_times.py`)
- Increase to 1.0 seconds for large batches (100+ facilities)
- Monitor API quota in Google Cloud Console
- Free tier resets monthly (5,000 requests)

### 2. **Data Freshness**

- **Popular times** = **historical patterns** (aggregated over weeks/months)
- **`current_popularity`** = **live data** (snapshot at fetch time, often null)
- **Recommendation**: Refetch data monthly to capture seasonal changes
- **Best Practice**: Version output files with timestamps

### 3. **Place ID vs Coordinates**

**Place ID** (preferred method):
- Unique identifier for each Google Maps location
- Most reliable, never returns wrong place
- Example: `ChIJe3YgG8XND4gRyeiM-KHzKj8`
- How to find: Google Maps → Right-click location → "What's here?" → Copy from URL

**Coordinates** (fallback method):
- Searches nearby area (50m radius default)
- May return wrong place if multiple businesses at same address
- Use only when Place ID unavailable

**Best Practice**: Always run `geocode_addresses.py` first to get Place IDs

### 4. **Missing Data Handling**

**Not all locations have popular times data**:
- New places (< 6 months old)
- Low traffic locations (Google doesn't collect data)
- Private facilities with limited Google Maps presence

**Check before using**:
```python
if facility['has_popular_times']:
    # Safe to use populartimes data
    heatmap = generate_heatmap(facility)
else:
    # Display "No data available" message
    print(f"{facility['name']}: No popular times data")
```

**Current PCC Results**: 8/8 facilities have data (100% success rate)

### 5. **Competitor Selection Strategy**

Based on PCC's Chicago market implementation:

**Direct Competitors** (within 5 miles):
- SPF Chicago (3 miles) - private club, similar model
- Big City Pickle (5 miles) - Fulton Market, younger demographic

**Substitute Competition**:
- Grant Park, Horner Park, Union Park - free public courts
- Different customer segment but competes for casual players

**Aspirational Benchmarks**:
- Slate Pickleball Club (Northbrook) - premium suburban, 5.0 rating
- Higher price point, different market, but useful for quality benchmarking

**Geographic Coverage**:
- North Side: Horner Park, Lovelace Park
- Downtown: Grant Park, Union Park, Big City Pickle
- Suburban: Slate (Northbrook)

---

## Troubleshooting

### Common Issues

#### 1. "No popular times data available"

**Symptoms**: `has_popular_times: false` in output

**Causes**:
- Place is new/unlisted in Google Maps
- Very low traffic (Google doesn't collect data)
- Place ID incorrect or expired

**Solutions**:
- Try coordinates search instead of Place ID
- Manually verify place exists on Google Maps
- Exclude from analysis if consistently fails
- Check if address is accurate (use Google Maps autocomplete)

#### 2. API Rate Limit Exceeded

**Symptoms**: `429 Too Many Requests` error

**Causes**:
- Free tier limit: 5,000 requests/month exceeded
- Too many requests per second

**Solutions**:
- Increase `--delay` parameter: `python batch_popular_times.py ... --delay 1.0`
- Batch process facilities weekly instead of daily
- Check Google Cloud Console quota dashboard
- Consider upgrading to paid tier if needed (unlikely for 50 facilities)

#### 3. Geocoding Returns Wrong Place

**Symptoms**: Wrong facility name or location in output

**Causes**:
- Address is ambiguous (e.g., "Park St" without city)
- Multiple businesses at same address

**Solutions**:
- Add full address with city, state, zip: "123 Main St, Chicago, IL 60618"
- Manually find Place ID on Google Maps:
  1. Search facility on maps.google.com
  2. Right-click on map pin
  3. Click "Share" → Copy URL
  4. Extract Place ID from URL: `...?q=place_id:ChIJ...`
- Add `place_id` directly to `addresses_full.json`

#### 4. Virtual Environment Issues

**Mac/Linux**:
```bash
source venv/bin/activate
```

**Windows**:
```bash
venv\Scripts\activate
```

**Verify activation**:
```bash
which python  # Should show venv/bin/python
```

#### 5. Missing Dependencies

**Symptoms**: `ModuleNotFoundError: No module named 'populartimes'`

**Solution**:
```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep populartimes
```

---

## Files Quick Reference

| File Path | Purpose | Input | Output |
|-----------|---------|-------|--------|
| `addresses_full.json` | Master competitor list | Manual curation | Facility addresses |
| `addresses_test.json` | Small test dataset | Manual subset | Test addresses |
| `geocode_addresses.py` | Convert addresses to coordinates | `addresses_*.json` | `geocoded_*.json` |
| `geocoded_full.json` | Geocoded facility data | Output from geocoder | lat/lng + place_id |
| `batch_popular_times.py` | Fetch popular times from API | `geocoded_*.json` | `facilities_*.json` |
| `facilities_final.json` | **Final output with heatmap data** | Output from fetcher | **Complete dataset** |
| `visualizer.py` | Heatmap generation library | `facilities_*.json` | PNG images |
| `chicago_lookup.py` | CLI tool for single facility | Place ID / coordinates | Terminal + PNG |
| `requirements.txt` | Python dependencies | - | - |
| `.env` | API key storage (gitignored) | Manual setup | - |

---

## Performance Metrics

**Current PCC Implementation** (as of Oct 5, 2025):

| Metric | Value |
|--------|-------|
| Total Facilities Tracked | 8 |
| Success Rate | 100% (8/8 with popular times) |
| API Calls Per Run | 8 |
| Time Per Run | ~4 seconds (0.5s delay) |
| Data Freshness | Monthly refresh recommended |
| API Key Cost | $0 (free tier sufficient) |
| Monthly API Usage | ~8 calls/month (manual runs) |

**Scalability**:
- 50 facilities: ~25 seconds
- 100 facilities: ~50 seconds
- 500 facilities: ~4 minutes
- Free tier limit: 5,000 requests/month = up to 5,000 facilities/month

---

## Next Steps for New Project Implementation

### Phase 1: Setup (1 hour)
1. ✅ Clone repository structure
2. ✅ Install Python dependencies
3. ✅ Get Google Maps API key
4. ✅ Configure `.env` file

### Phase 2: Data Collection (2 hours)
5. ✅ Research competitors in your market (10-20 facilities)
6. ✅ Create `addresses.json` with competitor list
7. ✅ Run geocoding script
8. ✅ Verify geocoding accuracy (check lat/lng on Google Maps)

### Phase 3: Data Fetching (30 minutes)
9. ✅ Run `batch_popular_times.py`
10. ✅ Verify output data quality
11. ✅ Check for missing/failed facilities

### Phase 4: Integration (4 hours)
12. ✅ Copy `facilities_final.json` to frontend project
13. ✅ Build React components to consume data
14. ✅ Implement heatmap visualization (Recharts or D3.js)
15. ✅ Add comparison grid view

### Phase 5: Automation (2 hours)
16. ✅ Set up monthly cron job to refresh data
17. ✅ Add data versioning (timestamp output files)
18. ✅ Create monitoring for API quota usage

---

## Additional Resources

**External Documentation**:
- **populartimes Library**: https://github.com/m-wrzr/populartimes
- **Google Places API Docs**: https://developers.google.com/maps/documentation/places/web-service
- **Google Cloud Console**: https://console.cloud.google.com

**PCC Project Documentation**:
- **Frontend Implementation**: `/frontend` directory (React + Recharts)
- **Competitive Intelligence Report**: `docs/PRD/PRD_Customer_Intelligence/COMPETITIVE_INTELLIGENCE_REPORT.md`
- **Technical Spec**: `docs/PRD/PRD_Customer_Intelligence/TECHNICAL_SPEC_Customer_Intelligence.md`

**maps-populartimes Repository**:
- **Location**: `/Users/petergiordano/Documents/GitHub/maps-populartimes/`
- **README**: Detailed CLI usage examples
- **Example Output**: `facilities_final.json` (8 Chicago facilities)

---

## Questions & Support

**Common Questions**:

**Q: How often should I refresh the data?**
A: Monthly is sufficient. Popular times are historical patterns, not real-time data. Seasonal changes (summer vs winter) may require more frequent updates.

**Q: Can I track more than 50 facilities?**
A: Yes, free tier supports 5,000/month. Practical limit is API rate limiting (use `--delay 1.0` for 100+ facilities).

**Q: What if a competitor doesn't have data?**
A: Check `has_popular_times` field. Display "No data available" in UI. Try adding their Place ID manually.

**Q: How accurate is this data?**
A: Google aggregates data from Android location services. Accuracy varies by location traffic. Higher-traffic locations = more accurate. Data represents patterns, not exact visitor counts.

**Q: Can I get real-time data?**
A: `current_popularity` field provides snapshot at fetch time, but often null. Not reliable for real-time monitoring. Use historical patterns for strategic planning.

**For Implementation Help**:
- Check `batch_popular_times.py` source code (fully commented)
- Review `visualizer.py` for heatmap generation examples
- Examine `facilities_final.json` for output format

---

**Document Status**: ✅ Complete
**Last Reviewed**: October 27, 2025
**Maintainer**: PCC Development Team
