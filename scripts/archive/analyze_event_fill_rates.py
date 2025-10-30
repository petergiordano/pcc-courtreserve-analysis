#!/usr/bin/env python3
"""
Event Fill Rate Analysis
Analyzes how well events fill up by category, time-of-day, and identifies optimization opportunities.

Purpose: Quantify event performance and identify underperforming programming
Output: Fill rate visualization + recommendations for event optimization

Author: Claude Code (Anthropic)
Date: October 27, 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))
from db_loader import CourtReserveDB


def load_event_data():
    """
    Load event registrant and summary data from database.

    Returns:
        tuple: (registrants_df, summary_df)
    """
    print("Loading event data from database...")

    with CourtReserveDB() as db:
        registrants = db.get_event_registrants()
        summary = db.get_event_summary()

    print(f"  Loaded {len(registrants)} event registrant records")
    print(f"  Loaded {len(summary)} event summary records")

    return registrants, summary


def calculate_fill_rates(registrants, summary):
    """
    Calculate popularity metrics for events based on registrant counts.

    Args:
        registrants: DataFrame with event registrant records
        summary: DataFrame with event summary records (not used - no capacity data)

    Returns:
        DataFrame: Event popularity analysis
    """
    print("\nCalculating event popularity metrics...")

    # Count registrants per event + date combination (to get average attendance)
    if 'event_date' in registrants.columns:
        event_instances = registrants.groupby(['event_name', 'event_date']).size().reset_index(name='attendance')

        # Calculate average attendance per event type
        fill_data = event_instances.groupby('event_name').agg({
            'attendance': ['mean', 'median', 'max', 'min', 'count']
        }).round(1)

        # Flatten column names
        fill_data.columns = ['avg_attendance', 'median_attendance', 'max_attendance', 'min_attendance', 'occurrences']
        fill_data = fill_data.reset_index()

        # Calculate total registrants per event type
        total_registrants = registrants.groupby('event_name').size().reset_index(name='total_registrants')
        fill_data = fill_data.merge(total_registrants, on='event_name')

    else:
        # If no date data, just count total registrants
        fill_data = registrants.groupby('event_name').size().reset_index(name='total_registrants')
        fill_data['avg_attendance'] = None
        fill_data['occurrences'] = None

    print(f"  Analyzed {len(fill_data)} unique event types")
    return fill_data


def categorize_events(fill_data, registrants):
    """
    Categorize events by type (Open Play, Drills, Lessons, Tournaments, etc.).

    Args:
        fill_data: DataFrame with fill rate data
        registrants: DataFrame with registrant records (for additional context)

    Returns:
        DataFrame: Fill data with event category column
    """
    print("\nCategorizing events...")

    def assign_category(event_name):
        """Assign category based on event name keywords."""
        event_lower = str(event_name).lower()

        if 'open play' in event_lower or 'drop-in' in event_lower:
            return 'Open Play'
        elif 'drill' in event_lower or 'skill' in event_lower:
            return 'Drills/Skills'
        elif 'lesson' in event_lower or 'clinic' in event_lower:
            return 'Lessons/Clinics'
        elif 'tournament' in event_lower or 'league' in event_lower:
            return 'Competitive'
        elif 'beginner' in event_lower:
            return 'Beginner Programs'
        elif 'social' in event_lower or 'mixer' in event_lower:
            return 'Social Events'
        else:
            return 'Other'

    fill_data['category'] = fill_data['event_name'].apply(assign_category)

    # Count events per category
    category_counts = fill_data['category'].value_counts()
    print("\nEvents by Category:")
    for cat, count in category_counts.items():
        print(f"  {cat:20s}: {count:4} events")

    return fill_data


def analyze_fill_rates_by_category(fill_data):
    """
    Analyze event popularity by category.

    Args:
        fill_data: DataFrame with popularity and category data

    Returns:
        dict: Summary statistics by category
    """
    print("\nAnalyzing event popularity by category...")

    # Filter to events with valid attendance data
    if 'avg_attendance' in fill_data.columns:
        valid_fill_data = fill_data[fill_data['avg_attendance'].notna()].copy()
    else:
        valid_fill_data = fill_data.copy()

    if len(valid_fill_data) == 0:
        print("Warning: No valid event data found")
        return {}

    # Calculate stats by category
    agg_dict = {'total_registrants': ['sum', 'mean']}
    if 'avg_attendance' in valid_fill_data.columns:
        agg_dict['avg_attendance'] = ['mean', 'median']
        agg_dict['occurrences'] = 'sum'

    category_stats = valid_fill_data.groupby('category').agg(agg_dict).round(1)

    print("\nEvent Popularity Statistics by Category:")
    print(category_stats.to_string())

    # Identify low-performing events (below median attendance or total registrants)
    if 'avg_attendance' in valid_fill_data.columns:
        median_attendance = valid_fill_data['avg_attendance'].median()
        underperforming = valid_fill_data[valid_fill_data['avg_attendance'] < median_attendance * 0.5].copy()
        underperforming = underperforming.sort_values('avg_attendance')
        metric_name = 'avg_attendance'
    else:
        median_registrants = valid_fill_data['total_registrants'].median()
        underperforming = valid_fill_data[valid_fill_data['total_registrants'] < median_registrants * 0.5].copy()
        underperforming = underperforming.sort_values('total_registrants')
        metric_name = 'total_registrants'

    print(f"\n⚠️  Low-Performing Events (bottom 50%): {len(underperforming)}")
    if len(underperforming) > 0:
        print("\nTop 10 Lowest Performing Events:")
        cols = ['event_name', 'category', metric_name, 'total_registrants']
        if 'occurrences' in underperforming.columns:
            cols.append('occurrences')
        print(underperforming[cols].head(10).to_string(index=False))

    # Convert category_stats to JSON-serializable format
    category_stats_dict = {}
    for col in category_stats.columns:
        # Convert column tuple to string (e.g., ('total_registrants', 'sum') -> 'total_registrants_sum')
        col_str = '_'.join(map(str, col)) if isinstance(col, tuple) else str(col)
        category_stats_dict[col_str] = category_stats[col].to_dict()

    results = {
        'category_stats': category_stats_dict,
        'underperforming_events': underperforming[['event_name', 'category', metric_name]].head(20).to_dict('records'),
        'total_registrants': int(valid_fill_data['total_registrants'].sum()),
        'avg_attendance': float(valid_fill_data['avg_attendance'].mean()) if 'avg_attendance' in valid_fill_data.columns else None
    }

    return results


def create_fill_rate_visualization(fill_data, results, output_path):
    """
    Create visualization of event fill rates.

    Args:
        fill_data: DataFrame with fill rate data
        results: Analysis results dictionary
        output_path: Path to save visualization PNG
    """
    print("\nCreating fill rate visualization...")

    # Use attendance or total registrants as metric
    if 'avg_attendance' in fill_data.columns:
        metric = 'avg_attendance'
        metric_label = 'Average Attendance'
        valid_fill_data = fill_data[fill_data[metric].notna()].copy()
    else:
        metric = 'total_registrants'
        metric_label = 'Total Registrants'
        valid_fill_data = fill_data.copy()

    if len(valid_fill_data) == 0:
        print("Warning: No valid event data to visualize")
        return

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # Chart 1: Average metric by category (bar chart)
    category_avg = valid_fill_data.groupby('category')[metric].mean().sort_values(ascending=False)
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(category_avg)))

    ax1.barh(category_avg.index, category_avg.values, color=colors, edgecolor='black', linewidth=1)
    ax1.set_xlabel(metric_label, fontsize=12)
    ax1.set_title(f'{metric_label} by Event Category', fontsize=14, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)

    # Add value labels
    for i, (cat, val) in enumerate(category_avg.items()):
        ax1.text(val + max(category_avg) * 0.02, i, f'{val:.1f}', va='center', fontsize=10, fontweight='bold')

    # Chart 2: Distribution (histogram)
    ax2.hist(valid_fill_data[metric], bins=20, color='steelblue', edgecolor='black', alpha=0.7)
    ax2.set_xlabel(metric_label, fontsize=12)
    ax2.set_ylabel('Number of Events', fontsize=12)
    ax2.set_title(f'Distribution of {metric_label}', fontsize=14, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)

    # Chart 3: Top 10 best-performing events
    top_10 = valid_fill_data.nlargest(10, metric)[['event_name', metric, 'category']]
    top_10_names = [name[:30] + '...' if len(name) > 30 else name for name in top_10['event_name']]

    colors_top = plt.cm.Greens([0.9] * len(top_10))
    ax3.barh(range(len(top_10)), top_10[metric].values, color=colors_top, edgecolor='black', linewidth=1)
    ax3.set_yticks(range(len(top_10)))
    ax3.set_yticklabels(top_10_names, fontsize=9)
    ax3.set_xlabel(metric_label, fontsize=12)
    ax3.set_title('Top 10 Most Popular Events', fontsize=14, fontweight='bold')
    ax3.invert_yaxis()
    ax3.grid(axis='x', alpha=0.3)

    # Add labels
    for i, val in enumerate(top_10[metric].values):
        ax3.text(val + max(top_10[metric]) * 0.02, i, f'{val:.1f}', va='center', fontsize=9)

    # Chart 4: Bottom 10 worst-performing events
    bottom_10 = valid_fill_data.nsmallest(10, metric)[['event_name', metric, 'category']]
    bottom_10_names = [name[:30] + '...' if len(name) > 30 else name for name in bottom_10['event_name']]

    colors_bottom = plt.cm.Reds([0.8] * len(bottom_10))
    ax4.barh(range(len(bottom_10)), bottom_10[metric].values, color=colors_bottom, edgecolor='black', linewidth=1)
    ax4.set_yticks(range(len(bottom_10)))
    ax4.set_yticklabels(bottom_10_names, fontsize=9)
    ax4.set_xlabel(metric_label, fontsize=12)
    ax4.set_title('Bottom 10 Least Popular Events', fontsize=14, fontweight='bold')
    ax4.invert_yaxis()
    ax4.grid(axis='x', alpha=0.3)

    # Add labels
    for i, val in enumerate(bottom_10[metric].values):
        ax4.text(val + max(bottom_10[metric]) * 0.02, i, f'{val:.1f}', va='center', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Visualization saved to {output_path}")
    plt.close()


def generate_narrative_insights(results):
    """
    Generate narrative insights from fill rate analysis.

    Args:
        results: Analysis results dictionary

    Returns:
        str: Narrative insights text
    """
    print("\nGenerating narrative insights...")

    total_reg = results.get('total_registrants', 0)
    avg_att = results.get('avg_attendance')
    underperforming_count = len(results.get('underperforming_events', []))

    # Format average attendance
    avg_att_str = f"{avg_att:.1f}" if avg_att is not None else "N/A"

    narrative = f"""
## Event Popularity Analysis

**Overall Performance:**
- **Total event registrants:** {total_reg:,}
- **Average attendance per event:** {avg_att_str}
- **Low-performing events (bottom 50%):** {underperforming_count}

**Top Low-Performing Events:**
"""

    # List top 5 underperforming events
    underperforming = results.get('underperforming_events', [])
    for i, event in enumerate(underperforming[:5], 1):
        metric_key = list(event.keys())[2]  # Get the metric name (avg_attendance or total_registrants)
        narrative += f"{i}. **{event['event_name']}** ({event['category']}): {event[metric_key]:.1f}\n"

    narrative += f"""
**Strategic Recommendations:**

1. **Cancel/Consolidate Low-Performing Events:**
   - Reallocate instructor time to high-demand categories
   - Merge similar low-attendance events into one stronger offering

2. **Optimize Pricing and Timing:**
   - Test discounts to attract fence-sitters
   - Move underperforming evening events to midday slots

3. **Expand Popular Events:**
   - Add additional time slots for high-attendance categories
   - Consider waitlist for consistently full events

4. **Category-Specific Marketing:**
   - Identify which customer segments attend popular events
   - Target similar profiles for underperforming categories

5. **Programming Mix:**
   - Focus resources on Open Play, Drills/Skills (highest attendance)
   - Reduce or reposition low-attendance specialty events
"""

    print(narrative)
    return narrative


def main():
    """Main execution function."""
    # Output paths
    visualization_output = 'deliverables/visualizations/event_fill_rates.png'
    data_output = 'deliverables/data/event_performance.json'

    try:
        # Load data
        registrants, summary = load_event_data()

        # Calculate fill rates
        fill_data = calculate_fill_rates(registrants, summary)

        # Categorize events
        fill_data = categorize_events(fill_data, registrants)

        # Analyze fill rates by category
        results = analyze_fill_rates_by_category(fill_data)

        # Create visualization
        if results:
            create_fill_rate_visualization(fill_data, results, visualization_output)

            # Generate narrative insights
            narrative = generate_narrative_insights(results)

            # Save results to JSON
            combined_results = {
                'fill_rate_analysis': results,
                'narrative': narrative
            }

            with open(data_output, 'w') as f:
                json.dump(combined_results, f, indent=2, default=str)
            print(f"\nData results saved to {data_output}")

            print("\n✅ Event fill rate analysis complete!")
            print(f"   - Visualization: {visualization_output}")
            print(f"   - Data: {data_output}")
        else:
            print("\n⚠️  No valid fill rate data available. Skipping visualization and narrative.")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
