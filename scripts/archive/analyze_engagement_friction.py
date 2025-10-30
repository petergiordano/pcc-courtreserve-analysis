#!/usr/bin/env python3
"""
Engagement Friction Analysis
Analyzes cancellation patterns, barriers to engagement, and drop-off points.

Purpose: Identify friction points that prevent customer engagement
Output: Friction metrics visualization + strategic recommendations

Friction Metrics:
- Cancellation rate by event type
- Time-to-cancellation patterns
- Repeat cancellers (serial cancellers vs. one-time)
- No-show patterns (registered but didn't check in)

Author: Claude Code (Anthropic)
Date: October 27, 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))
from db_loader import CourtReserveDB


def load_engagement_data():
    """
    Load reservations, cancellations, and check-ins data.

    Returns:
        tuple: (reservations_df, cancellations_df, checkins_df)
    """
    print("Loading engagement data from database...")

    with CourtReserveDB() as db:
        reservations = db.get_reservations()
        cancellations = db.get_cancellations()
        checkins = db.get_checkins()

    print(f"  Loaded {len(reservations)} reservations")
    print(f"  Loaded {len(cancellations)} cancellations")
    print(f"  Loaded {len(checkins)} check-ins")

    return reservations, cancellations, checkins


def analyze_cancellation_patterns(cancellations):
    """
    Analyze cancellation patterns and friction points.

    Args:
        cancellations: DataFrame with cancellation records

    Returns:
        dict: Cancellation analysis results
    """
    print("\nAnalyzing cancellation patterns...")

    if len(cancellations) == 0:
        print("Warning: No cancellation data found")
        return {}

    # Overall cancellation stats
    total_cancellations = len(cancellations)
    print(f"\nTotal cancellations: {total_cancellations:,}")

    # Cancellation rate by event/activity (if event_name available)
    if 'event_name' in cancellations.columns:
        cancel_by_event = cancellations['event_name'].value_counts().head(20)
        print(f"\nTop 20 Cancelled Events:")
        print(cancel_by_event.to_string())
    else:
        cancel_by_event = None

    # Time-to-cancellation analysis (if timestamps available)
    if 'start_datetime' in cancellations.columns and 'cancelled_on' in cancellations.columns:
        cancellations['time_to_cancel'] = (
            cancellations['start_datetime'] - cancellations['cancelled_on']
        ).dt.total_seconds() / 3600  # Convert to hours

        # Filter valid time_to_cancel (positive values)
        valid_cancel_times = cancellations[cancellations['time_to_cancel'] > 0].copy()

        if len(valid_cancel_times) > 0:
            avg_time_to_cancel = valid_cancel_times['time_to_cancel'].mean()
            median_time_to_cancel = valid_cancel_times['time_to_cancel'].median()

            # Categorize by urgency
            valid_cancel_times['cancel_urgency'] = pd.cut(
                valid_cancel_times['time_to_cancel'],
                bins=[0, 24, 72, 168, float('inf')],
                labels=['<24h', '1-3 days', '3-7 days', '>7 days']
            )

            urgency_dist = valid_cancel_times['cancel_urgency'].value_counts()

            print(f"\nTime to Cancellation:")
            print(f"  Average: {avg_time_to_cancel:.1f} hours ({avg_time_to_cancel/24:.1f} days)")
            print(f"  Median: {median_time_to_cancel:.1f} hours ({median_time_to_cancel/24:.1f} days)")
            print(f"\nCancellation Urgency Distribution:")
            print(urgency_dist.to_string())

            time_to_cancel_stats = {
                'avg_hours': float(avg_time_to_cancel),
                'median_hours': float(median_time_to_cancel),
                'urgency_distribution': urgency_dist.to_dict()
            }
        else:
            time_to_cancel_stats = None
    else:
        time_to_cancel_stats = None

    # Repeat cancellers analysis (if player ID available)
    if 'player__#' in cancellations.columns:
        player_cancel_counts = cancellations.groupby('player__#').size()
        repeat_cancellers = player_cancel_counts[player_cancel_counts > 1]
        serial_cancellers = player_cancel_counts[player_cancel_counts >= 5]

        print(f"\nRepeat Cancellers:")
        print(f"  Players with >1 cancellation: {len(repeat_cancellers):,}")
        print(f"  Serial cancellers (≥5 cancellations): {len(serial_cancellers):,}")

        if len(serial_cancellers) > 0:
            print(f"\nTop 10 Serial Cancellers:")
            top_serial = serial_cancellers.nlargest(10)
            print(top_serial.to_string())

        repeat_canceller_stats = {
            'repeat_count': int(len(repeat_cancellers)),
            'serial_count': int(len(serial_cancellers)),
            'top_serial_cancellers': serial_cancellers.nlargest(10).to_dict()
        }
    else:
        repeat_canceller_stats = None

    results = {
        'total_cancellations': int(total_cancellations),
        'top_cancelled_events': cancel_by_event.head(10).to_dict() if cancel_by_event is not None else None,
        'time_to_cancel_stats': time_to_cancel_stats,
        'repeat_canceller_stats': repeat_canceller_stats
    }

    return results


def analyze_no_show_patterns(reservations, checkins):
    """
    Analyze no-show patterns (reserved but didn't check in).

    Args:
        reservations: DataFrame with reservation records
        checkins: DataFrame with check-in records

    Returns:
        dict: No-show analysis results
    """
    print("\nAnalyzing no-show patterns...")

    # Need matching keys between reservations and check-ins
    # Try confirmation_# or player__# + start_datetime
    if 'confirmation_#' in reservations.columns and 'confirmation_#' in checkins.columns:
        # Match by confirmation number
        checked_in_confirmations = set(checkins['confirmation_#'].dropna().unique())
        reservations['checked_in'] = reservations['confirmation_#'].isin(checked_in_confirmations)

        no_shows = reservations[~reservations['checked_in']]
        no_show_rate = len(no_shows) / len(reservations) * 100

        print(f"\nNo-Show Analysis:")
        print(f"  Total reservations: {len(reservations):,}")
        print(f"  Check-ins: {len(reservations[reservations['checked_in']]):,}")
        print(f"  No-shows: {len(no_shows):,}")
        print(f"  No-show rate: {no_show_rate:.1f}%")

        results = {
            'total_reservations': int(len(reservations)),
            'checked_in_count': int(len(reservations[reservations['checked_in']])),
            'no_show_count': int(len(no_shows)),
            'no_show_rate': float(no_show_rate)
        }

        return results
    else:
        print("Warning: Cannot match reservations to check-ins (missing confirmation_#)")
        return {}


def create_friction_visualization(cancel_results, no_show_results, output_path):
    """
    Create visualization of engagement friction metrics.

    Args:
        cancel_results: Cancellation analysis results
        no_show_results: No-show analysis results
        output_path: Path to save visualization PNG
    """
    print("\nCreating friction metrics visualization...")

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # Chart 1: Top cancelled events
    if cancel_results.get('top_cancelled_events'):
        top_cancelled = pd.Series(cancel_results['top_cancelled_events'])
        top_10 = top_cancelled.head(10)
        event_names = [name[:30] + '...' if len(name) > 30 else name for name in top_10.index]

        colors = plt.cm.Reds([0.7] * len(top_10))
        ax1.barh(range(len(top_10)), top_10.values, color=colors, edgecolor='black', linewidth=1)
        ax1.set_yticks(range(len(top_10)))
        ax1.set_yticklabels(event_names, fontsize=9)
        ax1.set_xlabel('Cancellation Count', fontsize=12)
        ax1.set_title('Top 10 Most Cancelled Events', fontsize=14, fontweight='bold')
        ax1.invert_yaxis()
        ax1.grid(axis='x', alpha=0.3)

        for i, val in enumerate(top_10.values):
            ax1.text(val + max(top_10) * 0.02, i, f'{int(val)}', va='center', fontsize=9)
    else:
        ax1.text(0.5, 0.5, 'No cancellation data available', ha='center', va='center', fontsize=14)
        ax1.axis('off')

    # Chart 2: Cancellation urgency distribution
    if cancel_results.get('time_to_cancel_stats') and cancel_results['time_to_cancel_stats'].get('urgency_distribution'):
        urgency_dist = pd.Series(cancel_results['time_to_cancel_stats']['urgency_distribution'])
        urgency_order = ['<24h', '1-3 days', '3-7 days', '>7 days']
        urgency_dist = urgency_dist.reindex(urgency_order, fill_value=0)

        colors = ['#d32f2f', '#f57c00', '#fbc02d', '#7cb342']
        ax2.bar(urgency_dist.index, urgency_dist.values, color=colors, edgecolor='black', linewidth=1.5)
        ax2.set_ylabel('Number of Cancellations', fontsize=12)
        ax2.set_title('Cancellation Urgency (Time Before Event)', fontsize=14, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)

        for i, val in enumerate(urgency_dist.values):
            ax2.text(i, val + max(urgency_dist) * 0.02, f'{int(val)}', ha='center', fontsize=10, fontweight='bold')
    else:
        ax2.text(0.5, 0.5, 'No time-to-cancel data available', ha='center', va='center', fontsize=14)
        ax2.axis('off')

    # Chart 3: No-show rate
    if no_show_results:
        no_show_rate = no_show_results.get('no_show_rate', 0)
        check_in_rate = 100 - no_show_rate

        rates = [check_in_rate, no_show_rate]
        labels = ['Checked In', 'No-Show']
        colors = ['#4caf50', '#f44336']

        wedges, texts, autotexts = ax3.pie(
            rates,
            labels=labels,
            autopct='%1.1f%%',
            colors=colors,
            startangle=90,
            textprops={'fontsize': 12, 'fontweight': 'bold'}
        )
        ax3.set_title('Reservation Check-In Rate', fontsize=14, fontweight='bold')
    else:
        ax3.text(0.5, 0.5, 'No-show data not available', ha='center', va='center', fontsize=14)
        ax3.axis('off')

    # Chart 4: Repeat cancellers distribution
    if cancel_results.get('repeat_canceller_stats'):
        repeat_stats = cancel_results['repeat_canceller_stats']
        top_serial = pd.Series(repeat_stats.get('top_serial_cancellers', {})).head(10)

        if len(top_serial) > 0:
            colors = plt.cm.Oranges(np.linspace(0.5, 0.9, len(top_serial)))
            ax4.barh(range(len(top_serial)), top_serial.values, color=colors, edgecolor='black', linewidth=1)
            ax4.set_yticks(range(len(top_serial)))
            ax4.set_yticklabels([f'Player #{pid}' for pid in top_serial.index], fontsize=9)
            ax4.set_xlabel('Number of Cancellations', fontsize=12)
            ax4.set_title('Top 10 Serial Cancellers', fontsize=14, fontweight='bold')
            ax4.invert_yaxis()
            ax4.grid(axis='x', alpha=0.3)

            for i, val in enumerate(top_serial.values):
                ax4.text(val + max(top_serial) * 0.02, i, f'{int(val)}', va='center', fontsize=9)
        else:
            ax4.text(0.5, 0.5, 'No serial canceller data', ha='center', va='center', fontsize=14)
            ax4.axis('off')
    else:
        ax4.text(0.5, 0.5, 'No repeat canceller data', ha='center', va='center', fontsize=14)
        ax4.axis('off')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Visualization saved to {output_path}")
    plt.close()


def generate_narrative_insights(cancel_results, no_show_results):
    """
    Generate narrative insights from friction analysis.

    Args:
        cancel_results: Cancellation analysis results
        no_show_results: No-show analysis results

    Returns:
        str: Narrative insights text
    """
    print("\nGenerating narrative insights...")

    total_cancels = cancel_results.get('total_cancellations', 0)
    no_show_rate = no_show_results.get('no_show_rate', 0) if no_show_results else 0

    narrative = f"""
## Engagement Friction Analysis

**Cancellation Overview:**
- **Total cancellations:** {total_cancels:,}
"""

    # Time-to-cancellation insights
    if cancel_results.get('time_to_cancel_stats'):
        time_stats = cancel_results['time_to_cancel_stats']
        avg_hours = time_stats['avg_hours']
        avg_days = avg_hours / 24

        narrative += f"""
**Cancellation Timing:**
- **Average time to cancel:** {avg_days:.1f} days before event
- **Median time to cancel:** {time_stats['median_hours']/24:.1f} days before event
"""

        # Urgency distribution
        if time_stats.get('urgency_distribution'):
            urgency = time_stats['urgency_distribution']
            last_minute = urgency.get('<24h', 0)
            total_with_urgency = sum(urgency.values())
            last_minute_pct = (last_minute / total_with_urgency * 100) if total_with_urgency > 0 else 0

            narrative += f"""
**Last-Minute Cancellations (<24h):** {last_minute:,} ({last_minute_pct:.1f}%)
- Creates scheduling chaos and lost revenue
- Difficult to backfill on short notice
"""

    # Repeat cancellers
    if cancel_results.get('repeat_canceller_stats'):
        repeat_stats = cancel_results['repeat_canceller_stats']
        repeat_count = repeat_stats['repeat_count']
        serial_count = repeat_stats['serial_count']

        narrative += f"""
**Repeat Canceller Problem:**
- **Players with multiple cancellations:** {repeat_count:,}
- **Serial cancellers (≥5 cancellations):** {serial_count:,}
- These players create predictable friction and revenue loss
"""

    # No-show insights
    if no_show_results:
        narrative += f"""
**No-Show Rate:** {no_show_rate:.1f}%
- Reservations made but customers didn't show up
- Creates false scarcity (blocks others from booking)
"""

    narrative += f"""
**Strategic Recommendations:**

1. **Implement Cancellation Penalties:**
   - Charge 50% for cancellations within 24 hours
   - Full charge for no-shows (or credit-only)
   - Creates accountability and reduces last-minute cancellations

2. **Serial Canceller Policy:**
   - Flag players with ≥5 cancellations in 90 days
   - Require deposit or restrict advance booking privileges
   - Protects inventory for reliable customers

3. **Waitlist Automation:**
   - Auto-fill cancelled spots from waitlist (within 24h)
   - SMS/email notification for immediate backfill
   - Reduces lost revenue from cancellations

4. **Booking Window Optimization:**
   - Limit how far in advance non-members can book
   - Members get priority booking (incentive to upgrade)
   - Reduces speculative reservations and cancellations

5. **Event-Specific Interventions:**
   - High-cancellation events may have scheduling issues
   - Survey cancellers to understand friction points
   - Consider format changes or discontinuation

**Friction Score Calculation:**
- Cancellation rate + No-show rate = Total friction
- Current friction: {total_cancels:,} cancellations + {no_show_rate:.1f}% no-shows
- Goal: Reduce friction by 30% through policy changes
"""

    print(narrative)
    return narrative


def main():
    """Main execution function."""
    # Output paths
    visualization_output = 'deliverables/visualizations/friction_metrics.png'
    data_output = 'deliverables/data/friction_analysis.json'

    try:
        # Load data
        reservations, cancellations, checkins = load_engagement_data()

        # Analyze cancellation patterns
        cancel_results = analyze_cancellation_patterns(cancellations)

        # Analyze no-show patterns
        no_show_results = analyze_no_show_patterns(reservations, checkins)

        # Create visualization
        create_friction_visualization(cancel_results, no_show_results, visualization_output)

        # Generate narrative insights
        narrative = generate_narrative_insights(cancel_results, no_show_results)

        # Save results to JSON
        combined_results = {
            'cancellation_analysis': cancel_results,
            'no_show_analysis': no_show_results,
            'narrative': narrative
        }

        with open(data_output, 'w') as f:
            json.dump(combined_results, f, indent=2, default=str)
        print(f"\nData results saved to {data_output}")

        print("\n✅ Engagement friction analysis complete!")
        print(f"   - Visualization: {visualization_output}")
        print(f"   - Data: {data_output}")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
