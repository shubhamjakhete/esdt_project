"""
Propositional Logic Module
Simple constraint filtering using boolean logic

CPSC 583 Project
Authors: Cameron Potvin, Shubham Jakhete, Jaiveer Kapadia
"""

from dataclasses import dataclass
from typing import Dict, List, Callable
import pandas as pd


@dataclass
class Constraint:
    name: str
    check: Callable  # function that takes a car row and returns True/False
    description: str


class PropositionalLogic:
    """
    Simple propositional logic for filtering cars.

    Each constraint is a predicate, and we AND them all together:
    passes(car) = C1(car) AND C2(car) AND ... AND Cn(car)
    """

    def __init__(self):
        self.constraints = []

    def add_constraint(self, name, check, description):
        self.constraints.append(Constraint(name, check, description))

    def evaluate(self, car):
        # Check if a car satisfies all constraints
        failed = []
        for c in self.constraints:
            try:
                if not c.check(car):
                    failed.append(c.name)
            except:
                failed.append(c.name)  # treat errors as failures
        return len(failed) == 0, failed

    def filter_cars(self, df: pd.DataFrame) -> pd.DataFrame:
        #Filter dataframe to only cars passing all constraints
        passing = []
        for _, car in df.iterrows():
            ok, _ = self.evaluate(car)
            if ok:
                passing.append(car)

        return pd.DataFrame(passing) if passing else pd.DataFrame()

    def get_constraint_summary(self):
        lines = ["Constraints:"]
        for c in self.constraints:
            lines.append(f"  - {c.name}: {c.description}")
        return "\n".join(lines)


def create_user_constraints(prefs: Dict) -> PropositionalLogic:
    # Build constraint system from user preferences
    logic = PropositionalLogic()

    if 'max_price' in prefs:
        logic.add_constraint(
            'max_price',
            lambda car, p=prefs['max_price']: car.get('price', 999999) <= p,
            f"price <= ${prefs['max_price']:,}"
        )

    if 'min_year' in prefs:
        logic.add_constraint(
            'min_year',
            lambda car, y=prefs['min_year']: car.get('year', 0) >= y,
            f"year >= {prefs['min_year']}"
        )

    if 'max_year' in prefs:
        logic.add_constraint(
            'max_year',
            lambda car, y=prefs['max_year']: car.get('year', 9999) <= y,
            f"year <= {prefs['max_year']}"
        )

    if 'min_safety' in prefs:
        logic.add_constraint(
            'min_safety',
            lambda car, s=prefs['min_safety']: car.get('overall_rating', 0) >= s,
            f"safety >= {prefs['min_safety']}"
        )

    if 'max_mileage' in prefs:
        logic.add_constraint(
            'max_mileage',
            lambda car, m=prefs['max_mileage']: car.get('mileage', 999999) <= m,
            f"mileage <= {prefs['max_mileage']:,}"
        )

    if 'min_reliability' in prefs:
        logic.add_constraint(
            'min_reliability',
            lambda car, r=prefs['min_reliability']: car.get('reliability_score', 0) >= r,
            f"reliability >= {prefs['min_reliability']}"
        )

    return logic


# quick test
if __name__ == '__main__':
    test_cars = pd.DataFrame([
        {'make': 'Toyota', 'model': 'Camry', 'year': 2018, 'price': 18000,
         'overall_rating': 5, 'mileage': 45000, 'reliability_score': 0.9},
        {'make': 'Honda', 'model': 'Civic', 'year': 2015, 'price': 12000,
         'overall_rating': 4, 'mileage': 75000, 'reliability_score': 0.85},
        {'make': 'Ford', 'model': 'F-150', 'year': 2020, 'price': 35000,
         'overall_rating': 4, 'mileage': 25000, 'reliability_score': 0.75},
    ])

    prefs = {'max_price': 20000, 'min_year': 2016, 'min_safety': 4.5}

    logic = create_user_constraints(prefs)
    print(logic.get_constraint_summary())

    filtered = logic.filter_cars(test_cars)
    print(f"\nFiltered: {len(filtered)} cars")
