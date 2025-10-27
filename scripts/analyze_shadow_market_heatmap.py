#!/usr/bin/env python3
"""
Shadow Market Heatmap Analysis
Analyzes CourtUtilization-by-date.csv to quantify weekday daytime empty capacity.

Purpose: Replace qualitative "ghost town" narrative with precise utilization percentages
Output: Heatmap visualization + quantified revenue opportunity
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import sys

def load_utilization_data(file_path):
    """Load and parse court utilization CSV."""
    print(f"Loading utilization data from {file_path}...")

    # Read CSV, skip metadata row
    df = pd.read_csv(file_path, skiprows=1)

    # First column is time slots
    df = df.rename(columns={df.columns[0]: 'time_slot'})

    # Remove "Total" column if it exists
    if 'Total' in df.columns:
        df = df.drop(columns=['Total'])

    print(f"Loaded {len(df)} time slots across {len(df.columns)-1} dates")
    return df

def parse_time_slot(time_slot_str):
    """
    Parse time slot string like '9:00 AM - 10:00 AM' to hour number.
    Returns start hour (0-23).
    """
    if not isinstance(time_slot_str, str):
        return None

    try:
        start_time = time_slot_str.split(' - ')[0].strip()
        hour_str, period = start_time.split(' ')
        hour = int(hour_str.split(':')[0])

        if period == 'PM' and hour != 12:
            hour += 12
        elif period == 'AM' and hour == 12:
            hour = 0

        return hour
    except:
        return None

def get_day_of_week(date_str):
    """Convert date string like '1/1/2025' to day of week (0=Monday, 6=Sunday)."""
    try:
        date_obj = datetime.strptime(date_str, '%m/%d/%Y')
        return date_obj.weekday()
    except:
        return None

def analyze_shadow_market(df):
    """
    Analyze weekday 9 AM - 4 PM utilization (the 'shadow market').

    Returns dictionary with:
    - Average utilization by hour and day-of-week
    - Lowest utilization windows
    - Revenue opportunity calculations
    """
    print("\nAnalyzing shadow market (weekday 9 AM - 4 PM)...")

    # Add hour column
    df['hour'] = df['time_slot'].apply(parse_time_slot)

    # Filter to 9 AM - 4 PM (hours 9-15)
    shadow_hours = df[df['hour'].between(9, 15)].copy()

    # Initialize results
    utilization_by_day_hour = {}
    all_values = []

    # Process each date column
    date_columns = [col for col in df.columns if col not in ['time_slot', 'hour']]

    for col in date_columns:
        day_of_week = get_day_of_week(col)

        # Skip weekends (5=Saturday, 6=Sunday)
        if day_of_week is None or day_of_week >= 5:
            continue

        # Get utilization values for this date
        for idx, row in shadow_hours.iterrows():
            hour = row['hour']
            value_str = row[col]

            # Parse percentage (handle formats like "15.3 %", "0 %")
            try:
                if pd.isna(value_str) or value_str == '':
                    utilization = 0.0
                else:
                    utilization = float(str(value_str).replace('%', '').replace(' ', '').strip())
            except:
                utilization = 0.0

            # Store by day-of-week and hour
            key = (day_of_week, hour)
            if key not in utilization_by_day_hour:
                utilization_by_day_hour[key] = []
            utilization_by_day_hour[key].append(utilization)
            all_values.append(utilization)

    # Calculate averages
    avg_utilization_by_day_hour = {}
    for key, values in utilization_by_day_hour.items():
        avg_utilization_by_day_hour[key] = np.mean(values)

    # Find lowest utilization windows
    sorted_windows = sorted(avg_utilization_by_day_hour.items(), key=lambda x: x[1])
    lowest_windows = sorted_windows[:10]

    # Calculate overall statistics
    overall_avg = np.mean(all_values)
    overall_median = np.median(all_values)

    # Calculate empty capacity
    # Assume 7 courts, 7 hours (9 AM - 4 PM), 5 weekdays
    total_weekly_capacity = 7 * 7 * 5  # 245 court-hours per week
    avg_empty_pct = (100 - overall_avg) / 100
    empty_court_hours = total_weekly_capacity * avg_empty_pct

    # Revenue calculation
    # Assume $30/court-hour average (mix of drop-ins, reservations, events)
    revenue_per_court_hour = 30

    # If we fill 30% of empty capacity
    fillable_capacity = empty_court_hours * 0.30
    weekly_revenue_opportunity = fillable_capacity * revenue_per_court_hour
    annual_revenue_opportunity = weekly_revenue_opportunity * 52

    results = {
        'avg_utilization_by_day_hour': avg_utilization_by_day_hour,
        'lowest_windows': lowest_windows,
        'overall_avg': overall_avg,
        'overall_median': overall_median,
        'empty_court_hours_per_week': empty_court_hours,
        'fillable_capacity_30pct': fillable_capacity,
        'weekly_revenue_opportunity': weekly_revenue_opportunity,
        'annual_revenue_opportunity': annual_revenue_opportunity
    }

    print(f"\nShadow Market Analysis Results:")
    print(f"  Average utilization: {overall_avg:.1f}%")
    print(f"  Median utilization: {overall_median:.1f}%")
    print(f"  Empty capacity: {empty_court_hours:.1f} court-hours/week ({avg_empty_pct*100:.1f}% empty)")
    print(f"  Fillable capacity (30%): {fillable_capacity:.1f} court-hours/week")
    print(f"  Revenue opportunity: ${weekly_revenue_opportunity:,.0f}/week (${annual_revenue_opportunity:,.0f}/year)")

    print(f"\n10 Lowest Utilization Windows (Day, Hour, Avg Utilization):")
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    for (day, hour), util in lowest_windows:
        print(f"  {day_names[day]}, {hour}:00-{hour+1}:00: {util:.1f}%")

    return results

def create_heatmap(results, output_path):
    """Create heatmap visualization of weekday daytime utilization."""
    print(f"\nCreating heatmap visualization...")

    # Prepare data for heatmap
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    hours = list(range(9, 16))  # 9 AM - 3 PM (last slot is 3-4 PM)

    # Create matrix
    matrix = np.zeros((len(hours), len(day_names)))

    for (day, hour), util in results['avg_utilization_by_day_hour'].items():
        if day < 5 and hour in hours:
            day_idx = day
            hour_idx = hours.index(hour)
            matrix[hour_idx, day_idx] = util

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    # Create heatmap
    sns.heatmap(matrix,
                annot=True,
                fmt='.1f',
                cmap='RdYlGn',
                vmin=0,
                vmax=100,
                xticklabels=day_names,
                yticklabels=[f"{h}:00-{h+1}:00" for h in hours],
                cbar_kws={'label': 'Utilization (%)'},
                ax=ax)

    ax.set_title('Shadow Market: Weekday Daytime Court Utilization\n(9 AM - 4 PM, Jan-Oct 2025)',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Day of Week', fontsize=12, fontweight='bold')
    ax.set_ylabel('Time Slot', fontsize=12, fontweight='bold')

    # Add summary text
    summary_text = (
        f"Average Utilization: {results['overall_avg']:.1f}%\n"
        f"Empty Capacity: {results['empty_court_hours_per_week']:.0f} court-hours/week\n"
        f"Revenue Opportunity (30% fill): ${results['annual_revenue_opportunity']:,.0f}/year"
    )

    ax.text(0.5, -0.15, summary_text,
            transform=ax.transAxes,
            ha='center',
            fontsize=10,
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Heatmap saved to {output_path}")

    return fig

def generate_narrative_insights(results):
    """Generate narrative-friendly insights for partner document."""
    print("\nGenerating narrative insights...")

    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    # Find absolute lowest window
    lowest = results['lowest_windows'][0]
    (lowest_day, lowest_hour), lowest_util = lowest

    insights = {
        'overall_avg': results['overall_avg'],
        'lowest_window': {
            'day': day_names[lowest_day],
            'hour': f"{lowest_hour}:00-{lowest_hour+1}:00",
            'utilization': lowest_util,
            'empty_pct': 100 - lowest_util
        },
        'empty_capacity_weekly': results['empty_court_hours_per_week'],
        'fillable_capacity': results['fillable_capacity_30pct'],
        'revenue_annual': results['annual_revenue_opportunity']
    }

    # Generate narrative text
    narrative = f"""
## Shadow Market Quantification (From CourtUtilization Analysis)

**Weekday Daytime Utilization (9 AM - 4 PM):**
- **Average utilization:** {insights['overall_avg']:.1f}% (meaning {100-insights['overall_avg']:.1f}% sits empty)
- **Lowest utilization window:** {insights['lowest_window']['day']} {insights['lowest_window']['hour']} at {insights['lowest_window']['utilization']:.1f}% ({insights['lowest_window']['empty_pct']:.1f}% empty capacity)
- **Total empty capacity:** {insights['empty_capacity_weekly']:.1f} court-hours per week

**Revenue Opportunity:**
If we fill just 30% of this empty weekday daytime capacity:
- **Fillable capacity:** {insights['fillable_capacity']:.1f} additional court-hours/week
- **Annual revenue:** ${insights['revenue_annual']:,.0f}/year

This is PURE UPSIDE—these hours currently generate $0. No cannibalization of current member prime time.

**Strategic Implication:** The "shadow market" (weekday daytime) is not a weakness—it's unutilized inventory waiting for the right customer segments (retirees, WFH professionals, stay-at-home parents, shift workers).
"""

    print(narrative)
    return insights, narrative

def main():
    """Main execution function."""
    # File paths
    input_file = 'CourtUtilization-by-date.csv'
    heatmap_output = 'shadow_market_heatmap.png'
    insights_output = 'shadow_market_insights.txt'

    try:
        # Load data
        df = load_utilization_data(input_file)

        # Analyze shadow market
        results = analyze_shadow_market(df)

        # Create heatmap
        create_heatmap(results, heatmap_output)

        # Generate narrative insights
        insights, narrative = generate_narrative_insights(results)

        # Save insights to file
        with open(insights_output, 'w') as f:
            f.write(narrative)
        print(f"\nNarrative insights saved to {insights_output}")

        print("\n✅ Shadow market analysis complete!")
        print(f"   - Heatmap: {heatmap_output}")
        print(f"   - Insights: {insights_output}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
