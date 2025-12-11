"""
Integrates Prolog rules and RDF/OWL ontology for car recommendations

CPSC 583 Project
Authors: Cameron Potvin, Shubham Jakhete, Jaiveer Kapadia
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple

from propositional_logic import create_user_constraints
from prolog_reasoning import PrologReasoner
from ontology_builder import CarOntology
from probabilistic_reasoning import ReliabilityEstimator


class CarRecommendationEngine:
    """
    Recommendation system using multiple KR techniques:
    1. Propositional logic for constraint filtering
    2. Prolog for rule-based classification
    3. RDF/OWL ontology for semantic reasoning
    4. Simple probabilistic methods for reliability
    """

    def __init__(self, data_file='data/integrated_cars.csv'):
        self.data_file = Path(data_file)
        self.df = None
        self.load_data()

        # init components
        self.prolog = PrologReasoner()
        self.ontology = CarOntology()
        self.reliability = ReliabilityEstimator()

    def load_data(self):
        """Load the integrated dataset"""
        if self.data_file.exists():
            self.df = pd.read_csv(self.data_file)
            print(f"Loaded {len(self.df)} vehicles")
        else:
            print(f"Warning: {self.data_file} not found")
            self.df = pd.DataFrame()

    def get_recommendations(self, prefs: Dict, top_n: int = 10) -> Tuple[pd.DataFrame, Dict]:
        """
        Main method - runs all KR techniques and combines results
        """
        if self.df is None or self.df.empty:
            return pd.DataFrame(), {'message': 'No data available'}

        # ownership period (in years) comes from prefs['year']
        ownership_years = int(prefs.get('year', 5))

        print("\n" + "=" * 60)
        print("RUNNING RECOMMENDATION PIPELINE")
        print("=" * 60)

        # Step 1: Propositional Logic filtering
        print("\n[1/4] Propositional Logic - filtering by constraints...")
        logic = create_user_constraints(prefs)
        print(logic.get_constraint_summary())

        filtered = logic.filter_cars(self.df)
        print(f"  => {len(filtered)} vehicles pass all constraints")

        if filtered.empty:
            return pd.DataFrame(), {'message': 'No vehicles match your constraints'}

        # Step 2: Prolog classification
        print("\n[2/4] Prolog - running expert rules...")
        prolog_results = {}
        if self.prolog.is_available():
            prolog_results = self.prolog.classify_vehicles(filtered)
            for cat, cars in prolog_results.items():
                if cars:
                    print(f"  => {cat}: {len(cars)} vehicles")
        else:
            print("  => SWI-Prolog not installed, skipping")

        # Step 3: Ontology queries
        print("\n[3/4] RDF/OWL Ontology - semantic reasoning...")
        self.ontology.build_from_dataframe(filtered)

        # run some SPARQL queries to get semantic info
        safe_vehicles = self.ontology.query_safe_vehicles(min_rating=4.0)
        reliable_makes = self.ontology.query_reliable_manufacturers()
        print(f"  => Found {len(safe_vehicles)} highly-rated vehicles")
        print(f"  => Reliable manufacturers: {reliable_makes[:5]}...")

        # Step 4: Probabilistic reliability
        print("\n[4/4] Probabilistic - estimating reliability...")
        filtered = filtered.copy()

        prob_scores = []
        failure_probs = []
        repair_costs = []

        for idx, row in filtered.iterrows():
            # Pass ownership_years into the estimator
            metrics = self.reliability.estimate_reliability(
                row.to_dict(),
                ownership_years
            )

            # Use ownership-based reliability for scoring and display
            filtered.at[idx, 'reliability_score'] = metrics['reliability_score']

            prob_scores.append(metrics['reliability_score'])
            # these keys are expected to be returned by the estimator
            if 'failure_prob_ownership' in metrics:
                failure_probs.append(metrics['failure_prob_ownership'])
            else:
                failure_probs.append(metrics.get('failure_prob_5yr', 0.0))

            if 'expected_repair_cost_ownership' in metrics:
                repair_costs.append(metrics['expected_repair_cost_ownership'])
            else:
                repair_costs.append(metrics.get('expected_repair_cost_5yr', 0.0))

        filtered['prob_reliability'] = prob_scores
        filtered['failure_prob_ownership'] = failure_probs
        filtered['expected_repair_cost_ownership'] = repair_costs

        # Simple resale value estimate given ownership period
        filtered['expected_resale_value'] = filtered.apply(
            lambda row: self._estimate_resale_value(row, ownership_years),
            axis=1
        )

        # Combine everything into final score
        results = self._compute_final_scores(filtered, prolog_results)
        results = results.sort_values('final_score', ascending=False)

        # Build explanations
        explanations = self._build_explanations(results.head(top_n), prolog_results)

        print(f"\nDone! Returning top {min(top_n, len(results))} recommendations")

        return results.head(top_n), explanations

    def _estimate_resale_value(self, row, ownership_years: int) -> float:
        """
        Very simple resale value estimate.

        Uses current price, current depreciation_rate from the integrated data,
        and the user's ownership period (prefs['year']).

        Returns an estimated resale price in dollars.
        """
        try:
            price = float(row['price'])
        except (KeyError, TypeError, ValueError):
            return 0.0

        # base depreciation that has already happened (from data_integration.py)
        # e.g., age * 0.15
        try:
            base_rate = float(row.get('depreciation_rate', 0.3))
        except (TypeError, ValueError):
            base_rate = 0.3

        # Additional depreciation over the ownership period
        # Assume cars lose ~8% of remaining value per year going forward
        years = max(int(ownership_years), 1)
        extra_rate = years * 0.08

        total_rate = base_rate + extra_rate
        # clamp so it never goes below ~15% of original price
        total_rate = max(0.0, min(total_rate, 0.85))

        return price * (1.0 - total_rate)

    def _compute_final_scores(self, df, prolog_results):
        """
        Combine all the signals into one score
        """
        result = df.copy()

        # normalize safety (1-5 scale to 0-1)
        result['safety_norm'] = (result['overall_rating'] - 1) / 4.0
        result['safety_norm'] = result['safety_norm'].fillna(0.5)

        # reliability: prefer probabilistic score if available, otherwise fall back to original
        if 'prob_reliability' in result.columns:
            result['rel_norm'] = result['prob_reliability'].fillna(0.5)
        else:
            result['rel_norm'] = result['reliability_score'].fillna(0.5)

        # price - lower is better, normalize and invert
        if result['price'].max() > result['price'].min():
            result['price_norm'] = 1 - (result['price'] - result['price'].min()) / (
                result['price'].max() - result['price'].min()
            )
        else:
            result['price_norm'] = 0.5

        # resale value - higher is better
        if 'expected_resale_value' in result.columns and result['expected_resale_value'].notna().any():
            if result['expected_resale_value'].max() > result['expected_resale_value'].min():
                result['resale_norm'] = (
                    result['expected_resale_value'] - result['expected_resale_value'].min()
                ) / (result['expected_resale_value'].max() - result['expected_resale_value'].min())
            else:
                result['resale_norm'] = 0.5
        else:
            result['resale_norm'] = 0.5

        # bonus for Prolog classifications
        result['prolog_bonus'] = result.apply(
            lambda row: self._get_prolog_bonus(row, prolog_results), axis=1
        )

        # final weighted score
        # safety + reliability still dominate, price + resale share, Prolog is a bonus
        result['final_score'] = (
            result['safety_norm'] * 0.30 +
            result['rel_norm'] * 0.30 +
            result['price_norm'] * 0.20 +
            result['resale_norm'] * 0.20 +
            result['prolog_bonus'] * 0.10
        )

        return result

    def _get_prolog_bonus(self, row, prolog_results):
        """Give bonus points if Prolog classified this car positively"""
        bonus = 0
        for cat, cars in prolog_results.items():
            for car in cars:
                if (car.get('make') == row['make'] and
                    car.get('model') == row['model']):
                    bonus += 0.2  # small bonus per category
        return min(bonus, 1.0)  # cap at 1

    def _build_explanations(self, recs, prolog_results):
        """Generate explanations for the recommendations"""
        ontology_stats = self.ontology.get_stats()

        explanations = {
            'methodology': """
This system uses two main KR approaches:

1. PROLOG RULES - Expert knowledge encoded as logic rules
   Categories like 'family_car', 'good_value' etc are defined
   in prolog/car_rules.pl and evaluated against each vehicle.

2. RDF/OWL ONTOLOGY - Semantic knowledge graph
   Vehicles are represented as RDF triples with relationships
   like 'madeBy', 'safetyRating'. SPARQL queries
   find vehicles matching semantic criteria.

Also uses propositional logic for filtering and basic
probabilistic methods for reliability estimation.
""",
            'ontology_stats': ontology_stats,
            'top_picks': []
        }

        for _, row in recs.iterrows():
            # get strengths from Prolog reasoning
            prolog_strengths = []
            if self.prolog.is_available():
                prolog_strengths = self.prolog.get_car_strengths(row['make'], row['model'])

            pick = {
                'vehicle': f"{int(row['year'])} {row['make']} {row['model']}",
                'score': f"{row['final_score']:.3f}",
                'price': f"${row['price']:,.0f}",
                'safety': f"{row['overall_rating']:.1f} stars",
                'reliability': f"{row['reliability_score']:.0%}",
                'prolog_categories': self._get_categories(row, prolog_results),
                'prolog_strengths': prolog_strengths  # from Prolog reasoning
            }

            # resale value in explanation (if available)
            if 'expected_resale_value' in row and pd.notna(row['expected_resale_value']):
                pick['resale_value'] = f"${row['expected_resale_value']:,.0f}"
            else:
                pick['resale_value'] = "n/a"

            explanations['top_picks'].append(pick)

        return explanations

    def _get_categories(self, row, prolog_results):
        """Find which Prolog categories this car belongs to"""
        cats = []
        for cat, cars in prolog_results.items():
            for car in cars:
                if car.get('make') == row['make'] and car.get('model') == row['model']:
                    cats.append(cat)
                    break
        return cats if cats else ['uncategorized']

    def print_results(self, recs, explanations):
        """Pretty print the results"""
        print("\n" + "=" * 60)
        print("RECOMMENDATIONS")
        print("=" * 60)

        print(explanations['methodology'])

        print("-" * 60)
        print("TOP PICKS:")
        print("-" * 60)

        for i, pick in enumerate(explanations['top_picks'], 1):
            print(f"\n{i}. {pick['vehicle']}")
            print(f"   Score: {pick['score']} | Price: {pick['price']}")
            print(f"   Safety: {pick['safety']} | Reliability: {pick['reliability']}")
            print(f"   Categories: {', '.join(pick['prolog_categories'])}")
            # show estimated resale value 
            resale = pick.get('resale_value', 'n/a')
            print(f"   Estimated resale value: {resale}")


# quick test
if __name__ == '__main__':
    engine = CarRecommendationEngine()

    prefs = {
        'max_price': 25000,
        'min_year': 2016,
        'min_safety': 4,
        'min_reliability': 0.7,
        # ownership horizon in years (used inside get_recommendations)
        'year': 5
    }

    recs, explanations = engine.get_recommendations(prefs, top_n=10)
    engine.print_results(recs, explanations)
