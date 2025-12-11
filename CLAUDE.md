# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Used car recommendation system for CPSC 583 (Knowledge Representation and Reasoning). Focuses on two main KR approaches:
- **Prolog** - Rule-based classification (requires SWI-Prolog)
- **RDF/OWL + SPARQL** - Semantic knowledge graph queries

Plus propositional logic for filtering and probabilistic methods for reliability.

## Commands

### Running the Application

```bash
./run_app.sh        # Streamlit web UI at localhost:8501
python3 cli.py      # Command line interface
```

### Testing Components

```bash
python3 src/prolog_reasoning.py      # Test Prolog rules
python3 src/ontology_builder.py      # Test SPARQL queries
python3 src/recommendation_engine.py # Test full pipeline
```

### Dependencies

```bash
pip3 install pandas numpy rdflib matplotlib streamlit
brew install swi-prolog  # Optional but recommended
```

## Architecture

### Data Flow

1. Propositional logic filters vehicles by user constraints
2. **Prolog** classifies vehicles into categories (facts generated, reasoning in .pl file)
3. **RDF ontology** built and queried with **SPARQL** for semantic matching
4. Results combined with weighted scoring (safety 30%, reliability 30%, price 25%, prolog bonus 15%)

### Key Files

- `src/recommendation_engine.py` - Main orchestrator
- `src/prolog_reasoning.py` - Generates facts, calls SWI-Prolog for reasoning
- `src/ontology_builder.py` - Builds RDF graph, runs SPARQL queries
- `prolog/car_rules.pl` - Expert classification rules (hand-written)
- `ontology/cars.ttl` - Generated RDF graph

### Prolog Integration

Rules in `prolog/car_rules.pl`:
- `excellent_choice/1`, `good_value/1`, `family_car/1`, `reliable_commuter/1`, `budget_pick/1`

Fact format: `car(Make, Model, Year, Price, Safety, Reliability, Mileage).`

Python generates facts, Prolog does the reasoning. Works without Prolog installed (skips classification).

### SPARQL Queries

Key queries in `ontology_builder.py`:
- `query_safe_vehicles(min_rating)` - Find vehicles by safety rating
- `query_reliable_manufacturers()` - Find makes with avg reliability >= 0.7
- `query_best_value(max_price, min_safety, min_reliability)` - Combined criteria

## Data Limitations

- ~36% have actual NHTSA safety ratings (rest default to 3.0)
- ~22% have complaint history for reliability
