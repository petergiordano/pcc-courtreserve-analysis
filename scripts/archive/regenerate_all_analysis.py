#!/usr/bin/env python3
"""
Master Analysis Runner - Regenerate All Deliverables
Runs complete analysis suite using SQLite database.

This script executes all analysis scripts in the correct order and generates
fresh deliverables with the latest CourtReserve data.

Author: Claude Code (Anthropic)
Date: October 27, 2025
"""

import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

# Analysis scripts in execution order
ANALYSIS_SCRIPTS = [
    # Core JTBD analysis (K-Means clustering, context switching)
    {
        'name': 'JTBD Clustering Analysis',
        'script': 'analyze_courtreserve_jtbd.py',
        'outputs': [
            'deliverables/visualizations/segment_clusters.png',
            'deliverables/visualizations/segment_distribution.png',
            'deliverables/visualizations/booking_time_heatmaps.png',
            'deliverables/data/jtbd_analysis_results.json'
        ],
        'status': 'PENDING'
    },

    # Rule-based segmentation (ChatGPT's 5 behavioral clusters)
    {
        'name': 'Rule-Based Segmentation',
        'script': 'analyze_rule_based_segments.py',
        'outputs': [
            'deliverables/visualizations/rule_based_segments.png',
            'deliverables/data/rule_based_segments.json'
        ],
        'status': 'PENDING'
    },

    # Pay-per-use conversion analysis
    {
        'name': 'Pay-Per-Use Segment Analysis',
        'script': 'analyze_pay_per_use_segment.py',
        'outputs': [
            'deliverables/visualizations/pay_per_use_segment.png',
            'deliverables/data/pay_per_use_insights.txt'
        ],
        'status': 'PENDING'
    },

    # Shadow market capacity analysis
    {
        'name': 'Shadow Market Heatmap',
        'script': 'analyze_shadow_market_heatmap.py',
        'outputs': [
            'deliverables/visualizations/shadow_market_heatmap.png',
            'deliverables/data/shadow_market_insights.txt'
        ],
        'status': 'PENDING'
    },

    # Daypart pattern analysis
    {
        'name': 'Daypart Patterns Analysis',
        'script': 'analyze_daypart_patterns.py',
        'outputs': [
            'deliverables/visualizations/daypart_heatmap.png',
            'deliverables/data/daypart_analysis.json'
        ],
        'status': 'PENDING'
    },

    # Event fill rate analysis
    {
        'name': 'Event Fill Rates Analysis',
        'script': 'analyze_event_fill_rates.py',
        'outputs': [
            'deliverables/visualizations/event_fill_rates.png',
            'deliverables/data/event_performance.json'
        ],
        'status': 'PENDING'
    },

    # Engagement friction metrics
    {
        'name': 'Engagement Friction Analysis',
        'script': 'analyze_engagement_friction.py',
        'outputs': [
            'deliverables/visualizations/friction_metrics.png',
            'deliverables/data/friction_analysis.json'
        ],
        'status': 'PENDING'
    },

    # Transaction-based WTP analysis (NEW - 29K transactions!)
    {
        'name': 'Transaction WTP Analysis',
        'script': 'analyze_transaction_details.py',
        'outputs': [
            'deliverables/visualizations/transaction_wtp.png',
            'deliverables/data/wtp_analysis.json'
        ],
        'status': 'PENDING'
    },

    # Party size & social network analysis
    {
        'name': 'Social Network Analysis',
        'script': 'analyze_party_size_guests.py',
        'outputs': [
            'deliverables/visualizations/social_network.png',
            'deliverables/data/social_dynamics.json'
        ],
        'status': 'PENDING'
    }
]


def print_header():
    """Print header with timestamp."""
    print("=" * 80)
    print("COURTRESERVE ANALYSIS SUITE - COMPLETE REGENERATION")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: courtreserve.db")
    print(f"Scripts to run: {len(ANALYSIS_SCRIPTS)}")
    print("=" * 80)
    print()


def print_summary(results):
    """Print execution summary."""
    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)

    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    failed_count = sum(1 for r in results if r['status'] == 'FAILED')
    total_time = sum(r.get('duration', 0) for r in results)

    print(f"\nTotal scripts: {len(results)}")
    print(f"✓ Successful:  {success_count}")
    print(f"✗ Failed:      {failed_count}")
    print(f"Total time:    {total_time:.1f} seconds")
    print()

    # Show individual results
    for result in results:
        status_symbol = "✓" if result['status'] == 'SUCCESS' else "✗"
        duration = result.get('duration', 0)
        print(f"{status_symbol} {result['name']:40s} ({duration:.1f}s)")

    # Show output files
    if success_count > 0:
        print("\n" + "=" * 80)
        print("GENERATED DELIVERABLES")
        print("=" * 80)
        print("\nVisualizations:")
        vis_files = Path('deliverables/visualizations').glob('*.png')
        for f in sorted(vis_files):
            print(f"  - {f}")

        print("\nData Files:")
        data_files = list(Path('deliverables/data').glob('*.json')) + \
                     list(Path('deliverables/data').glob('*.txt'))
        for f in sorted(data_files):
            print(f"  - {f}")

    print("=" * 80)


def run_script(script_info):
    """
    Run a single analysis script.

    Args:
        script_info: Dictionary with script metadata

    Returns:
        Dictionary with execution results
    """
    script_path = Path('scripts') / script_info['script']

    print(f"\n{'─' * 80}")
    print(f"Running: {script_info['name']}")
    print(f"Script:  {script_info['script']}")
    print(f"{'─' * 80}")

    if not script_path.exists():
        print(f"⚠️  Script not found: {script_path}")
        print(f"   Skipping...")
        return {
            **script_info,
            'status': 'SKIPPED',
            'message': 'Script not yet implemented',
            'duration': 0
        }

    start_time = time.time()

    try:
        # Run script with subprocess
        result = subprocess.run(
            ['python3', str(script_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per script
        )

        duration = time.time() - start_time

        if result.returncode == 0:
            print(f"✓ Completed successfully in {duration:.1f} seconds")
            return {
                **script_info,
                'status': 'SUCCESS',
                'duration': duration,
                'stdout': result.stdout
            }
        else:
            print(f"✗ Failed with return code {result.returncode}")
            print(f"\nError output:")
            print(result.stderr)
            return {
                **script_info,
                'status': 'FAILED',
                'duration': duration,
                'error': result.stderr
            }

    except subprocess.TimeoutExpired:
        print(f"✗ Script timed out after 300 seconds")
        return {
            **script_info,
            'status': 'FAILED',
            'duration': 300,
            'error': 'Timeout after 300 seconds'
        }

    except Exception as e:
        print(f"✗ Exception: {str(e)}")
        return {
            **script_info,
            'status': 'FAILED',
            'duration': time.time() - start_time,
            'error': str(e)
        }


def main():
    """Main execution function."""
    print_header()

    # Ensure deliverables directories exist
    Path('deliverables/visualizations').mkdir(parents=True, exist_ok=True)
    Path('deliverables/data').mkdir(parents=True, exist_ok=True)
    Path('deliverables/reports').mkdir(parents=True, exist_ok=True)

    # Run all scripts
    results = []
    for script_info in ANALYSIS_SCRIPTS:
        result = run_script(script_info)
        results.append(result)

        # Stop if critical script fails (JTBD clustering is foundation)
        if result['status'] == 'FAILED' and script_info['script'] == 'analyze_courtreserve_jtbd.py':
            print("\n" + "!" * 80)
            print("CRITICAL ERROR: JTBD clustering failed. Stopping execution.")
            print("!" * 80)
            break

    # Print summary
    print_summary(results)

    # Return exit code based on results
    failed_count = sum(1 for r in results if r['status'] == 'FAILED')
    if failed_count > 0:
        print(f"\n⚠️  {failed_count} script(s) failed. Review errors above.")
        return 1
    else:
        print("\n✓ All scripts completed successfully!")
        print("\nNext steps:")
        print("  1. Review visualizations in deliverables/visualizations/")
        print("  2. Check data outputs in deliverables/data/")
        print("  3. Generate reports with updated findings")
        return 0


if __name__ == '__main__':
    sys.exit(main())
