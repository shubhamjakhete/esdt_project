#!/usr/bin/env python3
"""
Demo script - shows off all the KR methods
Good for presentations
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from recommendation_engine import CarRecommendationEngine


def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def main():
    print_header("USED CAR RECOMMENDATION SYSTEM")
    print("\nCPSC 583 Project")
    print("Cameron Potvin, Shubham Jakhete, Jaiveer Kapadia")
    
    input("\nPress Enter to start demo...")
    
    # load the system
    print("\nLoading data and initializing components...")
    engine = CarRecommendationEngine()
    
    if engine.df is None or len(engine.df) == 0:
        print("ERROR: couldn't load data")
        return
    
    print(f"Loaded {len(engine.df)} vehicles")
    
    input("\nPress Enter to run recommendation...")
    
    # demo preferences (good defaults for showing off the system)
    prefs = {
        'max_price': 25000,
        'min_year': 2016,
        'min_safety': 4.0,
        'min_reliability': 0.75,
        'max_mileage': 80000,
        'ownership_years': 5
    }
    
    print("\nPreferences:")
    for k, v in prefs.items():
        print(f"  {k}: {v}")
    
    print("\nRunning all 5 KR methods...")
    print("  [1] Propositional Logic - filtering by constraints")
    print("  [2] Prolog - rule-based classification")
    print("  [3] PDDL - ownership cost planning")
    print("  [4] RDF/OWL - building knowledge graph")
    print("  [5] Probabilistic - reliability estimation")
    
    recs, explanations = engine.get_recommendations(prefs, top_n=5)
    
    if recs.empty:
        print("\nNo results with these constraints")
        print("(this shouldn't happen with the demo preferences)")
        return
    
    # show results
    print_header("TOP RECOMMENDATIONS")
    
    for i, pick in enumerate(explanations['top_picks'], 1):
        print(f"\n{i}. {pick['vehicle']}")
        print(f"   Score: {pick['composite_score']}")
        print(f"   Category: {pick['prolog_classification']}")
        print(f"   Strengths: {', '.join(pick['strengths'][:2])}")
        if pick['considerations']:
            print(f"   Watch out for: {pick['considerations'][0]}")
    
    print_header("WHAT EACH METHOD CONTRIBUTED")
    
    print("""
1. PROPOSITIONAL LOGIC
   - Filtered dataset down to cars meeting hard constraints
   - Fast and deterministic
   
2. PROLOG RULES  
   - Classified cars as "family car", "good value", etc.
   - Uses expert knowledge encoded as logic rules
   
3. PDDL PLANNING
   - Calculated 5-year total cost of ownership
   - Estimates maintenance and resale value
   
4. RDF/OWL ONTOLOGY
   - Built semantic knowledge graph of vehicles
   - Enables SPARQL queries and relationship reasoning
   
5. PROBABILISTIC METHODS
   - Estimated reliability from complaint data
   - Calculated failure probabilities
""")
    
    print_header("COMPOSITE SCORING")
    print("""
Final scores are weighted:
  - Safety Rating: 25%
  - Reliability: 25%  
  - Initial Price: 20%
  - Total Cost of Ownership: 15%
  - Maintenance Risk: 15%
""")
    
    input("\nPress Enter to finish...")
    print("\nDemo complete!")
    print("Try the web interface: streamlit run app.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo cancelled")
