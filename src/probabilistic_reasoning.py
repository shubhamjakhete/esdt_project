"""
Probabilistic Reasoning Module
Estimates reliability using complaint data and vehicle age

CPSC 583 Project
Authors: Cameron Potvin, Shubham Jakhete, Jaiveer Kapadia
"""

import pandas as pd
import numpy as np
from typing import Dict, List


class ReliabilityEstimator:
    # Estimates vehicle reliability using probability calculations
    
    def __init__(self):
        # failure rates by vehicle age
        # these are rough estimates based on some googling + intuition
        self.failure_rates = {
            0: 0.02,
            1: 0.03,
            2: 0.04,
            3: 0.05,
            4: 0.06,
            5: 0.08,
            6: 0.10,
            7: 0.12,
            8: 0.15,
            9: 0.18,
            10: 0.22,
        }
        
        # avg repair costs 
        self.repair_costs = {
            'minor': 500,
            'moderate': 1500,
            'major': 4000,
            'critical': 8000
        }
    
    def get_failure_rate(self, age):
        # Get base failure rate for vehicle age
        if age <= 10:
            return self.failure_rates.get(age, 0.22)
        else:
            # exponential increase after 10 years
            return min(0.22 + (age - 10) * 0.03, 0.60)
    
    def estimate_reliability(self, vehicle: Dict, ownership_years: int = 5) -> Dict:
        """
        Estimate reliability metrics for a single vehicle

        Returns dict with:
        - reliability_score (0-1, higher is better)
        - failure_prob_1yr
        - failure_prob_5yr
        - expected_repair_cost_5yr
        """
        # making sure we have scalar values (pandas can sneak in Series/arrays)
        year = vehicle.get('year', 2020)
        if hasattr(year, 'item'):
            year = int(year.item())
        else:
            year = int(year)

        age = 2024 - year

        complaints = vehicle.get('complaint_count', 0)
        if hasattr(complaints, 'item'):
            complaints = int(complaints.item())
        else:
            complaints = int(complaints) if complaints else 0
        
        base = self.get_failure_rate(age)
        
        # more complaints = worse reliability
        complaint_mult = 1.0 + (complaints * 0.05)
        
        prob_1yr = min(base * complaint_mult, 0.80)  # cap at 80%
        
                # 5 year cumulative probability (baseline, kept for backward compatibility)
        prob_5yr = 1 - (1 - prob_1yr) ** 5

        # Expected costs over 5 years (same structure as before)
        minor_issues_5yr = 2.5 * (1 + age * 0.05)
        moderate_issues_5yr = 1.0 * complaint_mult
        major_issues_5yr = prob_5yr * 0.5

        expected_cost_5yr = (
            minor_issues_5yr * self.repair_costs['minor'] +
            moderate_issues_5yr * self.repair_costs['moderate'] +
            major_issues_5yr * self.repair_costs['major']
        )

        # Ownership-horizon probability and costs
        years = max(int(ownership_years), 1)

        prob_ownership = 1 - (1 - prob_1yr) ** years

        # Scale 5-year expected cost roughly by years/5
        years_factor = years / 5.0
        expected_cost_ownership = expected_cost_5yr * years_factor

        # reliability score = inverse of failure probability over ownership period
        score = 1 - prob_ownership
        
        return {
            'reliability_score': max(0, min(1, score)),
            'failure_prob_1yr': prob_1yr,
            'failure_prob_5yr': prob_5yr,
            'failure_prob_ownership': prob_ownership,
            'expected_repair_cost_5yr': expected_cost_5yr,
            'expected_repair_cost_ownership': expected_cost_ownership,
            'age': age,
            'complaint_count': complaints,
            'ownership_years': years
        }
    
    def compare_reliability_confidence(self, vehicles: List[Dict]) -> pd.DataFrame:
        # Compare reliability across multiple vehicles
        results = []
        
        for v in vehicles:
            metrics = self.estimate_reliability(v)
            
            results.append({
                'make': v.get('make', 'Unknown'),
                'model': v.get('model', 'Unknown'),
                'year': v.get('year', 0),
                'reliability_score': metrics['reliability_score'],
                'minor_issue_prob_1yr': metrics['failure_prob_1yr'] * 0.5,
                'major_issue_prob_1yr': metrics['failure_prob_1yr'],
                'major_issue_prob_5yr': metrics['failure_prob_5yr'],
                'expected_repair_cost_5yr': metrics['expected_repair_cost_5yr'],
            })
        
        return pd.DataFrame(results)
    
    def get_recommendation(self, vehicle):
        # Get maintenance recommendation based on reliability
        m = self.estimate_reliability(vehicle)
        
        if m['failure_prob_5yr'] < 0.20:
            return "Low risk - standard maintenance should be fine"
        elif m['failure_prob_5yr'] < 0.40:
            return "Moderate risk - consider extended warranty"
        elif m['failure_prob_5yr'] < 0.60:
            return "Higher risk - extended warranty recommended, budget for repairs"
        else:
            return "High risk - expect significant maintenance costs"


if __name__ == '__main__':
    estimator = ReliabilityEstimator()
    
    test_cars = [
        {'make': 'Toyota', 'model': 'Camry', 'year': 2018, 'complaint_count': 2},
        {'make': 'BMW', 'model': '328i', 'year': 2014, 'complaint_count': 15},
        {'make': 'Honda', 'model': 'Civic', 'year': 2020, 'complaint_count': 1},
    ]
    
    print("Reliability Analysis")
    print("=" * 60)
    
    for car in test_cars:
        m = estimator.estimate_reliability(car)
        print(f"\n{car['year']} {car['make']} {car['model']}")
        print(f"  Reliability: {m['reliability_score']:.0%}")
        print(f"  1-yr failure prob: {m['failure_prob_1yr']:.0%}")
        print(f"  5-yr failure prob: {m['failure_prob_5yr']:.0%}")
        print(f"  Expected 5-yr repairs: ${m['expected_repair_cost_5yr']:,.0f}")
        print(f"  Recommendation: {estimator.get_recommendation(car)}")
    
    print("\n\nComparison table:")
    df = estimator.compare_reliability_confidence(test_cars)
    print(df.to_string(index=False))
