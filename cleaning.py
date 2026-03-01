"""
STEP 1: DATA CLEANING
====================
Clean and prepare the F1 telemetry data
"""

import pandas as pd
import numpy as np

def clean_data():
    """Load and clean the raw data."""
    
    print("="*50)
    print("STEP 1: DATA CLEANING")
    print("="*50)
    
    # Load data
    print("\n1. Loading data...")
    df = pd.read_csv('f1_telemetry.csv')
    print(f"   Loaded: {len(df)} rows, {len(df.columns)} columns")
    print(f"   Columns: {list(df.columns)}")
    
    # Check data
    print("\n2. Checking data quality...")
    print(f"   Missing values: {df.isnull().sum().sum()}")
    print(f"   Duplicates: {df.duplicated().sum()}")
    
    # Clean data
    print("\n3. Cleaning data...")
    
    # Convert Brake to numeric (True/False -> 1/0)
    df['Brake'] = df['Brake'].astype(int)
    print("   [OK] Converted Brake to numeric")
    
    # Fill any missing values
    df = df.fillna(0)
    print("   [OK] Filled missing values")
    
    # Remove duplicates
    df = df.drop_duplicates()
    print("   [OK] Removed duplicates")
    
    # Sort by time
    df = df.sort_values('SessionTime').reset_index(drop=True)
    print("   [OK] Sorted by time")
    
    # Save cleaned data
    df.to_csv('cleaned_data.csv', index=False)
    print(f"\n[OK] Cleaned data saved: cleaned_data.csv")
    print(f"   Final shape: {df.shape}")
    
    # Show sample
    print("\n[DATA] Sample of cleaned data:")
    print(df[['RPM', 'Speed', 'Throttle', 'Brake']].head())
    
    return df


if __name__ == "__main__":
    df = clean_data()
    print("\n" + "="*50)
    print("STEP 1 COMPLETE ✓")
    print("="*50)
    print("\nNext: Run 'python step2_feature_engineering.py'")
