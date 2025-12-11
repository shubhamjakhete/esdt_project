"""
Command line interface for car recommendations

CPSC 583 Project
Authors: Cameron Potvin, Shubham Jakhete, Jaiveer Kapadia
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / 'src'))

from recommendation_engine import CarRecommendationEngine


def get_preferences():
    # Get user preferences 
    print()
    print("=" * 50)
    print("  USED CAR RECOMMENDATION SYSTEM")
    print("  CPSC 583 Project")
    print("=" * 50)
    print()
    print("Enter your preferences (hit enter for defaults):")
    print()
    
    prefs = {}
    
    val = input("Max budget [$25000]: ").strip()
    prefs['max_price'] = float(val) if val else 25000
    
    val = input("Min year [2016]: ").strip()
    prefs['min_year'] = int(val) if val else 2016
    
    val = input("Max year [2024]: ").strip()
    prefs['max_year'] = int(val) if val else 2024
    
    val = input("Min safety rating (1-5) [4.0]: ").strip()
    prefs['min_safety'] = float(val) if val else 4.0
    
    val = input("Min reliability (0-1) [0.75]: ").strip()
    prefs['min_reliability'] = float(val) if val else 0.75
    
    val = input("Max mileage [80000]: ").strip()
    prefs['max_mileage'] = float(val) if val else 80000
    
    val = input("Ownership period in years [5]: ").strip()
    prefs['year'] = int(val) if val else 5
    
    val = input("How many results? [10]: ").strip()
    top_n = int(val) if val else 10
    
    return prefs, top_n


def main():
    try:
        prefs, top_n = get_preferences()
        
        print()
        print("=" * 50)
        print("Analyzing vehicles...")
        print("=" * 50)
        
        engine = CarRecommendationEngine()
        
        if engine.df is None or len(engine.df) == 0:
            print()
            print("ERROR: No data loaded!")
            print("Run: python src/data_integration.py first")
            return
        
        recs, explanations = engine.get_recommendations(prefs, top_n=top_n)
        
        if recs.empty:
            print()
            print("No cars matched your criteria :(")
            print("Try:")
            print("  - increasing budget")
            print("  - widening year range")
            print("  - lowering min requirements")
        else:
            engine.print_results(recs, explanations)
            
            print()
            save = input("Save to CSV? (y/n) [y]: ").strip().lower()
            if save != 'n':
                recs.to_csv('data/recommendations.csv', index=False)
                print("Saved to data/recommendations.csv")
    
    except KeyboardInterrupt:
        print("\n\nbye")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
