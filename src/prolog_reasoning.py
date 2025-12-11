"""
Prolog Reasoning Module

The actual reasoning logic is in prolog/car_rules.pl
This module just handles loading data and calling Prolog

CPSC 583 Project
Authors: Cameron Potvin, Shubham Jakhete, Jaiveer Kapadia
"""

import subprocess
import pandas as pd
from pathlib import Path
from typing import Dict, List


class PrologReasoner:
    """
    The rules are defined in prolog/car_rules.pl
    We generate facts from the data and query Prolog for classifications.
    """

    def __init__(self, rules_file='prolog/car_rules.pl'):
        self.rules_file = Path(rules_file)
        self.swipl_path = self._find_prolog()

    def _find_prolog(self):
        # Try to find SWI-Prolog on the system
        paths = [
            'swipl',
            '/opt/homebrew/bin/swipl',
            '/usr/local/bin/swipl',
            '/usr/bin/swipl',
        ]
        for p in paths:
            try:
                result = subprocess.run([p, '--version'],
                                       capture_output=True, timeout=3)
                if result.returncode == 0:
                    return p
            except:
                pass
        return None

    def is_available(self):
        # Check if Prolog is installed
        return self.swipl_path is not None

    def _generate_facts(self, df: pd.DataFrame) -> Path:
        """
        Convert dataframe to Prolog facts file

        Each car becomes a fact like:
        car(make, model, year, price, safety, reliability, mileage).
        """
        facts = []

        for _, row in df.iterrows():
            # clean up strings for Prolog
            make = str(row.get('make', 'unknown')).upper().replace("'", "")
            model = str(row.get('model', 'unknown')).upper().replace("'", "")
            year = int(row.get('year', 2020))
            price = float(row.get('price', 0))
            safety = float(row.get('overall_rating', 3.0))
            reliability = float(row.get('reliability_score', 0.5))
            mileage = float(row.get('mileage', 50000))

            fact = f"car('{make}', '{model}', {year}, {price}, {safety}, {reliability}, {mileage})."
            facts.append(fact)

        # write to file
        out_path = Path('prolog/car_facts.pl')
        out_path.parent.mkdir(exist_ok=True)

        with open(out_path, 'w') as f:
            f.write("% Generated car facts - don't edit manually\n")
            f.write(":- discontiguous car/7.\n\n")
            for fact in facts:
                f.write(fact + "\n")

        return out_path

    def classify_vehicles(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """
        Run Prolog rules to classify vehicles into categories

        Returns dict like:
        {
            'excellent_choice': [car1, car2, ...],
            'good_value': [...],
            ...
        }
        """
        if not self.is_available():
            print("  Warning: SWI-Prolog not found")
            return {}

        # generate facts file from dataframe
        self.facts_file = self._generate_facts(df)

        # categories we want to query (these match predicates in car_rules.pl)
        categories = [
            'excellent_choice',
            'good_value',
            'family_car',
            'reliable_commuter',
            'budget_pick'
        ]

        results = {}
        for cat in categories:
            cars = self._query_category(cat, self.facts_file)
            if cars:
                results[cat] = cars

        return results

    def get_car_strengths(self, make: str, model: str) -> List[str]:
        """
        Query Prolog for the strengths of a specific car.
        Uses the car_strengths/2 predicate defined in car_rules.pl
        """
        if not self.is_available() or not hasattr(self, 'facts_file'):
            return []

        make = make.upper().replace("'", "")
        model = model.upper().replace("'", "")

        query = f"""
:- ['{self.rules_file.stem}'].
:- ['{self.facts_file.stem}'].

run :-
    car('{make}', '{model}', Year, Price, Safety, Rel, Miles),
    Car = car('{make}', '{model}', Year, Price, Safety, Rel, Miles),
    car_strengths(Car, Strengths),
    forall(member(S, Strengths), (format('STRENGTH|~w~n', [S]))),
    !.
run.

:- run, halt.
"""

        query_file = Path('prolog/_temp_strengths.pl')
        with open(query_file, 'w') as f:
            f.write(query)

        try:
            result = subprocess.run(
                [self.swipl_path, '-q', '-s', '_temp_strengths.pl'],
                capture_output=True,
                text=True,
                timeout=5,
                cwd='prolog'
            )

            strengths = []
            for line in result.stdout.split('\n'):
                if line.startswith('STRENGTH|'):
                    strength = line.replace('STRENGTH|', '').strip()
                    if strength:
                        strengths.append(strength)

            query_file.unlink(missing_ok=True)
            return strengths

        except Exception as e:
            print(f"  Prolog strengths query error: {e}")
            return []

    def _query_category(self, predicate: str, facts_file: Path) -> List[Dict]:
        # Query Prolog for all cars matching a category predicate

        # build a simple query script
        query = f"""
:- ['{self.rules_file.stem}'].
:- ['{facts_file.stem}'].

run :-
    car(Make, Model, Year, Price, Safety, Rel, Miles),
    Car = car(Make, Model, Year, Price, Safety, Rel, Miles),
    {predicate}(Car),
    format('RESULT|~w|~w|~w|~w|~w|~w|~w~n',
           [Make, Model, Year, Price, Safety, Rel, Miles]),
    fail.
run.

:- run, halt.
"""

        # write temp query file in prolog directory
        query_file = Path('prolog/_temp_query.pl')
        with open(query_file, 'w') as f:
            f.write(query)

        try:
            result = subprocess.run(
                [self.swipl_path, '-q', '-s', '_temp_query.pl'],
                capture_output=True,
                text=True,
                timeout=10,
                cwd='prolog'
            )

            # parse results
            cars = []
            for line in result.stdout.split('\n'):
                if line.startswith('RESULT|'):
                    parts = line.replace('RESULT|', '').split('|')
                    if len(parts) == 7:
                        cars.append({
                            'make': parts[0],
                            'model': parts[1],
                            'year': int(parts[2]),
                            'price': float(parts[3]),
                            'safety': float(parts[4]),
                            'reliability': float(parts[5]),
                            'mileage': float(parts[6])
                        })

            # cleanup
            query_file.unlink(missing_ok=True)
            return cars

        except Exception as e:
            print(f"  Prolog query error: {e}")
            return []


# test
if __name__ == '__main__':
    reasoner = PrologReasoner()

    if reasoner.is_available():
        print("Prolog found!")

        # test with some sample data
        test_df = pd.DataFrame([
            {'make': 'TOYOTA', 'model': 'CAMRY', 'year': 2020, 'price': 22000,
             'overall_rating': 5.0, 'reliability_score': 0.95, 'mileage': 30000},
            {'make': 'BMW', 'model': '328i', 'year': 2016, 'price': 18000,
             'overall_rating': 4.0, 'reliability_score': 0.6, 'mileage': 65000},
        ])

        results = reasoner.classify_vehicles(test_df)

        print("\nClassifications:")
        for cat, cars in results.items():
            print(f"  {cat}: {len(cars)} cars")
            for c in cars:
                print(f"    - {c['year']} {c['make']} {c['model']}")
    else:
        print("SWI-Prolog not installed")
        print("Get it from: https://www.swi-prolog.org/")
