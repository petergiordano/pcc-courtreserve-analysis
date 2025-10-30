#!/usr/bin/env python3
"""
Party Size and Social Network Analysis
Analyzes group reservations to identify social networks and playing patterns.

Purpose: Understand how customers play together and identify community leaders
Output: Social network metrics + visualization of key patterns

Key Insights:
- Average party size (solo vs. group players)
- Most connected players (community hubs)
- Playing partner frequency
- Social clusters and cliques

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
import re
from pathlib import Path
from collections import Counter, defaultdict

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))
from db_loader import CourtReserveDB


def load_reservation_data():
    """
    Load reservations with party and guest information.

    Returns:
        DataFrame: Reservations with party size and member data
    """
    print("Loading reservation data from database...")

    with CourtReserveDB() as db:
        reservations = db.get_reservations()

    print(f"  Loaded {len(reservations)} reservations")
    return reservations


def parse_members_field(members_str):
    """
    Parse the members field to extract player IDs.

    Format: "Name1 (#ID1), Name2 (#ID2), ..."

    Args:
        members_str: Comma-separated string of members with IDs

    Returns:
        list: Player IDs (as strings)
    """
    if pd.isna(members_str) or not members_str:
        return []

    # Extract all IDs using regex
    pattern = r'#(\d+)'
    ids = re.findall(pattern, str(members_str))
    return ids


def analyze_party_size_patterns(reservations):
    """
    Analyze party size patterns and group vs. solo play.

    Args:
        reservations: DataFrame with reservation records

    Returns:
        dict: Party size analysis results
    """
    print("\nAnalyzing party size patterns...")

    # Parse members field to get party IDs
    reservations['party_ids'] = reservations['members'].apply(parse_members_field)
    reservations['party_size'] = reservations['party_ids'].apply(len)

    # Filter to valid reservations (party_size > 0)
    valid_reservations = reservations[reservations['party_size'] > 0].copy()

    if len(valid_reservations) == 0:
        print("  Warning: No valid party data found")
        return None

    # Party size distribution
    party_size_dist = valid_reservations['party_size'].value_counts().sort_index()

    # Solo vs. group players
    solo_count = (valid_reservations['party_size'] == 1).sum()
    group_count = (valid_reservations['party_size'] > 1).sum()

    # Average party size
    avg_party_size = valid_reservations['party_size'].mean()
    median_party_size = valid_reservations['party_size'].median()

    # Most common party sizes
    top_party_sizes = party_size_dist.head(5)

    print(f"\nParty Size Overview:")
    print(f"  Average party size: {avg_party_size:.2f}")
    print(f"  Median party size: {median_party_size:.0f}")
    print(f"  Solo reservations: {solo_count:,} ({solo_count/len(valid_reservations)*100:.1f}%)")
    print(f"  Group reservations: {group_count:,} ({group_count/len(valid_reservations)*100:.1f}%)")

    return {
        'party_size_distribution': party_size_dist.to_dict(),
        'avg_party_size': float(avg_party_size),
        'median_party_size': float(median_party_size),
        'solo_count': int(solo_count),
        'group_count': int(group_count),
        'total_valid_reservations': int(len(valid_reservations)),
        'top_party_sizes': top_party_sizes.to_dict(),
        'valid_reservations_df': valid_reservations
    }


def analyze_social_network(reservations_df):
    """
    Analyze social network connections between players.

    Args:
        reservations_df: DataFrame with parsed party_ids

    Returns:
        dict: Social network metrics
    """
    print("\nAnalyzing social network connections...")

    # Build co-play matrix (who plays with whom)
    connections = defaultdict(Counter)

    for _, row in reservations_df.iterrows():
        party = row['party_ids']
        if len(party) > 1:
            # Record all pairwise connections
            for i, player_a in enumerate(party):
                for player_b in party[i+1:]:
                    connections[player_a][player_b] += 1
                    connections[player_b][player_a] += 1

    if not connections:
        print("  Warning: No social connections found")
        return None

    # Calculate metrics for each player
    player_metrics = []
    for player_id, partners in connections.items():
        total_connections = sum(partners.values())
        unique_partners = len(partners)
        most_frequent_partner = partners.most_common(1)[0] if partners else (None, 0)

        player_metrics.append({
            'player_id': player_id,
            'total_connections': total_connections,
            'unique_partners': unique_partners,
            'most_frequent_partner': most_frequent_partner[0],
            'most_frequent_count': most_frequent_partner[1]
        })

    network_df = pd.DataFrame(player_metrics)

    # Identify community hubs (most connected players)
    top_connectors = network_df.nlargest(20, 'total_connections')

    # Calculate network density
    total_unique_players = len(connections)
    total_connections = network_df['total_connections'].sum() / 2  # Divide by 2 (bidirectional)

    print(f"\nSocial Network Metrics:")
    print(f"  Total connected players: {total_unique_players:,}")
    print(f"  Total connections: {int(total_connections):,}")
    print(f"  Average connections per player: {network_df['total_connections'].mean():.1f}")
    print(f"  Average unique partners: {network_df['unique_partners'].mean():.1f}")

    return {
        'network_df': network_df,
        'top_connectors': top_connectors,
        'total_unique_players': int(total_unique_players),
        'total_connections': int(total_connections),
        'avg_connections_per_player': float(network_df['total_connections'].mean()),
        'avg_unique_partners': float(network_df['unique_partners'].mean()),
        'connections_dict': connections
    }


def create_party_size_visualization(party_results, network_results, output_path):
    """
    Create visualization of party size and social network patterns.

    Args:
        party_results: Party size analysis results
        network_results: Social network analysis results
        output_path: Path to save visualization PNG
    """
    print("\nCreating party size and social network visualization...")

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # Chart 1: Party size distribution
    party_dist = pd.Series(party_results['party_size_distribution']).sort_index()
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(party_dist)))

    ax1.bar(party_dist.index, party_dist.values, color=colors, edgecolor='black', linewidth=1.5)
    ax1.set_xlabel('Party Size', fontsize=12)
    ax1.set_ylabel('Number of Reservations', fontsize=12)
    ax1.set_title('Party Size Distribution', fontsize=14, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)

    for i, (size, count) in enumerate(party_dist.items()):
        ax1.text(size, count + max(party_dist) * 0.02, f'{count:,}', ha='center', fontsize=9, fontweight='bold')

    # Chart 2: Solo vs. Group play (pie chart)
    labels = ['Solo Players', 'Group Players']
    sizes = [party_results['solo_count'], party_results['group_count']]
    colors_pie = ['#FF6B6B', '#4ECDC4']
    explode = (0.05, 0)

    wedges, texts, autotexts = ax2.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        colors=colors_pie,
        explode=explode,
        startangle=90,
        textprops={'fontsize': 12, 'fontweight': 'bold'}
    )
    ax2.set_title('Solo vs. Group Play', fontsize=14, fontweight='bold')

    # Chart 3: Top 20 most connected players (social hubs)
    if network_results and network_results['top_connectors'] is not None:
        top_20 = network_results['top_connectors'].head(20)
        colors_bar = plt.cm.Greens(np.linspace(0.5, 0.9, len(top_20)))

        ax3.barh(range(len(top_20)), top_20['total_connections'].values, color=colors_bar,
                edgecolor='black', linewidth=1)
        ax3.set_yticks(range(len(top_20)))
        ax3.set_yticklabels([f"Player {pid}" for pid in top_20['player_id']], fontsize=8)
        ax3.set_xlabel('Total Connections (Co-Play Count)', fontsize=12)
        ax3.set_title('Top 20 Most Connected Players (Community Hubs)', fontsize=14, fontweight='bold')
        ax3.invert_yaxis()
        ax3.grid(axis='x', alpha=0.3)

        for i, val in enumerate(top_20['total_connections'].values):
            ax3.text(val + max(top_20['total_connections']) * 0.02, i, f'{val:.0f}',
                    va='center', fontsize=8)
    else:
        ax3.text(0.5, 0.5, 'Social network data not available', ha='center', va='center', fontsize=14)
        ax3.axis('off')

    # Chart 4: Unique partners distribution (histogram)
    if network_results and network_results['network_df'] is not None:
        network_df = network_results['network_df']

        ax4.hist(network_df['unique_partners'], bins=30, color='steelblue', edgecolor='black', alpha=0.7)
        ax4.axvline(network_df['unique_partners'].mean(), color='red', linestyle='--',
                   linewidth=2, label=f"Mean: {network_df['unique_partners'].mean():.1f}")
        ax4.axvline(network_df['unique_partners'].median(), color='green', linestyle='--',
                   linewidth=2, label=f"Median: {network_df['unique_partners'].median():.1f}")
        ax4.set_xlabel('Number of Unique Playing Partners', fontsize=12)
        ax4.set_ylabel('Number of Players', fontsize=12)
        ax4.set_title('Unique Playing Partners Distribution', fontsize=14, fontweight='bold')
        ax4.legend()
        ax4.grid(axis='y', alpha=0.3)
    else:
        ax4.text(0.5, 0.5, 'Partner distribution data not available', ha='center', va='center', fontsize=14)
        ax4.axis('off')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Visualization saved to {output_path}")
    plt.close()


def generate_narrative_insights(party_results, network_results):
    """
    Generate narrative insights from party size and social network analysis.

    Args:
        party_results: Party size analysis results
        network_results: Social network analysis results

    Returns:
        str: Narrative insights text
    """
    print("\nGenerating narrative insights...")

    pr = party_results
    nr = network_results if network_results else {}

    narrative = f"""
## Party Size and Social Network Analysis

**Party Size Patterns:**
- **Average party size:** {pr['avg_party_size']:.2f} players
- **Median party size:** {pr['median_party_size']:.0f} players
- **Solo reservations:** {pr['solo_count']:,} ({pr['solo_count']/pr['total_valid_reservations']*100:.1f}%)
- **Group reservations:** {pr['group_count']:,} ({pr['group_count']/pr['total_valid_reservations']*100:.1f}%)

**Most Common Party Sizes:**
"""

    for size, count in pr['top_party_sizes'].items():
        pct = count / pr['total_valid_reservations'] * 100
        narrative += f"- **{size} players:** {count:,} reservations ({pct:.1f}%)\n"

    if nr:
        narrative += f"""
**Social Network Insights:**
- **Total connected players:** {nr['total_unique_players']:,}
- **Total co-play connections:** {nr['total_connections']:,}
- **Average connections per player:** {nr['avg_connections_per_player']:.1f}
- **Average unique partners:** {nr['avg_unique_partners']:.1f}

**Community Structure:**
- Players with most connections are **community hubs**
- High unique partner count = social butterflies (play with many different people)
- Low partner count but high connections = tight-knit cliques
"""

    narrative += f"""
**Strategic Applications:**

1. **Community Building:**
   - Identify and empower community hubs (top connected players)
   - Host social events to connect solo players with groups
   - Recognize "social butterflies" who integrate new members

2. **Programming Mix:**
   - Solo players ({pr['solo_count']/pr['total_valid_reservations']*100:.1f}%) need matchmaking services
   - Group players ({pr['group_count']/pr['total_valid_reservations']*100:.1f}%) prefer reserved court blocks
   - Create "looking for partners" bulletin board

3. **Retention Strategy:**
   - Players with strong social connections have higher retention
   - New member onboarding: Introduce to community hubs
   - Track "social isolation" risk (players with few connections)

4. **Event Design:**
   - Average party size {pr['avg_party_size']:.2f} suggests optimal event capacity
   - Social mixers should accommodate groups of {pr['median_party_size']:.0f}
   - Consider "bring a friend" promotions for solo players

5. **Pricing Strategy:**
   - Solo players may prefer pay-per-use (less commitment)
   - Group players likely to buy memberships (regular play)
   - Consider "group discount" for parties of 4+

6. **Referral Programs:**
   - Community hubs are natural brand ambassadors
   - Target top {nr['total_unique_players'] if nr else 0} connected players for referral incentives
   - "Play with 5 new partners" challenge to increase network density
"""

    print(narrative)
    return narrative


def main():
    """Main execution function."""
    # Output paths
    visualization_output = 'deliverables/visualizations/party_size_social_network.png'
    data_output = 'deliverables/data/party_size_social_network.json'

    try:
        # Load data
        reservations = load_reservation_data()

        # Analyze party size patterns
        party_results = analyze_party_size_patterns(reservations)

        if not party_results:
            print("\n⚠️  No valid party size data available")
            sys.exit(1)

        # Analyze social network
        network_results = analyze_social_network(party_results['valid_reservations_df'])

        # Create visualization
        create_party_size_visualization(party_results, network_results, visualization_output)

        # Generate narrative insights
        narrative = generate_narrative_insights(party_results, network_results)

        # Prepare results for JSON (remove DataFrames)
        party_results_json = {
            'party_size_distribution': party_results['party_size_distribution'],
            'avg_party_size': party_results['avg_party_size'],
            'median_party_size': party_results['median_party_size'],
            'solo_count': party_results['solo_count'],
            'group_count': party_results['group_count'],
            'total_valid_reservations': party_results['total_valid_reservations'],
            'top_party_sizes': party_results['top_party_sizes']
        }

        network_results_json = None
        if network_results:
            # Get top 100 connectors for JSON
            top_100 = network_results['network_df'].nlargest(100, 'total_connections')
            network_results_json = {
                'total_unique_players': network_results['total_unique_players'],
                'total_connections': network_results['total_connections'],
                'avg_connections_per_player': network_results['avg_connections_per_player'],
                'avg_unique_partners': network_results['avg_unique_partners'],
                'top_100_connectors': top_100.to_dict('records')
            }

        combined_results = {
            'party_size_analysis': party_results_json,
            'social_network_analysis': network_results_json,
            'narrative': narrative
        }

        with open(data_output, 'w') as f:
            json.dump(combined_results, f, indent=2, default=str)
        print(f"\nData results saved to {data_output}")

        print("\n✅ Party size and social network analysis complete!")
        print(f"   - Visualization: {visualization_output}")
        print(f"   - Data: {data_output}")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
