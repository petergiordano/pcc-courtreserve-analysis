#!/usr/bin/env python3
"""
CourtReserve JTBD Customer Segmentation Analysis
Pickleball Clubhouse Chicago - Customer Intelligence Center

Analyzes customer behavior across multiple data sources to identify
Jobs-to-be-Done segments based on:
1. Same JTBD (progress they're trying to make)
2. Same Value Preferences (how they measure success)
3. Same Willingness-to-Pay (what they'll spend)

Author: Claude Code (Anthropic)
Date: October 26, 2025
"""

import pandas as pd
import numpy as np
import json
import warnings
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict, Counter

# Machine learning and clustering
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, davies_bouldin_score

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings('ignore')

# Set style for visualizations
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (12, 8)

class JTBDAnalyzer:
    """
    Analyzes CourtReserve data to identify JTBD customer segments.
    """

    def __init__(self, data_dir: str = '.'):
        """Initialize analyzer with data directory."""
        self.data_dir = Path(data_dir)
        self.reservations = None
        self.members = None
        self.transactions = None
        self.cancellations = None
        self.events = None
        self.checkins = None

        # Analysis results
        self.customer_features = None
        self.segments = None
        self.context_switchers = None

    def load_data(self) -> None:
        """Load all CSV files and perform initial cleaning."""
        print("Loading data files...")

        # Load reservations
        self.reservations = pd.read_csv(
            self.data_dir / 'ReservationReport_2025-10-26_03-50-PM.csv',
            encoding='utf-8-sig'
        )
        print(f"  Loaded {len(self.reservations)} reservation records")

        # Load members
        self.members = pd.read_csv(
            self.data_dir / 'MembersReport_2025-10-26_04-58-PM.csv',
            encoding='utf-8-sig'
        )
        print(f"  Loaded {len(self.members)} member records")

        # Load transactions
        self.transactions = pd.read_csv(
            self.data_dir / 'Transactions-2025.csv',
            encoding='utf-8-sig'
        )
        print(f"  Loaded {len(self.transactions)} transaction records")

        # Load cancellations
        self.cancellations = pd.read_csv(
            self.data_dir / 'CancellationsReport_2025-10-26_09-49-PM.csv',
            encoding='utf-8-sig'
        )
        print(f"  Loaded {len(self.cancellations)} cancellation records")

        # Load events
        self.events = pd.read_csv(
            self.data_dir / 'Event_Summary.csv',
            encoding='utf-8-sig'
        )
        print(f"  Loaded {len(self.events)} event summary records")

        # Load check-ins
        self.checkins = pd.read_csv(
            self.data_dir / 'CheckinReports2025-10-26_09-55-PM.csv',
            encoding='utf-8-sig'
        )
        print(f"  Loaded {len(self.checkins)} check-in records")

        print("\nData loaded successfully!")

    def clean_data(self) -> None:
        """Clean and standardize data across all datasets."""
        print("\nCleaning data...")

        # Clean reservations
        self.reservations['Start Date / Time'] = pd.to_datetime(
            self.reservations['Start Date / Time'],
            format='%m/%d/%Y %I:%M %p',
            errors='coerce'
        )
        self.reservations['Player _#'] = self.reservations['Player _#'].str.replace('#', '').str.strip()

        # Clean members - extract member number
        self.members['Member #'] = self.members['Member #'].astype(str)

        # Clean transactions
        self.transactions['Trans. Date'] = pd.to_datetime(
            self.transactions['Trans. Date'],
            errors='coerce'
        )
        self.transactions['Member #'] = self.transactions['Member #'].astype(str)

        # Clean checkins
        self.checkins['Check-in Date/Time'] = pd.to_datetime(
            self.checkins['Check-in Date/Time'],
            format='%m/%d/%Y %I:%M %p',
            errors='coerce'
        )
        self.checkins['Player _#'] = self.checkins['Player _#'].astype(str)

        print("  Data cleaning complete")

    def engineer_features(self) -> pd.DataFrame:
        """
        Engineer behavioral features for clustering across all 3 JTBD dimensions:
        1. JTBD signals (what progress they're making)
        2. Value preference signals (how they measure success)
        3. Willingness-to-pay signals (what they'll spend)
        """
        print("\nEngineering features...")

        # Get unique members from reservations
        member_ids = self.reservations['Player _#'].dropna().unique()
        features = []

        for member_id in member_ids:
            feature_dict = self._extract_member_features(member_id)
            if feature_dict is not None:
                features.append(feature_dict)

        self.customer_features = pd.DataFrame(features)

        print(f"  Engineered {len(self.customer_features.columns)} features for {len(self.customer_features)} customers")
        print(f"  Features: {', '.join(self.customer_features.columns[:10])}...")

        return self.customer_features

    def _extract_member_features(self, member_id: str) -> Dict[str, Any]:
        """Extract all behavioral features for a single member."""

        # Get member's data
        member_reservations = self.reservations[self.reservations['Player _#'] == member_id]
        member_transactions = self.transactions[self.transactions['Member #'] == member_id]
        member_checkins = self.checkins[self.checkins['Player _#'] == member_id]
        member_info = self.members[self.members['Member #'] == member_id]

        if len(member_reservations) == 0:
            return None

        features = {'member_id': member_id}

        # === TEMPORAL PATTERNS (JTBD Context Signals) ===

        # Time of day distribution
        hours = member_reservations['Start Date / Time'].dt.hour
        features['pct_morning'] = (hours.between(6, 11).sum() / len(hours)) if len(hours) > 0 else 0
        features['pct_afternoon'] = (hours.between(12, 16).sum() / len(hours)) if len(hours) > 0 else 0
        features['pct_evening'] = (hours.between(17, 21).sum() / len(hours)) if len(hours) > 0 else 0

        # Day of week distribution
        dow = member_reservations['Start Date / Time'].dt.dayofweek
        features['pct_weekday'] = (dow.between(0, 4).sum() / len(dow)) if len(dow) > 0 else 0
        features['pct_weekend'] = ((dow == 5) | (dow == 6)).sum() / len(dow) if len(dow) > 0 else 0

        # Consistency (variance in booking times)
        features['time_consistency'] = 1 / (hours.std() + 1) if len(hours) > 1 else 0
        features['day_consistency'] = 1 / (dow.std() + 1) if len(dow) > 1 else 0

        # === SOCIAL PATTERNS (Value Preference Signals) ===

        # Partner variety
        all_members_field = member_reservations['Members'].dropna()
        unique_partners = set()
        for members_str in all_members_field:
            # Extract member IDs from format "Name (#ID), Name2 (#ID2)"
            import re
            partner_ids = re.findall(r'#(\d+)', str(members_str))
            unique_partners.update([p for p in partner_ids if p != member_id])

        features['unique_partners'] = len(unique_partners)
        features['partner_variety_rate'] = len(unique_partners) / len(member_reservations) if len(member_reservations) > 0 else 0

        # Party size patterns
        features['avg_party_size'] = member_reservations['Members Count'].mean()
        features['solo_rate'] = (member_reservations['Members Count'] == 1).sum() / len(member_reservations)

        # Guest booking rate (bringing new people)
        features['guest_booking_rate'] = member_reservations['Guests'].notna().sum() / len(member_reservations)

        # === EVENT PARTICIPATION (Value Dimension Signals) ===

        # Event attendance
        event_bookings = member_reservations[member_reservations['Is Event?'] == 'TRUE']
        features['event_participation_rate'] = len(event_bookings) / len(member_reservations) if len(member_reservations) > 0 else 0
        features['total_events'] = len(event_bookings)

        # Event type analysis
        event_names = event_bookings['Event Name'].fillna('').str.lower()
        features['drills_events'] = event_names.str.contains('drill|skill', case=False).sum()
        features['social_events'] = event_names.str.contains('social|mixer|open play', case=False).sum()
        features['competitive_events'] = event_names.str.contains('tournament|advanced|expert', case=False).sum()

        # === ENGAGEMENT METRICS ===

        # Booking frequency (extrapolate to monthly)
        date_range = (member_reservations['Start Date / Time'].max() -
                     member_reservations['Start Date / Time'].min()).days + 1
        features['bookings_per_month'] = (len(member_reservations) / date_range * 30) if date_range > 0 else 0
        features['total_bookings'] = len(member_reservations)

        # Check-in engagement
        if len(member_checkins) > 0:
            checked_in = (member_checkins['Check-In Status'] == 'Checked-In').sum()
            features['check_in_rate'] = checked_in / len(member_checkins) if len(member_checkins) > 0 else 0

            # Early arrival (proxy for social JTBD)
            # TODO: Calculate time difference between check-in and reservation start
            features['has_checkin_data'] = 1
        else:
            features['check_in_rate'] = 0
            features['has_checkin_data'] = 0

        # === WILLINGNESS-TO-PAY INDICATORS ===

        # Spending behavior
        if len(member_transactions) > 0:
            features['total_spend'] = member_transactions['Total'].sum()
            features['avg_transaction'] = member_transactions['Total'].mean()
            features['spend_per_booking'] = features['total_spend'] / len(member_reservations) if len(member_reservations) > 0 else 0
        else:
            features['total_spend'] = 0
            features['avg_transaction'] = 0
            features['spend_per_booking'] = 0

        # Membership tier (from members data)
        if len(member_info) > 0:
            membership = member_info.iloc[0]['Current Membership']
            features['membership_tier'] = self._encode_membership_tier(membership)
            features['total_paid'] = member_info.iloc[0]['Total Paid']

            # DUPR (skill level)
            dupr_singles = member_info.iloc[0].get('DUPR - Singles', None)
            dupr_doubles = member_info.iloc[0].get('DUPR - Doubles', None)
            features['dupr_level'] = self._parse_dupr(dupr_singles, dupr_doubles)
        else:
            features['membership_tier'] = 0
            features['total_paid'] = 0
            features['dupr_level'] = 0

        # Reservation type preferences (organized vs. drop-in)
        res_types = member_reservations['Reservation Type'].fillna('')
        features['organized_bookings_rate'] = res_types.str.contains('Doubles.*Add Players Now', case=False).sum() / len(member_reservations)
        features['dropsin_rate'] = res_types.str.contains('drop', case=False).sum() / len(member_reservations)

        # Payment behavior
        paid_bookings = member_reservations[member_reservations['Payment Status'].isin(['Paid', 'Partially Paid'])]
        features['payment_rate'] = len(paid_bookings) / len(member_reservations) if len(member_reservations) > 0 else 0

        return features

    def _encode_membership_tier(self, membership: str) -> int:
        """Convert membership tier to numeric value (proxy for WTP)."""
        if pd.isna(membership):
            return 0
        membership_lower = str(membership).lower()
        if 'founder' in membership_lower:
            return 5
        elif 'fanatic' in membership_lower or 'annual' in membership_lower:
            return 4
        elif 'fight club' in membership_lower or 'family' in membership_lower:
            return 3
        elif 'individual' in membership_lower or 'membership' in membership_lower:
            return 2
        elif 'coach' in membership_lower or 'employee' in membership_lower:
            return 2
        else:  # Non-member/Visitor
            return 1

    def _parse_dupr(self, singles, doubles) -> float:
        """Parse DUPR rating, preferring doubles over singles."""
        try:
            if pd.notna(doubles) and doubles != '':
                return float(doubles)
            elif pd.notna(singles) and singles != '':
                return float(singles)
        except:
            pass
        return 0.0

    def cluster_customers(self, n_clusters_range: Tuple[int, int] = (3, 8)) -> Dict[str, Any]:
        """
        Run multiple clustering algorithms to discover natural segments.

        Returns dictionary with clustering results and metrics.
        """
        print("\nRunning clustering analysis...")

        # Prepare features for clustering (exclude non-numeric and ID columns)
        numeric_cols = [col for col in self.customer_features.columns
                       if col != 'member_id' and self.customer_features[col].dtype in [np.float64, np.int64]]

        X = self.customer_features[numeric_cols].fillna(0)

        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Try different numbers of clusters
        best_kmeans = None
        best_score = -1
        best_k = None

        print("\n  Testing K-Means with different cluster counts...")
        for k in range(n_clusters_range[0], n_clusters_range[1] + 1):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X_scaled)

            if len(set(labels)) > 1:  # Need at least 2 clusters for silhouette
                score = silhouette_score(X_scaled, labels)
                print(f"    k={k}: silhouette={score:.3f}, inertia={kmeans.inertia_:.1f}")

                if score > best_score:
                    best_score = score
                    best_kmeans = kmeans
                    best_k = k

        print(f"\n  Best K-Means: k={best_k}, silhouette={best_score:.3f}")

        # Use best K-Means result
        self.customer_features['cluster_kmeans'] = best_kmeans.predict(X_scaled)

        # Also try DBSCAN for density-based clustering
        print("\n  Running DBSCAN...")
        dbscan = DBSCAN(eps=0.5, min_samples=5)
        self.customer_features['cluster_dbscan'] = dbscan.fit_predict(X_scaled)
        n_dbscan_clusters = len(set(self.customer_features['cluster_dbscan'])) - (1 if -1 in self.customer_features['cluster_dbscan'] else 0)
        print(f"    DBSCAN found {n_dbscan_clusters} clusters (+ {(self.customer_features['cluster_dbscan'] == -1).sum()} noise points)")

        # Hierarchical clustering
        print("\n  Running Hierarchical Clustering...")
        hierarchical = AgglomerativeClustering(n_clusters=best_k)
        self.customer_features['cluster_hierarchical'] = hierarchical.fit_predict(X_scaled)

        # Use K-Means as primary clustering method
        self.customer_features['segment'] = self.customer_features['cluster_kmeans']

        # Store clustering metadata
        clustering_results = {
            'best_k': best_k,
            'silhouette_score': best_score,
            'davies_bouldin_score': davies_bouldin_score(X_scaled, self.customer_features['segment']),
            'n_customers': len(self.customer_features),
            'feature_names': numeric_cols,
            'scaler': scaler,
            'model': best_kmeans
        }

        print(f"\nClustering complete: {best_k} segments discovered")

        return clustering_results

    def profile_segments(self) -> Dict[int, Dict[str, Any]]:
        """
        Create detailed profiles for each discovered segment.
        """
        print("\nProfiling segments...")

        segments = {}

        for segment_id in sorted(self.customer_features['segment'].unique()):
            segment_data = self.customer_features[self.customer_features['segment'] == segment_id]

            profile = {
                'segment_id': int(segment_id),
                'size': len(segment_data),
                'pct_of_total': len(segment_data) / len(self.customer_features) * 100,
                'member_ids': segment_data['member_id'].tolist()[:10],  # Sample
                'behavioral_signature': {},
                'jtbd_hypothesis': None,
                'confidence': 'medium',
                'unmet_needs': []
            }

            # Calculate mean for key behavioral features
            key_features = [
                'pct_morning', 'pct_afternoon', 'pct_evening',
                'pct_weekday', 'pct_weekend',
                'partner_variety_rate', 'event_participation_rate',
                'bookings_per_month', 'spend_per_booking',
                'membership_tier', 'dupr_level',
                'organized_bookings_rate', 'drills_events', 'social_events'
            ]

            for feature in key_features:
                if feature in segment_data.columns:
                    profile['behavioral_signature'][feature] = {
                        'mean': float(segment_data[feature].mean()),
                        'std': float(segment_data[feature].std()),
                        'median': float(segment_data[feature].median())
                    }

            segments[segment_id] = profile

            print(f"  Segment {segment_id}: {len(segment_data)} customers ({profile['pct_of_total']:.1f}%)")

        self.segments = segments
        return segments

    def generate_jtbd_hypotheses(self) -> None:
        """
        Generate JTBD hypotheses for each segment based on behavioral signatures.
        Uses the 9-element JTBD framework.
        """
        print("\nGenerating JTBD hypotheses...")

        for segment_id, profile in self.segments.items():
            sig = profile['behavioral_signature']

            # Extract key patterns
            is_morning = sig.get('pct_morning', {}).get('mean', 0) > 0.5
            is_evening = sig.get('pct_evening', {}).get('mean', 0) > 0.5
            is_weekday = sig.get('pct_weekday', {}).get('mean', 0) > 0.6

            high_partner_variety = sig.get('partner_variety_rate', {}).get('mean', 0) > 0.3
            high_events = sig.get('event_participation_rate', {}).get('mean', 0) > 0.3
            high_drills = sig.get('drills_events', {}).get('mean', 0) > 2
            high_social = sig.get('social_events', {}).get('mean', 0) > 2

            high_frequency = sig.get('bookings_per_month', {}).get('mean', 0) > 8
            high_spend = sig.get('spend_per_booking', {}).get('mean', 0) > 20

            # Rule-based JTBD classification
            jtbd_statement = self._classify_jtbd(
                is_morning, is_evening, is_weekday,
                high_partner_variety, high_events, high_drills, high_social,
                high_frequency, high_spend
            )

            profile['jtbd_hypothesis'] = jtbd_statement

            print(f"  Segment {segment_id}: {jtbd_statement['name']}")

    def _classify_jtbd(self, is_morning, is_evening, is_weekday,
                       high_partner_variety, high_events, high_drills, high_social,
                       high_frequency, high_spend) -> Dict[str, str]:
        """Classify JTBD based on behavioral patterns."""

        # Consistent Exercisers: weekday mornings, high frequency, low variance
        if is_morning and is_weekday and high_frequency and not high_partner_variety:
            return {
                'name': 'Consistent Exercisers',
                'job_performer': 'Busy professionals and retirees',
                'verb': 'maintain',
                'object': 'physical fitness routine',
                'context': 'when fitting exercise into a busy schedule',
                'desired_outcome': 'stay healthy and energized without disrupting daily commitments',
                'metric': 'consistency of attendance and feeling physically strong',
                'constraints': 'limited time windows (early morning), need reliable court availability',
                'emotional_social': 'feel disciplined and accomplished, not seeking heavy social interaction',
                'time_dimension': 'regular weekday mornings, 3-5x per week',
                'confidence': 'high'
            }

        # Social Connectors: evenings/weekends, high partner variety, high spend
        elif (is_evening or not is_weekday) and high_partner_variety and high_spend:
            return {
                'name': 'Social Connectors',
                'job_performer': 'Social individuals seeking community',
                'verb': 'build and maintain',
                'object': 'friendships and social connections',
                'context': 'when looking for fun social activities with diverse groups',
                'desired_outcome': 'feel part of a vibrant community and make lasting friendships',
                'metric': 'number of new people met, quality of social interactions, having plans to meet again',
                'constraints': 'need variety in playing partners, want welcoming atmosphere',
                'emotional_social': 'feel welcomed, energized, and socially fulfilled',
                'time_dimension': 'evenings and weekends when social energy is high',
                'confidence': 'high'
            }

        # Skill Improvers: drills, events, structured learning
        elif high_drills and high_events and not high_social:
            return {
                'name': 'Skill Improvers',
                'job_performer': 'Competitive individuals focused on mastery',
                'verb': 'improve',
                'object': 'pickleball skills and competitive standing',
                'context': 'when seeking to advance their game systematically',
                'desired_outcome': 'see measurable skill progression and win more games',
                'metric': 'DUPR rating improvement, tournament results, coach feedback',
                'constraints': 'need structured instruction, quality coaching, appropriate skill-level partners',
                'emotional_social': 'feel challenged but not overwhelmed, recognized for improvement',
                'time_dimension': 'consistent weekly drills and practice sessions',
                'confidence': 'high'
            }

        # Competitive Players: high skill, organized games, consistent partners
        elif high_frequency and not high_partner_variety and high_events:
            return {
                'name': 'Competitive Players',
                'job_performer': 'Serious pickleball players',
                'verb': 'compete and win',
                'object': 'matches against worthy opponents',
                'context': 'when seeking competitive challenge and testing skills',
                'desired_outcome': 'win competitive matches and build strong playing partnerships',
                'metric': 'win rate, tournament results, strength of opponents',
                'constraints': 'need high-quality competition, consistent partners, peak-time courts',
                'emotional_social': 'feel respected as a skilled player, enjoy competitive thrill',
                'time_dimension': 'regular games with consistent partners, tournament participation',
                'confidence': 'medium'
            }

        # Casual Explorers: low frequency, variable patterns
        else:
            return {
                'name': 'Casual Explorers',
                'job_performer': 'Occasional players testing the waters',
                'verb': 'explore and try',
                'object': 'pickleball as a potential hobby',
                'context': 'when looking for new activities or occasional recreation',
                'desired_outcome': 'have fun without commitment, decide if pickleball is for them',
                'metric': 'enjoyment level, ease of getting started, welcoming atmosphere',
                'constraints': 'uncertain about long-term commitment, price-sensitive, need beginner-friendly options',
                'emotional_social': 'feel welcome as a beginner, not judged for skill level',
                'time_dimension': 'sporadic, typically weekends or special occasions',
                'confidence': 'medium'
            }

    def identify_context_switchers(self, min_bookings: int = 5) -> List[Dict[str, Any]]:
        """
        Identify customers who exhibit multiple behavioral patterns in different contexts.

        Critical for understanding that segments are context-based, not person-based.
        """
        print("\nIdentifying context switchers...")

        context_switchers = []

        # Only analyze customers with sufficient bookings
        active_members = self.customer_features[
            self.customer_features['total_bookings'] >= min_bookings
        ]['member_id'].tolist()

        for member_id in active_members:
            member_reservations = self.reservations[self.reservations['Player _#'] == member_id]

            if len(member_reservations) < min_bookings:
                continue

            # Split by time context
            morning_bookings = member_reservations[member_reservations['Start Date / Time'].dt.hour.between(6, 11)]
            evening_bookings = member_reservations[member_reservations['Start Date / Time'].dt.hour.between(17, 21)]

            weekday_bookings = member_reservations[member_reservations['Start Date / Time'].dt.dayofweek.between(0, 4)]
            weekend_bookings = member_reservations[~member_reservations['Start Date / Time'].dt.dayofweek.between(0, 4)]

            # Check for significant behavioral differences
            contexts = []

            # Morning vs. Evening
            if len(morning_bookings) >= 2 and len(evening_bookings) >= 2:
                morning_pattern = self._summarize_context_pattern(morning_bookings, member_id)
                evening_pattern = self._summarize_context_pattern(evening_bookings, member_id)

                if self._patterns_differ(morning_pattern, evening_pattern):
                    contexts.append({
                        'dimension': 'time_of_day',
                        'context_a': 'morning',
                        'context_b': 'evening',
                        'pattern_a': morning_pattern,
                        'pattern_b': evening_pattern
                    })

            # Weekday vs. Weekend
            if len(weekday_bookings) >= 2 and len(weekend_bookings) >= 2:
                weekday_pattern = self._summarize_context_pattern(weekday_bookings, member_id)
                weekend_pattern = self._summarize_context_pattern(weekend_bookings, member_id)

                if self._patterns_differ(weekday_pattern, weekend_pattern):
                    contexts.append({
                        'dimension': 'day_of_week',
                        'context_a': 'weekday',
                        'context_b': 'weekend',
                        'pattern_a': weekday_pattern,
                        'pattern_b': weekend_pattern
                    })

            if contexts:
                # Get member name
                member_name = member_reservations.iloc[0]['Player Name'] if len(member_reservations) > 0 else f"Member {member_id}"

                context_switchers.append({
                    'member_id': member_id,
                    'member_name': member_name,
                    'total_bookings': len(member_reservations),
                    'contexts': contexts
                })

        self.context_switchers = context_switchers
        print(f"  Found {len(context_switchers)} context switchers")

        return context_switchers

    def _summarize_context_pattern(self, bookings: pd.DataFrame, member_id: str) -> Dict[str, Any]:
        """Summarize behavioral pattern for a specific context."""

        # Partner variety
        all_members_field = bookings['Members'].dropna()
        unique_partners = set()
        for members_str in all_members_field:
            import re
            partner_ids = re.findall(r'#(\d+)', str(members_str))
            unique_partners.update([p for p in partner_ids if p != member_id])

        return {
            'n_bookings': len(bookings),
            'avg_party_size': bookings['Members Count'].mean(),
            'has_guests': bookings['Guests'].notna().sum() > 0,
            'n_unique_partners': len(unique_partners),
            'event_rate': (bookings['Is Event?'] == 'TRUE').sum() / len(bookings) if len(bookings) > 0 else 0
        }

    def _patterns_differ(self, pattern_a: Dict, pattern_b: Dict, threshold: float = 0.3) -> bool:
        """Check if two behavioral patterns differ significantly."""

        # Compare party size
        if abs(pattern_a['avg_party_size'] - pattern_b['avg_party_size']) > 1:
            return True

        # Compare partner variety
        if abs(pattern_a['n_unique_partners'] - pattern_b['n_unique_partners']) > 3:
            return True

        # Compare event participation
        if abs(pattern_a['event_rate'] - pattern_b['event_rate']) > threshold:
            return True

        return False

    def generate_report(self, output_file: str = 'jtbd-analysis-report.md') -> None:
        """Generate comprehensive markdown report."""
        print(f"\nGenerating report: {output_file}")

        report = []
        report.append("# JTBD Customer Segmentation Analysis")
        report.append(f"\n**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"\n**Analysis Period:** October 1-26, 2025 (26 days)")
        report.append(f"\n**Total Customers Analyzed:** {len(self.customer_features)}")
        report.append(f"\n**Segments Discovered:** {len(self.segments)}")

        # Executive Summary
        report.append("\n## Executive Summary")
        report.append("\nThis analysis identifies customer segments based on Jobs-to-be-Done (JTBD) theory:")
        report.append("- **Same Job:** What progress they're trying to make")
        report.append("- **Same Value Preferences:** How they measure success")
        report.append("- **Same Willingness-to-Pay:** What they'll spend")

        report.append(f"\n\nWe discovered **{len(self.segments)} distinct behavioral segments** representing different customer needs and contexts.")

        # Segment Profiles
        report.append("\n## Discovered Segments")

        for segment_id, profile in sorted(self.segments.items()):
            report.append(f"\n### Segment {segment_id}: {profile['jtbd_hypothesis']['name']}")
            report.append(f"\n**Size:** {profile['size']} customers ({profile['pct_of_total']:.1f}% of total)")
            report.append(f"\n**Confidence:** {profile['jtbd_hypothesis']['confidence'].title()}")

            # JTBD Statement
            report.append("\n#### JTBD Statement")
            jtbd = profile['jtbd_hypothesis']
            report.append(f"\n*When {jtbd['context']}, {jtbd['job_performer']} want to {jtbd['verb']} {jtbd['object']}, ")
            report.append(f"so they can {jtbd['desired_outcome']}, measured by {jtbd['metric']}.*")

            # Behavioral Signature
            report.append("\n#### Behavioral Signature")
            sig = profile['behavioral_signature']

            report.append("\n**Temporal Patterns:**")
            report.append(f"- Morning bookings: {sig.get('pct_morning', {}).get('mean', 0)*100:.0f}%")
            report.append(f"- Evening bookings: {sig.get('pct_evening', {}).get('mean', 0)*100:.0f}%")
            report.append(f"- Weekday vs. Weekend: {sig.get('pct_weekday', {}).get('mean', 0)*100:.0f}% / {sig.get('pct_weekend', {}).get('mean', 0)*100:.0f}%")

            report.append("\n**Social Patterns:**")
            report.append(f"- Partner variety rate: {sig.get('partner_variety_rate', {}).get('mean', 0):.2f}")
            report.append(f"- Event participation: {sig.get('event_participation_rate', {}).get('mean', 0)*100:.0f}%")

            report.append("\n**Engagement & WTP:**")
            report.append(f"- Bookings per month: {sig.get('bookings_per_month', {}).get('mean', 0):.1f}")
            report.append(f"- Spend per booking: ${sig.get('spend_per_booking', {}).get('mean', 0):.2f}")
            report.append(f"- Membership tier: {sig.get('membership_tier', {}).get('mean', 0):.1f}/5")

            # Example members
            report.append("\n#### Example Members")
            sample_ids = profile['member_ids'][:5]
            for mid in sample_ids:
                member_data = self.members[self.members['Member #'] == mid]
                if len(member_data) > 0:
                    name = f"{member_data.iloc[0]['First Name']} {member_data.iloc[0]['Last Name']}"
                    report.append(f"- {name} (#{mid})")

        # Context Switchers
        if self.context_switchers:
            report.append("\n## Context Switchers")
            report.append(f"\nIdentified **{len(self.context_switchers)} customers** who exhibit different behavioral patterns in different contexts.")
            report.append("\nThis validates that segments are **context-based, not person-based**.")

            # Show top examples
            for i, switcher in enumerate(self.context_switchers[:5], 1):
                report.append(f"\n### Example {i}: {switcher['member_name']} (#{switcher['member_id']})")
                report.append(f"**Total Bookings:** {switcher['total_bookings']}")

                for context in switcher['contexts']:
                    report.append(f"\n**Context Switch: {context['dimension'].replace('_', ' ').title()}**")

                    pattern_a = context['pattern_a']
                    pattern_b = context['pattern_b']

                    report.append(f"- **{context['context_a'].title()}:** {pattern_a['n_bookings']} bookings, "
                                f"{pattern_a['n_unique_partners']} unique partners, "
                                f"{pattern_a['event_rate']*100:.0f}% events")

                    report.append(f"- **{context['context_b'].title()}:** {pattern_b['n_bookings']} bookings, "
                                f"{pattern_b['n_unique_partners']} unique partners, "
                                f"{pattern_b['event_rate']*100:.0f}% events")

        # Data Quality Assessment
        report.append("\n## Data Quality Assessment")
        report.append("\n### Data Coverage")
        report.append(f"- **Reservations:** {len(self.reservations)} records")
        report.append(f"- **Members:** {len(self.members)} records")
        report.append(f"- **Transactions:** {len(self.transactions)} records")
        report.append(f"- **Cancellations:** {len(self.cancellations)} records")
        report.append(f"- **Events:** {len(self.events)} event sessions")
        report.append(f"- **Check-ins:** {len(self.checkins)} records")

        report.append("\n### Limitations")
        report.append("- **Partial month:** October 1-26 (26 days). Monthly metrics are extrapolated.")
        report.append("- **New facility:** Opened February 2025, limited historical data.")
        report.append("- **Self-selection bias:** Current members may not represent all potential segments.")

        # Write report
        with open(self.data_dir / output_file, 'w') as f:
            f.write('\n'.join(report))

        print(f"  Report saved to {output_file}")

    def export_json_results(self, output_file: str = 'analysis-results.json') -> None:
        """Export machine-readable JSON results."""
        print(f"\nExporting JSON results: {output_file}")

        results = {
            'summary': {
                'total_customers': int(len(self.customer_features)),
                'total_bookings': int(self.reservations['Player _#'].value_counts().sum()),
                'date_range': 'October 1-26, 2025',
                'analysis_date': datetime.now().isoformat(),
                'segments_discovered': len(self.segments)
            },
            'segments': [],
            'context_switchers': [],
            'methodology': {
                'clustering_algorithm': 'K-Means',
                'n_features': len([c for c in self.customer_features.columns if c not in ['member_id', 'segment', 'cluster_kmeans', 'cluster_dbscan', 'cluster_hierarchical']]),
                'jtbd_framework': '9-element Clayton Christensen framework'
            }
        }

        # Add segment details
        for segment_id, profile in sorted(self.segments.items()):
            segment_dict = {
                'id': int(segment_id),
                'name': profile['jtbd_hypothesis']['name'],
                'size': int(profile['size']),
                'pct_of_total': round(float(profile['pct_of_total']), 2),
                'confidence': profile['jtbd_hypothesis']['confidence'],
                'jtbd_statement': {
                    'job_performer': profile['jtbd_hypothesis']['job_performer'],
                    'verb': profile['jtbd_hypothesis']['verb'],
                    'object': profile['jtbd_hypothesis']['object'],
                    'context': profile['jtbd_hypothesis']['context'],
                    'desired_outcome': profile['jtbd_hypothesis']['desired_outcome'],
                    'metric': profile['jtbd_hypothesis']['metric'],
                    'constraints': profile['jtbd_hypothesis']['constraints'],
                    'emotional_social': profile['jtbd_hypothesis']['emotional_social'],
                    'time_dimension': profile['jtbd_hypothesis']['time_dimension']
                },
                'behavioral_signals': {
                    'temporal': {
                        'pct_morning': round(profile['behavioral_signature'].get('pct_morning', {}).get('mean', 0), 3),
                        'pct_evening': round(profile['behavioral_signature'].get('pct_evening', {}).get('mean', 0), 3),
                        'pct_weekday': round(profile['behavioral_signature'].get('pct_weekday', {}).get('mean', 0), 3)
                    },
                    'social': {
                        'partner_variety_rate': round(profile['behavioral_signature'].get('partner_variety_rate', {}).get('mean', 0), 3),
                        'event_participation_rate': round(profile['behavioral_signature'].get('event_participation_rate', {}).get('mean', 0), 3)
                    },
                    'engagement': {
                        'bookings_per_month': round(profile['behavioral_signature'].get('bookings_per_month', {}).get('mean', 0), 2),
                        'spend_per_booking': round(profile['behavioral_signature'].get('spend_per_booking', {}).get('mean', 0), 2)
                    }
                },
                'example_member_ids': profile['member_ids'][:5]
            }
            results['segments'].append(segment_dict)

        # Add context switcher examples
        if self.context_switchers:
            for switcher in self.context_switchers[:10]:  # Top 10
                # Convert numpy types to native Python types
                contexts_serializable = []
                for ctx in switcher['contexts']:
                    def convert_numpy(val):
                        """Convert numpy types to native Python types."""
                        if isinstance(val, (np.integer)):
                            return int(val)
                        elif isinstance(val, (np.floating)):
                            return float(val)
                        elif isinstance(val, (np.bool_)):
                            return bool(val)
                        else:
                            return val

                    ctx_dict = {
                        'dimension': ctx['dimension'],
                        'context_a': ctx['context_a'],
                        'context_b': ctx['context_b'],
                        'pattern_a': {k: convert_numpy(v) for k, v in ctx['pattern_a'].items()},
                        'pattern_b': {k: convert_numpy(v) for k, v in ctx['pattern_b'].items()}
                    }
                    contexts_serializable.append(ctx_dict)

                results['context_switchers'].append({
                    'member_id': str(switcher['member_id']),
                    'member_name': str(switcher['member_name']),
                    'total_bookings': int(switcher['total_bookings']),
                    'n_contexts': len(switcher['contexts']),
                    'contexts': contexts_serializable
                })

        # Write JSON
        with open(self.data_dir / output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"  JSON results saved to {output_file}")

    def create_visualizations(self, output_dir: str = '.') -> None:
        """Create visualization plots."""
        print("\nCreating visualizations...")

        output_path = Path(output_dir)

        # 1. Cluster scatter plot (PCA)
        numeric_cols = [col for col in self.customer_features.columns
                       if col not in ['member_id', 'segment', 'cluster_kmeans', 'cluster_dbscan', 'cluster_hierarchical']
                       and self.customer_features[col].dtype in [np.float64, np.int64]]

        X = self.customer_features[numeric_cols].fillna(0)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)

        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1],
                            c=self.customer_features['segment'],
                            cmap='viridis',
                            alpha=0.6,
                            s=50)
        plt.colorbar(scatter, label='Segment')
        plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% variance)')
        plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% variance)')
        plt.title('Customer Segments (PCA Projection)')
        plt.tight_layout()
        plt.savefig(output_path / 'segment_clusters.png', dpi=300)
        print("  Saved: segment_clusters.png")
        plt.close()

        # 2. Segment size distribution
        plt.figure(figsize=(10, 6))
        segment_sizes = self.customer_features['segment'].value_counts().sort_index()
        segment_names = [self.segments[sid]['jtbd_hypothesis']['name'] for sid in segment_sizes.index]

        plt.bar(range(len(segment_sizes)), segment_sizes.values)
        plt.xticks(range(len(segment_sizes)), segment_names, rotation=45, ha='right')
        plt.xlabel('Segment')
        plt.ylabel('Number of Customers')
        plt.title('Customer Distribution Across Segments')
        plt.tight_layout()
        plt.savefig(output_path / 'segment_distribution.png', dpi=300)
        print("  Saved: segment_distribution.png")
        plt.close()

        # 3. Booking time heatmap by segment
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()

        for idx, (segment_id, profile) in enumerate(sorted(self.segments.items())):
            if idx >= 6:
                break

            ax = axes[idx]
            segment_members = self.customer_features[self.customer_features['segment'] == segment_id]['member_id'].tolist()
            segment_reservations = self.reservations[self.reservations['Player _#'].isin(segment_members)]

            if len(segment_reservations) > 0:
                hours = segment_reservations['Start Date / Time'].dt.hour
                days = segment_reservations['Start Date / Time'].dt.dayofweek

                heatmap_data = np.zeros((7, 24))
                for day, hour in zip(days, hours):
                    if pd.notna(day) and pd.notna(hour):
                        heatmap_data[int(day), int(hour)] += 1

                sns.heatmap(heatmap_data, ax=ax, cmap='YlOrRd', cbar=True)
                ax.set_title(f"Segment {segment_id}: {profile['jtbd_hypothesis']['name']}")
                ax.set_xlabel('Hour of Day')
                ax.set_ylabel('Day of Week')
                ax.set_yticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], rotation=0)

        plt.tight_layout()
        plt.savefig(output_path / 'booking_time_heatmaps.png', dpi=300)
        print("  Saved: booking_time_heatmaps.png")
        plt.close()

        print("  Visualization creation complete")


def main():
    """Main execution function."""
    print("="*70)
    print("CourtReserve JTBD Customer Segmentation Analysis")
    print("Pickleball Clubhouse Chicago")
    print("="*70)

    # Initialize analyzer
    analyzer = JTBDAnalyzer(data_dir='.')

    # Load and clean data
    analyzer.load_data()
    analyzer.clean_data()

    # Feature engineering
    analyzer.engineer_features()

    # Clustering
    analyzer.cluster_customers(n_clusters_range=(3, 7))

    # Segment profiling
    analyzer.profile_segments()

    # JTBD hypothesis generation
    analyzer.generate_jtbd_hypotheses()

    # Context switcher detection
    analyzer.identify_context_switchers(min_bookings=5)

    # Generate outputs
    analyzer.generate_report('jtbd-analysis-report.md')
    analyzer.export_json_results('analysis-results.json')

    # Optional: Create visualizations
    try:
        analyzer.create_visualizations('.')
    except Exception as e:
        print(f"\nWarning: Visualization creation failed: {e}")
        print("Continuing without visualizations...")

    print("\n" + "="*70)
    print("Analysis complete!")
    print("="*70)
    print("\nGenerated files:")
    print("  - jtbd-analysis-report.md (comprehensive analysis)")
    print("  - analysis-results.json (machine-readable results)")
    print("  - segment_clusters.png (visualization)")
    print("  - segment_distribution.png (visualization)")
    print("  - booking_time_heatmaps.png (visualization)")
    print("\nNext steps:")
    print("  1. Review jtbd-analysis-report.md for insights")
    print("  2. Validate segments with business stakeholders")
    print("  3. Design programming to address unmet needs")
    print("  4. Integrate analysis-results.json into CIC dashboard")


if __name__ == '__main__':
    main()
