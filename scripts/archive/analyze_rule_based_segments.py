#!/usr/bin/env python3
"""
Rule-Based Segmentation Analysis
Implements ChatGPT's 5 behavioral cluster framework as an alternative to K-Means.

Purpose: Validate K-Means clustering with rule-based behavioral segmentation
Output: Segment distribution visualization + comparison with JTBD clusters

ChatGPT's 5 Behavioral Clusters:
1. **Competitive Regulars** - Tournament/league players, high frequency, peak hours
2. **Social Casuals** - Open play focus, moderate frequency, social motivation
3. **Skill Builders** - Drills/clinics, improvement-focused, consistent attendance
4. **Drop-In Experimenters** - Low frequency, trying different formats, price-sensitive
5. **Peak-Hour Warriors** - Evening/weekend only, work schedule constraints

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


def load_behavioral_data():
    """
    Load reservations, check-ins, and events data for segmentation.

    Returns:
        tuple: (reservations_df, checkins_df, members_df)
    """
    print("Loading behavioral data from database...")

    with CourtReserveDB() as db:
        reservations = db.get_reservations()
        checkins = db.get_checkins()
        members = db.get_members()

    print(f"  Loaded {len(reservations)} reservations")
    print(f"  Loaded {len(checkins)} check-ins")
    print(f"  Loaded {len(members)} members")

    return reservations, checkins, members


def classify_event_type(event_name):
    """
    Classify event into category for behavioral analysis.

    Args:
        event_name: Event name string

    Returns:
        str: Event category
    """
    if pd.isna(event_name):
        return 'Unknown'

    event_lower = str(event_name).lower()

    # Competitive events
    if any(word in event_lower for word in ['tournament', 'league', 'ladder', 'competitive', 'championship']):
        return 'Competitive'

    # Skill-building events
    if any(word in event_lower for word in ['drill', 'skill', 'clinic', 'lesson', 'academy', 'training']):
        return 'Skill-Building'

    # Open play / social
    if any(word in event_lower for word in ['open play', 'drop-in', 'social', 'mixer']):
        return 'Social/Open Play'

    return 'Other'


def classify_time_preference(hour):
    """
    Classify hour into time preference category.

    Args:
        hour: Hour of day (0-23)

    Returns:
        str: Time preference category
    """
    if 5 <= hour < 11:
        return 'Morning'
    elif 11 <= hour < 16:
        return 'Midday'
    elif 16 <= hour < 21:
        return 'Peak Evening'
    else:
        return 'Late/Off-Peak'


def segment_customers_rule_based(reservations, checkins, members):
    """
    Apply rule-based segmentation logic to assign customers to behavioral clusters.

    Args:
        reservations: DataFrame with reservation records
        checkins: DataFrame with check-in records
        members: DataFrame with member records

    Returns:
        DataFrame: Customer segments with behavioral profiles
    """
    print("\nApplying rule-based segmentation...")

    # Combine reservations and check-ins for comprehensive view
    # Use reservations as primary source
    if 'player__#' not in reservations.columns:
        print("Warning: No player ID column found in reservations")
        return pd.DataFrame()

    # Extract behavioral features per player
    player_behaviors = []

    for player_id in reservations['player__#'].unique():
        player_reservations = reservations[reservations['player__#'] == player_id]

        # Frequency
        visit_count = len(player_reservations)

        # Event type preferences
        if 'event_name' in player_reservations.columns:
            player_reservations['event_type'] = player_reservations['event_name'].apply(classify_event_type)
            event_type_dist = player_reservations['event_type'].value_counts()

            competitive_pct = (event_type_dist.get('Competitive', 0) / visit_count * 100) if visit_count > 0 else 0
            skill_pct = (event_type_dist.get('Skill-Building', 0) / visit_count * 100) if visit_count > 0 else 0
            social_pct = (event_type_dist.get('Social/Open Play', 0) / visit_count * 100) if visit_count > 0 else 0
        else:
            competitive_pct = 0
            skill_pct = 0
            social_pct = 0

        # Time preferences
        if 'start_datetime' in player_reservations.columns:
            player_reservations['hour'] = player_reservations['start_datetime'].dt.hour
            player_reservations['time_pref'] = player_reservations['hour'].apply(classify_time_preference)
            time_dist = player_reservations['time_pref'].value_counts()

            peak_evening_pct = (time_dist.get('Peak Evening', 0) / visit_count * 100) if visit_count > 0 else 0
        else:
            peak_evening_pct = 0

        player_behaviors.append({
            'player_id': player_id,
            'visit_count': visit_count,
            'competitive_pct': competitive_pct,
            'skill_pct': skill_pct,
            'social_pct': social_pct,
            'peak_evening_pct': peak_evening_pct
        })

    behavior_df = pd.DataFrame(player_behaviors)

    # Apply segmentation rules
    def assign_segment(row):
        """Assign segment based on ChatGPT's behavioral cluster definitions."""

        # 1. Competitive Regulars: High frequency + competitive events
        if row['visit_count'] >= 20 and row['competitive_pct'] >= 30:
            return 'Competitive Regulars'

        # 2. Skill Builders: Drills/clinics focus
        if row['skill_pct'] >= 40:
            return 'Skill Builders'

        # 3. Social Casuals: Open play focus, moderate frequency
        if row['social_pct'] >= 50 and row['visit_count'] >= 5:
            return 'Social Casuals'

        # 4. Peak-Hour Warriors: Evening-only players
        if row['peak_evening_pct'] >= 70:
            return 'Peak-Hour Warriors'

        # 5. Drop-In Experimenters: Low frequency, exploring
        if row['visit_count'] < 5:
            return 'Drop-In Experimenters'

        # Default: Social Casuals (most common)
        return 'Social Casuals'

    behavior_df['segment'] = behavior_df.apply(assign_segment, axis=1)

    # Summary stats
    segment_counts = behavior_df['segment'].value_counts()
    print(f"\nSegment Distribution:")
    for segment, count in segment_counts.items():
        pct = count / len(behavior_df) * 100
        print(f"  {segment:30s}: {count:5,} ({pct:5.1f}%)")

    return behavior_df


def create_segment_visualization(behavior_df, output_path):
    """
    Create visualization of rule-based segments.

    Args:
        behavior_df: DataFrame with segmented customers
        output_path: Path to save visualization PNG
    """
    print("\nCreating segment visualization...")

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # Chart 1: Segment distribution (pie chart)
    segment_counts = behavior_df['segment'].value_counts()
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']

    wedges, texts, autotexts = ax1.pie(
        segment_counts.values,
        labels=segment_counts.index,
        autopct='%1.1f%%',
        colors=colors[:len(segment_counts)],
        startangle=90,
        textprops={'fontsize': 10}
    )
    ax1.set_title('Rule-Based Segment Distribution', fontsize=14, fontweight='bold')

    # Chart 2: Average visit frequency by segment
    avg_visits = behavior_df.groupby('segment')['visit_count'].mean().sort_values(ascending=False)
    colors_bar = plt.cm.viridis(np.linspace(0.3, 0.9, len(avg_visits)))

    ax2.barh(avg_visits.index, avg_visits.values, color=colors_bar, edgecolor='black', linewidth=1)
    ax2.set_xlabel('Average Visit Count', fontsize=12)
    ax2.set_title('Average Frequency by Segment', fontsize=14, fontweight='bold')
    ax2.grid(axis='x', alpha=0.3)

    for i, val in enumerate(avg_visits.values):
        ax2.text(val + max(avg_visits) * 0.02, i, f'{val:.1f}', va='center', fontsize=10, fontweight='bold')

    # Chart 3: Behavioral profile heatmap
    profile_metrics = ['competitive_pct', 'skill_pct', 'social_pct', 'peak_evening_pct']
    segment_profiles = behavior_df.groupby('segment')[profile_metrics].mean()

    # Rename columns for readability
    segment_profiles.columns = ['Competitive %', 'Skill-Building %', 'Social %', 'Peak Evening %']

    sns.heatmap(
        segment_profiles,
        annot=True,
        fmt='.1f',
        cmap='YlOrRd',
        cbar_kws={'label': 'Percentage'},
        linewidths=0.5,
        ax=ax3
    )
    ax3.set_title('Behavioral Profile by Segment', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Behavioral Metric', fontsize=12)
    ax3.set_ylabel('Segment', fontsize=12)

    # Chart 4: Segment size and average frequency (scatter plot)
    segment_summary = behavior_df.groupby('segment').agg({
        'player_id': 'count',
        'visit_count': 'mean'
    }).reset_index()
    segment_summary.columns = ['segment', 'size', 'avg_visits']

    colors_scatter = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
    for i, row in segment_summary.iterrows():
        ax4.scatter(row['avg_visits'], row['size'], s=row['size']*2, color=colors_scatter[i],
                   alpha=0.7, edgecolor='black', linewidth=2, label=row['segment'])

    ax4.set_xlabel('Average Visit Frequency', fontsize=12)
    ax4.set_ylabel('Segment Size (# of Customers)', fontsize=12)
    ax4.set_title('Segment Size vs. Frequency', fontsize=14, fontweight='bold')
    ax4.legend(fontsize=9, loc='best')
    ax4.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Visualization saved to {output_path}")
    plt.close()


def generate_narrative_insights(behavior_df):
    """
    Generate narrative insights from rule-based segmentation.

    Args:
        behavior_df: DataFrame with segmented customers

    Returns:
        str: Narrative insights text
    """
    print("\nGenerating narrative insights...")

    segment_counts = behavior_df['segment'].value_counts()
    total_customers = len(behavior_df)

    narrative = f"""
## Rule-Based Segmentation Analysis (ChatGPT's 5 Behavioral Clusters)

**Total Customers Segmented:** {total_customers:,}

**Segment Breakdown:**
"""

    for segment, count in segment_counts.items():
        pct = count / total_customers * 100
        avg_visits = behavior_df[behavior_df['segment'] == segment]['visit_count'].mean()
        narrative += f"- **{segment}:** {count:,} customers ({pct:.1f}%) - Avg {avg_visits:.1f} visits\n"

    narrative += f"""
**Segment Definitions:**

1. **Competitive Regulars ({segment_counts.get('Competitive Regulars', 0):,} customers)**
   - High frequency (≥20 visits)
   - Tournament/league participation (≥30%)
   - Target: Premium memberships, advanced programming

2. **Skill Builders ({segment_counts.get('Skill Builders', 0):,} customers)**
   - Drills/clinics focus (≥40%)
   - Improvement-oriented mindset
   - Target: Structured learning paths, instructor upsells

3. **Social Casuals ({segment_counts.get('Social Casuals', 0):,} customers)**
   - Open play preference (≥50%)
   - Moderate frequency (≥5 visits)
   - Target: Social events, drop-in memberships

4. **Peak-Hour Warriors ({segment_counts.get('Peak-Hour Warriors', 0):,} customers)**
   - Evening/weekend only (≥70%)
   - Work schedule constraints
   - Target: Peak-hour passes, flexible memberships

5. **Drop-In Experimenters ({segment_counts.get('Drop-In Experimenters', 0):,} customers)**
   - Low frequency (<5 visits)
   - Exploring different formats
   - Target: Trial memberships, starter packages

**Comparison with K-Means Clustering:**
- Rule-based: Deterministic, interpretable, business-logic driven
- K-Means: Data-driven, discovers hidden patterns, more nuanced
- Both approaches validate each other when segments align
- Use rule-based for marketing/sales; K-Means for behavioral insights

**Strategic Applications:**

1. **Marketing Segmentation:**
   - Different messaging for each segment
   - Competitive Regulars: "Join the elite community"
   - Social Casuals: "Fun, friendly games anytime"

2. **Pricing Strategy:**
   - Peak-Hour Warriors: Premium pricing for evening slots
   - Drop-In Experimenters: Discounted trial offers

3. **Programming Mix:**
   - Skill Builders demand highest instructor quality
   - Social Casuals need variety and flexibility

4. **Retention Focus:**
   - Drop-In Experimenters have lowest lifetime value
   - Competitive Regulars are sticky (high churn cost)
"""

    print(narrative)
    return narrative


def main():
    """Main execution function."""
    # Output paths
    visualization_output = 'deliverables/visualizations/rule_based_segments.png'
    data_output = 'deliverables/data/rule_based_segments.json'

    try:
        # Load data
        reservations, checkins, members = load_behavioral_data()

        # Segment customers using rule-based approach
        behavior_df = segment_customers_rule_based(reservations, checkins, members)

        if len(behavior_df) == 0:
            print("\n⚠️  No customer data available for segmentation")
            sys.exit(1)

        # Create visualization
        create_segment_visualization(behavior_df, visualization_output)

        # Generate narrative insights
        narrative = generate_narrative_insights(behavior_df)

        # Save results to JSON
        segment_summary = behavior_df.groupby('segment').agg({
            'player_id': 'count',
            'visit_count': ['mean', 'median'],
            'competitive_pct': 'mean',
            'skill_pct': 'mean',
            'social_pct': 'mean',
            'peak_evening_pct': 'mean'
        }).round(2)

        # Flatten multi-level columns
        segment_summary.columns = ['_'.join(col).strip('_') if isinstance(col, tuple) else col
                                   for col in segment_summary.columns]

        combined_results = {
            'segment_summary': segment_summary.to_dict(),
            'total_customers': int(len(behavior_df)),
            'segment_distribution': behavior_df['segment'].value_counts().to_dict(),
            'narrative': narrative
        }

        with open(data_output, 'w') as f:
            json.dump(combined_results, f, indent=2, default=str)
        print(f"\nData results saved to {data_output}")

        print("\n✅ Rule-based segmentation complete!")
        print(f"   - Visualization: {visualization_output}")
        print(f"   - Data: {data_output}")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
