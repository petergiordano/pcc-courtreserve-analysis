#!/usr/bin/env python3
"""
Generate stakeholder charts for PCC Customer Intelligence deliverables.

This script generates 4 publication-quality visualizations:
1. Membership Gap - Current vs Goal
2. Party Size Distribution - Group vs Solo bookings
3. Frequency Comparison - Members vs Non-Members visit patterns
4. Segment Distribution - 5 behavioral segments

Author: Claude Code (Anthropic)
Date: October 29, 2025
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# Set working directory to deliverables/
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / 'data'
CHARTS_DIR = SCRIPT_DIR / 'charts'

# Ensure charts directory exists
CHARTS_DIR.mkdir(exist_ok=True)

print("=" * 80)
print("GENERATING STAKEHOLDER CHARTS")
print("=" * 80)

# ==============================================================================
# Chart 1: Membership Gap
# ==============================================================================
print("\n1. Generating Membership Gap chart...")

fig, ax = plt.subplots(figsize=(10, 6))
categories = ['Current\nMembers', 'Goal']
values = [240, 400]
colors = ['#dd1e28', '#0072bb']

bars = ax.bar(categories, values, color=colors, width=0.5)

# Add value labels
for bar in bars:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}',
            ha='center', va='bottom', fontsize=18, fontweight='bold')

# Add gap annotation
ax.annotate('', xy=(1, 240), xytext=(1, 400),
            arrowprops=dict(arrowstyle='<->', color='#323F54', lw=2))
ax.text(1.15, 320, 'Gap: 160\nmembers', fontsize=14, color='#323F54', fontweight='bold')

ax.set_ylabel('Number of Members', fontsize=14, fontweight='bold')
ax.set_title('The Membership Gap', fontsize=18, fontweight='bold', pad=20)
ax.set_ylim(0, 450)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig(CHARTS_DIR / 'membership-gap.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"   ✓ Saved: {CHARTS_DIR / 'membership-gap.png'}")

# ==============================================================================
# Chart 2: Party Size Distribution
# ==============================================================================
print("\n2. Generating Party Size Distribution chart...")

with open(DATA_DIR / 'party_size_social_network.json', 'r') as f:
    data = json.load(f)

party_dist = data['party_size_analysis']['party_size_distribution']
solo = party_dist.get('1', 0)
total = data['party_size_analysis']['total_valid_reservations']
groups = total - solo

fig, ax = plt.subplots(figsize=(10, 6))
labels = ['Solo Players', 'Group Bookings']
sizes = [solo, groups]
colors = ['#dd1e28', '#0072bb']
explode = (0.05, 0)

wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                    startangle=90, explode=explode, textprops={'fontsize': 14})
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontweight('bold')
    autotext.set_fontsize(16)

ax.set_title('92% of Reservations are Group Bookings\n(Average 9 people per reservation)',
             fontsize=16, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig(CHARTS_DIR / 'party-size-distribution.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"   ✓ Saved: {CHARTS_DIR / 'party-size-distribution.png'}")

# ==============================================================================
# Chart 3: Frequency Comparison (Members vs Non-Members)
# ==============================================================================
print("\n3. Generating Frequency Comparison chart...")

members = pd.read_csv(DATA_DIR / 'frequency_summary_members.csv')
nonmembers = pd.read_csv(DATA_DIR / 'frequency_summary_nonmembers.csv')

# Merge on frequency_segment to handle different lengths
# Use outer merge and fill missing values with 0
all_segments = pd.merge(
    members[['frequency_segment', 'avg_visits_per_month']],
    nonmembers[['frequency_segment', 'avg_visits_per_month']],
    on='frequency_segment',
    how='outer',
    suffixes=('_members', '_nonmembers')
).fillna(0)

fig, ax = plt.subplots(figsize=(12, 6))

x = range(len(all_segments))
width = 0.35

bars1 = ax.bar([i - width/2 for i in x], all_segments['avg_visits_per_month_members'],
               width, label='Members', color='#0072bb')
bars2 = ax.bar([i + width/2 for i in x], all_segments['avg_visits_per_month_nonmembers'],
               width, label='Non-Members', color='#dd1e28')

ax.set_xlabel('Frequency Segment', fontsize=12, fontweight='bold')
ax.set_ylabel('Average Visits per Month', fontsize=12, fontweight='bold')
ax.set_title('Visit Frequency: Members vs Non-Members', fontsize=16, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(all_segments['frequency_segment'], fontsize=11)
ax.legend(fontsize=12)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Add value labels
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        if height > 0:  # Only show label if non-zero
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig(CHARTS_DIR / 'frequency-comparison.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"   ✓ Saved: {CHARTS_DIR / 'frequency-comparison.png'}")

# ==============================================================================
# Chart 4: Segment Distribution
# ==============================================================================
print("\n4. Generating Segment Distribution chart...")

with open(DATA_DIR / 'rule_based_segments.json', 'r') as f:
    data = json.load(f)

segments = data['segment_distribution']

fig, ax = plt.subplots(figsize=(10, 6))
labels = list(segments.keys())
sizes = list(segments.values())
colors = ['#dd1e28', '#0072bb', '#324158', '#323F54', '#9ca3af']

wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors[:len(sizes)],
                                    autopct='%1.1f%%', startangle=90,
                                    textprops={'fontsize': 11})
for autotext in autotexts:
    autotext.set_color('white')
    autotext.set_fontweight('bold')
    autotext.set_fontsize(12)

# Add count labels
for i, (label, size) in enumerate(zip(labels, sizes)):
    angle = (wedges[i].theta2 + wedges[i].theta1) / 2
    x = 1.3 * np.cos(np.radians(angle))
    y = 1.3 * np.sin(np.radians(angle))
    ax.text(x, y, f'n={size}', ha='center', va='center', fontsize=10, fontweight='bold')

ax.set_title('Five Behavioral Segments Discovered\n(Total: 2,575 Players)',
             fontsize=16, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig(CHARTS_DIR / 'segment-distribution.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"   ✓ Saved: {CHARTS_DIR / 'segment-distribution.png'}")

# ==============================================================================
# Summary
# ==============================================================================
print("\n" + "=" * 80)
print("CHART GENERATION COMPLETE")
print("=" * 80)
print(f"\nGenerated 4 charts in: {CHARTS_DIR}")
print("\nFiles created:")
print("  • membership-gap.png")
print("  • party-size-distribution.png")
print("  • frequency-comparison.png")
print("  • segment-distribution.png")
print("\nAll charts saved at 300 DPI (publication quality)")
print("=" * 80)
