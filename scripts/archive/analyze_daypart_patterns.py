#!/usr/bin/env python3
"""
Daypart Pattern Analysis
Analyzes customer behavioral patterns across different times of day.

Purpose: Identify which customer segments prefer Early AM, Midday, Evening, or Late time slots
Output: Heatmap visualization + daypart preference insights

Daypart Definitions:
- Early AM: 5:00 AM - 11:00 AM
- Midday: 11:00 AM - 4:00 PM
- Evening: 4:00 PM - 9:00 PM
- Late: 9:00 PM - 12:00 AM

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


def classify_daypart(hour):
    """
    Classify hour (0-23) into daypart category.

    Args:
        hour: Integer hour of day (0-23)

    Returns:
        String: 'Early AM', 'Midday', 'Evening', or 'Late'
    """
    if 5 <= hour < 11:
        return 'Early AM'
    elif 11 <= hour < 16:
        return 'Midday'
    elif 16 <= hour < 21:
        return 'Evening'
    elif 21 <= hour < 24 or 0 <= hour < 5:
        return 'Late'
    else:
        return 'Unknown'


def load_and_prepare_data():
    """
    Load reservations and check-ins data from database.

    Returns:
        tuple: (reservations_df, checkins_df)
    """
    print("Loading data from database...")

    with CourtReserveDB() as db:
        reservations = db.get_reservations()
        checkins = db.get_checkins()

    print(f"  Loaded {len(reservations)} reservation records")
    print(f"  Loaded {len(checkins)} check-in records")

    return reservations, checkins


def analyze_reservation_dayparts(reservations):
    """
    Analyze daypart patterns from reservations data.

    Args:
        reservations: DataFrame with reservation records

    Returns:
        dict: Analysis results with daypart distribution, top players per daypart
    """
    print("\nAnalyzing reservation daypart patterns...")

    # Extract hour from start_datetime
    reservations['hour'] = reservations['start_datetime'].dt.hour
    reservations['daypart'] = reservations['hour'].apply(classify_daypart)

    # Filter out Unknown dayparts
    valid_reservations = reservations[reservations['daypart'] != 'Unknown'].copy()

    # Overall daypart distribution
    daypart_counts = valid_reservations['daypart'].value_counts()
    daypart_pcts = (daypart_counts / len(valid_reservations) * 100).round(1)

    print(f"\nOverall Daypart Distribution ({len(valid_reservations)} reservations):")
    for daypart in ['Early AM', 'Midday', 'Evening', 'Late']:
        count = daypart_counts.get(daypart, 0)
        pct = daypart_pcts.get(daypart, 0)
        print(f"  {daypart:12s}: {count:5,} ({pct:5.1f}%)")

    # Daypart preferences by player
    if 'player__#' in valid_reservations.columns:
        player_col = 'player__#'
    elif 'Player _#' in valid_reservations.columns:
        player_col = 'Player _#'
    else:
        print("Warning: No player ID column found")
        return {
            'daypart_distribution': daypart_counts.to_dict(),
            'daypart_percentages': daypart_pcts.to_dict()
        }

    player_dayparts = valid_reservations.groupby([player_col, 'daypart']).size().reset_index(name='count')
    player_totals = valid_reservations.groupby(player_col).size().reset_index(name='total_reservations')

    # Find dominant daypart for each player
    player_dominant = player_dayparts.loc[player_dayparts.groupby(player_col)['count'].idxmax()]
    player_dominant = player_dominant.merge(player_totals, on=player_col)

    # Calculate percentage of visits in dominant daypart
    player_dominant['dominant_pct'] = (player_dominant['count'] / player_dominant['total_reservations'] * 100).round(1)

    # Top 10 players per daypart (by visit frequency)
    top_players_by_daypart = {}
    for daypart in ['Early AM', 'Midday', 'Evening', 'Late']:
        daypart_players = player_dominant[player_dominant['daypart'] == daypart].copy()
        top_10 = daypart_players.nlargest(10, 'count')
        top_players_by_daypart[daypart] = top_10.to_dict('records')

    # Behavioral insights: What % of players are "loyal" to one daypart (>70% of visits)?
    loyal_players = player_dominant[player_dominant['dominant_pct'] >= 70]
    loyal_pct = len(loyal_players) / len(player_dominant) * 100

    print(f"\nDaypart Loyalty:")
    print(f"  Players with ≥70% visits in single daypart: {len(loyal_players):,} ({loyal_pct:.1f}%)")

    results = {
        'daypart_distribution': daypart_counts.to_dict(),
        'daypart_percentages': daypart_pcts.to_dict(),
        'top_players_by_daypart': top_players_by_daypart,
        'loyalty_stats': {
            'loyal_players_count': int(len(loyal_players)),
            'loyal_percentage': float(loyal_pct),
            'total_players': int(len(player_dominant))
        }
    }

    return results


def analyze_checkin_dayparts(checkins):
    """
    Analyze daypart patterns from check-ins data.

    Args:
        checkins: DataFrame with check-in records

    Returns:
        dict: Analysis results with daypart distribution by membership type
    """
    print("\nAnalyzing check-in daypart patterns...")

    # Extract hour from checkin_datetime
    checkins['hour'] = checkins['checkin_datetime'].dt.hour
    checkins['daypart'] = checkins['hour'].apply(classify_daypart)

    # Filter out Unknown dayparts
    valid_checkins = checkins[checkins['daypart'] != 'Unknown'].copy()

    # Daypart distribution by membership type
    if 'membership_name' not in valid_checkins.columns:
        print("Warning: No membership_name column found")
        return {}

    membership_daypart = pd.crosstab(
        valid_checkins['membership_name'],
        valid_checkins['daypart'],
        normalize='index'
    ) * 100

    # Sort dayparts in chronological order
    daypart_order = ['Early AM', 'Midday', 'Evening', 'Late']
    membership_daypart = membership_daypart[[col for col in daypart_order if col in membership_daypart.columns]]

    print(f"\nDaypart Distribution by Membership Type (% of check-ins):")
    print(membership_daypart.round(1).to_string())

    results = {
        'membership_daypart_distribution': membership_daypart.to_dict()
    }

    return results


def create_daypart_heatmap(reservation_results, checkin_results, output_path):
    """
    Create heatmap visualization of daypart patterns.

    Args:
        reservation_results: Results from reservation analysis
        checkin_results: Results from check-in analysis
        output_path: Path to save heatmap PNG
    """
    print("\nCreating daypart heatmap visualization...")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Chart 1: Overall daypart distribution (from reservations)
    daypart_order = ['Early AM', 'Midday', 'Evening', 'Late']
    daypart_pcts = reservation_results['daypart_percentages']

    values = [daypart_pcts.get(dp, 0) for dp in daypart_order]
    colors = ['#FFA500', '#FFD700', '#FF6347', '#8B008B']  # Orange, Gold, Tomato, Purple

    ax1.bar(daypart_order, values, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Percentage of Reservations (%)', fontsize=12)
    ax1.set_title('Reservation Distribution by Daypart', fontsize=14, fontweight='bold')
    ax1.set_ylim(0, max(values) * 1.2)
    ax1.grid(axis='y', alpha=0.3)

    # Add percentage labels on bars
    for i, (dp, val) in enumerate(zip(daypart_order, values)):
        ax1.text(i, val + 1, f'{val:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

    # Chart 2: Membership daypart heatmap (from check-ins)
    if 'membership_daypart_distribution' in checkin_results:
        membership_daypart = pd.DataFrame(checkin_results['membership_daypart_distribution'])

        # Transpose for better visualization (membership types as rows, dayparts as columns)
        membership_daypart = membership_daypart.T

        # Limit to top 10 membership types by total check-ins
        if len(membership_daypart) > 10:
            membership_daypart = membership_daypart.iloc[:10]

        sns.heatmap(
            membership_daypart,
            annot=True,
            fmt='.1f',
            cmap='YlOrRd',
            cbar_kws={'label': '% of Check-ins'},
            linewidths=0.5,
            ax=ax2
        )
        ax2.set_title('Daypart Preferences by Membership Type', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Daypart', fontsize=12)
        ax2.set_ylabel('Membership Type', fontsize=12)
    else:
        ax2.text(0.5, 0.5, 'Check-in data not available',
                ha='center', va='center', fontsize=14)
        ax2.axis('off')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Heatmap saved to {output_path}")
    plt.close()


def generate_narrative_insights(reservation_results, checkin_results):
    """
    Generate narrative insights from daypart analysis.

    Args:
        reservation_results: Results from reservation analysis
        checkin_results: Results from check-in analysis

    Returns:
        str: Narrative insights text
    """
    print("\nGenerating narrative insights...")

    daypart_pcts = reservation_results['daypart_percentages']
    loyalty = reservation_results['loyalty_stats']

    # Find most and least popular dayparts
    sorted_dayparts = sorted(daypart_pcts.items(), key=lambda x: x[1], reverse=True)
    most_popular = sorted_dayparts[0]
    least_popular = sorted_dayparts[-1]

    narrative = f"""
## Daypart Pattern Analysis

**Overall Reservation Distribution:**
- **Most Popular:** {most_popular[0]} ({most_popular[1]:.1f}% of reservations)
- **Least Popular:** {least_popular[0]} ({least_popular[1]:.1f}% of reservations)

**Daypart Breakdown:**
"""

    for daypart in ['Early AM', 'Midday', 'Evening', 'Late']:
        pct = daypart_pcts.get(daypart, 0)
        narrative += f"- **{daypart}** (5-11 AM): {pct:.1f}%\n" if daypart == 'Early AM' else ""
        narrative += f"- **{daypart}** (11 AM-4 PM): {pct:.1f}%\n" if daypart == 'Midday' else ""
        narrative += f"- **{daypart}** (4-9 PM): {pct:.1f}%\n" if daypart == 'Evening' else ""
        narrative += f"- **{daypart}** (9 PM-12 AM): {pct:.1f}%\n" if daypart == 'Late' else ""

    narrative += f"""
**Behavioral Loyalty:**
- **Daypart-loyal players:** {loyalty['loyal_players_count']:,} players ({loyalty['loyal_percentage']:.1f}%)
- **Definition:** Players with ≥70% of visits in a single daypart
- **Interpretation:** {loyalty['loyal_percentage']:.0f}% of players have predictable time preferences

**Strategic Implications:**

1. **Capacity Planning:** Focus staffing/amenities on {most_popular[0]} when demand peaks
2. **Conversion Opportunities:** Target {least_popular[0]} slots for discounted memberships
3. **Segment-Specific Programming:** Design events for daypart-loyal segments
4. **Work-from-Home Advantage:** Midday slots are prime for WFH professionals
5. **Retiree Programs:** Early AM slots ideal for senior programming
"""

    print(narrative)
    return narrative


def main():
    """Main execution function."""
    # Output paths
    visualization_output = 'deliverables/visualizations/daypart_heatmap.png'
    data_output = 'deliverables/data/daypart_analysis.json'

    try:
        # Load data
        reservations, checkins = load_and_prepare_data()

        # Analyze reservation dayparts
        reservation_results = analyze_reservation_dayparts(reservations)

        # Analyze check-in dayparts
        checkin_results = analyze_checkin_dayparts(checkins)

        # Create visualization
        create_daypart_heatmap(reservation_results, checkin_results, visualization_output)

        # Generate narrative insights
        narrative = generate_narrative_insights(reservation_results, checkin_results)

        # Save results to JSON
        combined_results = {
            'reservation_analysis': reservation_results,
            'checkin_analysis': checkin_results,
            'narrative': narrative
        }

        with open(data_output, 'w') as f:
            json.dump(combined_results, f, indent=2)
        print(f"\nData results saved to {data_output}")

        print("\n✅ Daypart pattern analysis complete!")
        print(f"   - Visualization: {visualization_output}")
        print(f"   - Data: {data_output}")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
