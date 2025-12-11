"""
Data Integration Module
Integrates three real datasets

CPSC 583 Project
Authors: Cameron Potvin, Shubham Jakhete, Jaiveer Kapadia
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re

class DataIntegrator:
    def __init__(self, raw_data_dir='raw_data'):
        self.raw_data_dir = Path(raw_data_dir)
        self.integrated_data = None
        
    def load_datasets(self):
        # Load the three CSV datasets
        print("Loading datasets...")
        
        # Load Used Car Price Dataset
        price_file = self.raw_data_dir / 'used_car_prices.csv'
        if price_file.exists():
            self.price_data = pd.read_csv(price_file)
            print(f"Loaded price data: {len(self.price_data)} records")
        else:
            print(f"Warning: {price_file} not found")
            self.price_data = pd.DataFrame()
        
        # Load NHTSA Safety Ratings
        safety_file = self.raw_data_dir / 'nhtsa_safety_ratings.csv'
        if safety_file.exists():
            self.safety_data = pd.read_csv(safety_file, low_memory=False)
            print(f"Loaded safety data: {len(self.safety_data)} records")
        else:
            print(f"Warning: {safety_file} not found")
            self.safety_data = pd.DataFrame()
        
        # Load NHTSA Complaints
        complaints_file = self.raw_data_dir / 'nhtsa_complaints.csv'
        if complaints_file.exists():
            self.complaints_data = pd.read_csv(complaints_file, nrows=100000)
            print(f"Loaded complaints data: {len(self.complaints_data)} records")
        else:
            print(f"Warning: {complaints_file} not found")
            self.complaints_data = pd.DataFrame()
    
    def normalize_model_name(self, model_name):
        
        # Normalize model names for better matching (strips trim levels, colors, extra descriptors)
        
        if pd.isna(model_name):
            return ""
        
        model = str(model_name).upper().strip()
        
        # Remove common trim level indicators
        trim_patterns = [
            r'\bBASE\b', r'\bSE\b', r'\bSEL\b', r'\bLIMITED\b', r'\bSPORT\b',
            r'\bLX\b', r'\bEX\b', r'\bDX\b', r'\bLE\b', r'\bXLE\b', r'\bSR\b',
            r'\bLT\b', r'\bLS\b', r'\bLTZ\b', r'\bPREMIUM\b', r'\bPLUS\b',
            r'\bS\sLINE\b', r'\bLUXURY\b', r'\bTOURING\b', r'\bAWD\b', r'\bFWD\b',
            r'\b4WD\b', r'\b2WD\b', r'\bHYBRID\b', r'\bELECTRIC\b',
            r'\bDENALI\b', r'\bSLT\b', r'\bHIGHLAND\b', r'\bLARIAT\b',
            r'\bXLT\b', r'\bKING\sRANCH\b', r'\bPLATINUM\b',
            r'\bTRAILHAWK\b', r'\bLATITUDE\b', r'\bALTITUDE\b'
        ]
        
        for pattern in trim_patterns:
            model = re.sub(pattern, '', model)
        
        # Remove common descriptors
        model = re.sub(r'\bLONG\sRANGE\b', '', model)
        model = re.sub(r'\bDUAL\sCAB\b', '', model)
        model = re.sub(r'\bCREW\sCAB\b', '', model)
        model = re.sub(r'\bEXTENDED\sCAB\b', '', model)
        model = re.sub(r'\bREGULAR\sCAB\b', '', model)
        
        # Remove numbers that are part of trim (like 2.4L, 3.0)
        model = re.sub(r'\b\d+\.\d+L?\b', '', model)
        
        # Clean up extra spaces
        model = re.sub(r'\s+', ' ', model).strip()
        
        # Get first few words (the actual model name)
        words = model.split()
        if len(words) > 2:
            model = ' '.join(words[:2])
        
        return model
    
    def clean_price(self, price_str):
        # Clean price string to numeric value
        if pd.isna(price_str):
            return np.nan
        if isinstance(price_str, (int, float)):
            return float(price_str)
        cleaned = re.sub(r'[\$,]', '', str(price_str))
        try:
            return float(cleaned)
        except:
            return np.nan
    
    def clean_mileage(self, mileage_str):
        # Clean mileage string to numeric value
        if pd.isna(mileage_str):
            return np.nan
        if isinstance(mileage_str, (int, float)):
            return float(mileage_str)
        cleaned = re.sub(r'[,\s]', '', str(mileage_str))
        cleaned = re.sub(r'mi\.?', '', cleaned, flags=re.IGNORECASE)
        try:
            return float(cleaned)
        except:
            return np.nan
    
    def calculate_complaint_metrics(self):
        # Calculate reliability metrics from complaints data
        if self.complaints_data.empty:
            return pd.DataFrame()
        
        make_col = None
        model_col = None
        year_col = None
        
        for col in self.complaints_data.columns:
            col_lower = col.lower()
            if 'make' in col_lower and make_col is None:
                make_col = col
            if 'model' in col_lower and model_col is None:
                model_col = col
            if 'year' in col_lower and year_col is None:
                year_col = col
        
        if not all([make_col, model_col, year_col]):
            print(f"Warning: Could not find required columns in complaints data")
            return pd.DataFrame()
        
        complaints = self.complaints_data.copy()
        complaints[make_col] = complaints[make_col].str.strip().str.upper()
        complaints['model_norm'] = complaints[model_col].apply(self.normalize_model_name)
        
        complaints_agg = complaints.groupby(
            [make_col, 'model_norm', year_col]
        ).size().reset_index(name='complaint_count')
        
        print(f"Aggregated complaints for {len(complaints_agg)} vehicle combinations")
        return complaints_agg
    
    def integrate_datasets(self):
        # Integrate all three datasets into unified format
        print("\nIntegrating datasets...")
        
        if self.price_data.empty:
            print("Error: Price data is required for integration")
            return None
        
        integrated = self.price_data.copy()
        
        make_col = next((col for col in integrated.columns if 'make' in col.lower()), None)
        model_col = next((col for col in integrated.columns if 'model' in col.lower()), None)
        year_col = next((col for col in integrated.columns if 'year' in col.lower()), None)
        price_col = next((col for col in integrated.columns if 'price' in col.lower()), None)
        mileage_col = next((col for col in integrated.columns if 'mile' in col.lower() or 'milage' in col.lower()), None)
        
        if not all([make_col, model_col, year_col]):
            print("Error: Could not identify required columns")
            return None
        
        print(f"Using columns: make={make_col}, model={model_col}, year={year_col}")
        
        # Clean numeric columns
        if price_col:
            integrated['price'] = integrated[price_col].apply(self.clean_price)
            integrated = integrated[integrated['price'].notna()]
        
        if mileage_col:
            integrated['mileage'] = integrated[mileage_col].apply(self.clean_mileage)
        
        # Normalize names
        integrated['make'] = integrated[make_col].str.strip().str.upper()
        integrated['model_normalized'] = integrated[model_col].apply(self.normalize_model_name)
        integrated['year'] = pd.to_numeric(integrated[year_col], errors='coerce').astype('Int64')
        integrated = integrated[integrated['year'].notna()]
        
        # Keep original model name 
        integrated['model'] = integrated[model_col].str.strip().str.upper()
        
        # Merge with safety data
        integrated['overall_rating'] = 3.0  # Default
        
        if not self.safety_data.empty:
            safety = self.safety_data.copy()
            
            if all(col in safety.columns for col in ['MAKE', 'MODEL', 'MODEL_YR', 'OVERALL_STARS']):
                safety['make_norm'] = safety['MAKE'].str.strip().str.upper()
                safety['model_norm'] = safety['MODEL'].apply(self.normalize_model_name)
                safety['year_norm'] = pd.to_numeric(safety['MODEL_YR'], errors='coerce').astype('Int64')
                safety['overall_rating'] = pd.to_numeric(safety['OVERALL_STARS'], errors='coerce')
                
                safety_merge = safety[['make_norm', 'model_norm', 'year_norm', 'overall_rating']].copy()
                safety_merge = safety_merge[safety_merge['overall_rating'].notna()]
                
                print(f"Prepared {len(safety_merge)} safety records for merging")
                print(f"Sample normalized safety models: {safety_merge['model_norm'].head(10).tolist()}")
                
                # Merge using normalized names
                integrated = pd.merge(
                    integrated,
                    safety_merge,
                    left_on=['make', 'model_normalized', 'year'],
                    right_on=['make_norm', 'model_norm', 'year_norm'],
                    how='left',
                    suffixes=('_old', '')
                )
                
                # Clean up
                integrated.drop(['make_norm', 'model_norm', 'year_norm'], axis=1, inplace=True, errors='ignore')
                
                if 'overall_rating_old' in integrated.columns:
                    integrated['overall_rating'] = integrated['overall_rating'].fillna(integrated['overall_rating_old'])
                    integrated.drop('overall_rating_old', axis=1, inplace=True)
                
                integrated['overall_rating'] = integrated['overall_rating'].fillna(3.0)
                
                safety_matches = (integrated['overall_rating'] != 3.0).sum()
                print(f"Merged safety ratings: {safety_matches} matches found")
                
                # Show some matches for debugging
                matched = integrated[integrated['overall_rating'] != 3.0][['make', 'model', 'model_normalized', 'year', 'overall_rating']].head(10)
                print(f"Sample matches:\n{matched}")
        
        # Add complaint metrics
        if not self.complaints_data.empty:
            complaints_metrics = self.calculate_complaint_metrics()
            if not complaints_metrics.empty:
                comp_cols = complaints_metrics.columns.tolist()
                comp_make = comp_cols[0]
                comp_model_norm = 'model_norm'
                comp_year = comp_cols[2]
                
                integrated = pd.merge(
                    integrated,
                    complaints_metrics,
                    left_on=['make', 'model_normalized', 'year'],
                    right_on=[comp_make, comp_model_norm, comp_year],
                    how='left'
                )
                
                # Clean up duplicate columns
                for col in integrated.columns:
                    if col.endswith('_x') or col.endswith('_y'):
                        if col.endswith('_x'):
                            base = col[:-2]
                            if f'{base}_y' in integrated.columns:
                                integrated[base] = integrated[col].fillna(integrated[f'{base}_y'])
                                integrated.drop([col, f'{base}_y'], axis=1, inplace=True)
                
                complaint_matches = integrated['complaint_count'].notna().sum()
                print(f"Merged complaints data: {complaint_matches} matches found")
                
                integrated['complaint_count'] = integrated['complaint_count'].fillna(0)
                
                max_complaints = integrated['complaint_count'].max()
                if max_complaints > 0:
                    integrated['reliability_score'] = 1 - (integrated['complaint_count'] / (max_complaints + 100))
                else:
                    integrated['reliability_score'] = 1.0
                
                integrated['reliability_score'] = integrated['reliability_score'].clip(0, 1)
        else:
            integrated['complaint_count'] = 0
            integrated['reliability_score'] = 1.0
        
        # Calculate derived metrics
        current_year = 2024
        integrated['age'] = current_year - integrated['year']
        integrated['depreciation_rate'] = integrated['age'] * 0.15
        
        # Keep essential columns
        essential_cols = ['make', 'model', 'year', 'price', 'mileage', 'overall_rating', 
                         'complaint_count', 'reliability_score', 'age', 'depreciation_rate']
        
        for col in integrated.columns:
            if col not in essential_cols:
                if any(keyword in col.lower() for keyword in ['fuel', 'engine', 'transmission', 'color', 'accident', 'title']):
                    essential_cols.append(col)
        
        integrated = integrated[[col for col in essential_cols if col in integrated.columns]]
        
        self.integrated_data = integrated
        print(f"\nIntegration complete: {len(integrated)} records")
        
        print(f"\nSample statistics:")
        print(f"  Price range: ${integrated['price'].min():,.0f} - ${integrated['price'].max():,.0f}")
        print(f"  Year range: {integrated['year'].min()} - {integrated['year'].max()}")
        print(f"  Safety rating range: {integrated['overall_rating'].min():.1f} - {integrated['overall_rating'].max():.1f}")
        print(f"  Vehicles with safety > 3.0: {(integrated['overall_rating'] > 3.0).sum()}")
        
        return integrated
    
    def save_integrated_data(self, output_file='data/integrated_cars.csv'):
        # Save integrated dataset
        if self.integrated_data is None:
            return
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.integrated_data.to_csv(output_path, index=False)
        print(f"\nSaved integrated data to {output_path}")

def main():
    # Main integration workflow
    print("=== Used Car Data Integration ===\n")
    
    integrator = DataIntegrator()
    integrator.load_datasets()
    integrated = integrator.integrate_datasets()
    
    if integrated is not None:
        integrator.save_integrated_data()

if __name__ == '__main__':
    main()
