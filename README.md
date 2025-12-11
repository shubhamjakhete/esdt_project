# Used Car Recommendation System
### CPSC 583 - Knowledge Representation and Reasoning
**Cameron Potvin, Shubham Jakhete, Jaiveer Kapadia**
California State University, Fullerton

---

## Overview

A used car recommendation system that uses knowledge representation to help users find reliable, safe vehicles within budget. We focus on two main KR approaches:

1. **Prolog Logic Programming** - Expert rules for vehicle classification
2. **RDF/OWL Ontology with SPARQL** - Semantic knowledge graph

Plus supporting components for constraint filtering and reliability estimation.

## Getting Started

### Prerequisites

```bash
pip3 install pandas numpy rdflib matplotlib streamlit
```

For Prolog reasoning (recommended):
```bash
brew install swi-prolog  # Mac
# or apt-get install swi-prolog on Linux
```

### Running the System

**Web interface** (easiest):
```bash
./run_app.sh
# then go to http://localhost:8501
```

**Command line**:
```bash
python3 cli.py
```

## Knowledge Representation Approaches

### 1. Prolog Logic Programming

Expert rules are defined in `prolog/car_rules.pl`. Python generates the facts from data, but **the actual reasoning happens in Prolog** at runtime.

Categories defined:
- `excellent_choice` - High reliability + safety + recent + low miles
- `good_value` - Reliable and safe but affordable
- `family_car` - Prioritizes safety
- `reliable_commuter` - Good for daily driving
- `budget_pick` - Cheapest decent options

Example rule:
```prolog
good_value(Car) :-
    high_reliability(Car),
    high_safety(Car),
    affordable(Car).
```

### 2. RDF/OWL Ontology with SPARQL

Vehicles are represented as RDF triples in a knowledge graph. **SPARQL queries** handle the semantic reasoning at runtime.

The ontology includes:
- Vehicle class with properties (price, safety, reliability, mileage)
- Manufacturer relationships
- Body type subclasses

Example SPARQL query:
```sparql
SELECT ?model ?make ?year ?price
WHERE {
    ?vehicle a car:Vehicle .
    ?vehicle car:safetyRating ?safety .
    ?vehicle car:reliabilityScore ?rel .
    FILTER(?safety >= 4.0 && ?rel >= 0.8)
}
```

### 3. Supporting Components

- **Propositional Logic** - Simple AND of constraints to filter dataset
- **Probabilistic Methods** - Reliability estimation from age and complaint data

## Data Sources

We integrated three datasets:
1. **Used Car Prices** from Kaggle (4,009 vehicles)
2. **NHTSA Safety Ratings** (11,028 crash test ratings)
3. **NHTSA Complaints Database** (~100k complaints)

Final integrated dataset: 5,181 vehicles

## Project Structure

```
├── app.py                 # Streamlit web interface
├── cli.py                 # Command line interface
├── src/
│   ├── recommendation_engine.py   # Main orchestration
│   ├── prolog_reasoning.py        # Prolog interface
│   ├── ontology_builder.py        # RDF/OWL + SPARQL
│   ├── propositional_logic.py     # Constraint filtering
│   └── probabilistic_reasoning.py # Reliability estimation
├── prolog/
│   ├── car_rules.pl       # Expert rules (hand-written)
│   └── car_facts.pl       # Generated from data at runtime
├── ontology/
│   └── cars.ttl           # Generated RDF graph
└── data/
    └── integrated_cars.csv
```

## How It Works

1. User sets preferences (price, year, safety requirements)
2. Propositional logic filters dataset to matching vehicles
3. Prolog evaluates expert rules to classify vehicles into categories
4. RDF ontology built and queried with SPARQL for semantic matching
5. Results combined with weighted scoring
6. Explanations show which categories each vehicle belongs to

## Known Limitations

- ~36% of vehicles have actual NHTSA safety ratings (rest default to 3.0)
- ~22% have complaint data for reliability scoring
- Prolog requires SWI-Prolog installation (system works without it, just loses rule-based classification)

## Testing Components

```bash
python3 src/prolog_reasoning.py      # Test Prolog rules
python3 src/ontology_builder.py      # Test SPARQL queries
python3 src/recommendation_engine.py # Test full pipeline
```
