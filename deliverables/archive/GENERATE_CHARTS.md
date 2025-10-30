# Chart Generation Instructions for Claude Code

## Setup
```bash
cd /Users/petergiordano/Documents/GitHub/pcc-courtreserve-analysis/deliverables
pip install matplotlib pandas seaborn
```

## Chart 1: Membership Gap
**File**: `charts/membership-gap.png`
**Data**: Manual (current: ~240, goal: 400, gap: 160)
**Type**: Bar chart with two bars

```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

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
ax.spines('right').set_visible(False)
plt.tight_layout()
plt.savefig('charts/membership-gap.png', dpi=300, bbox_inches='tight')
plt.close()
```

## Chart 2: Party Size Distribution
**File**: `charts/party-size-distribution.png`
**Data**: `data/party_size_social_network.json`

```python
import json
import matplotlib.pyplot as plt

with open('data/party_size_social_network.json', 'r') as f:
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
plt.savefig('charts/party-size-distribution.png', dpi=300, bbox_inches='tight')
plt.close()
```

## Chart 3: Frequency Comparison (Members vs Non-Members)
**File**: `charts/frequency-comparison.png`
**Data**: `data/frequency_summary_members.csv` and `data/frequency_summary_nonmembers.csv`

```python
import pandas as pd
import matplotlib.pyplot as plt

members = pd.read_csv('data/frequency_summary_members.csv')
nonmembers = pd.read_csv('data/frequency_summary_nonmembers.csv')

fig, ax = plt.subplots(figsize=(12, 6))

x = range(len(members))
width = 0.35

bars1 = ax.bar([i - width/2 for i in x], members['avg_visits_per_month'], 
               width, label='Members', color='#0072bb')
bars2 = ax.bar([i + width/2 for i in x], nonmembers['avg_visits_per_month'], 
               width, label='Non-Members', color='#dd1e28')

ax.set_xlabel('Frequency Segment', fontsize=12, fontweight='bold')
ax.set_ylabel('Average Visits per Month', fontsize=12, fontweight='bold')
ax.set_title('Visit Frequency: Members vs Non-Members', fontsize=16, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(members['frequency_segment'], fontsize=11)
ax.legend(fontsize=12)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Add value labels
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('charts/frequency-comparison.png', dpi=300, bbox_inches='tight')
plt.close()
```

## Chart 4: Segment Distribution
**File**: `charts/segment-distribution.png`
**Data**: `data/rule_based_segments.json`

```python
import json
import matplotlib.pyplot as plt

with open('data/rule_based_segments.json', 'r') as f:
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
plt.savefig('charts/segment-distribution.png', dpi=300, bbox_inches='tight')
plt.close()
```

## Run All Charts
```python
import numpy as np  # Add this at top for segment distribution chart
# Run all 4 chart generation blocks above
print("✓ Charts generated in deliverables/charts/")
```

## Expected Output
- `charts/membership-gap.png`
- `charts/party-size-distribution.png`
- `charts/frequency-comparison.png`
- `charts/segment-distribution.png`
