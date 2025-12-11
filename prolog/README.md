# Prolog Knowledge Base

## Overview

This directory contains the Prolog rules for rule-based car classification.

### Files

- `car_rules.pl` - The expert rules (hand-written)
- `car_facts.pl` - Generated at runtime from filtered vehicles

### How it works

1. User sets preferences in the UI
2. Propositional logic filters dataset down to matching cars
3. `prolog_reasoning.py` generates `car_facts.pl` with those cars
4. Prolog loads both files and evaluates which rules each car satisfies
5. Cars get tagged with categories like "good_value", "family_car", etc.

### Car fact format

```prolog
car('TOYOTA', 'CAMRY', 2020, 18000.0, 5.0, 0.9, 35000.0).
%   Make     Model   Year  Price  Safety Rel   Mileage
```

### Rules defined

- `excellent_choice/1` - high reliability + safety + recent + low miles
- `good_value/1` - reliable + safe + affordable
- `family_car/1` - prioritizes safety
- `reliable_commuter/1` - reliable + low mileage + affordable
- `budget_pick/1` - cheap but still decent

### Requirements

You need SWI-Prolog installed:

```bash
brew install swi-prolog  # Mac
sudo apt-get install swi-prolog  # Ubuntu/Debian
```

If Prolog isn't installed, the system still works - you just won't get the rule-based classifications.

### Testing

```bash
python3 src/prolog_reasoning.py
```
