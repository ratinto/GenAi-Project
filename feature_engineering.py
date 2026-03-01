"""
STEP 2: FEATURE ENGINEERING
===========================
Create features from the cleaned data
"""

import pandas as pd
import numpy as np

def engineer_features():
    """Create features for the model."""
    
    print("="*50)
    print("STEP 2: FEATURE ENGINEERING")
    print("="*50)
    
    # Load cleaned data
    print("\n1. Loading cleaned data...")
    df = pd.read_csv('cleaned_data.csv')
    print(f"   Loaded: {df.shape}")
    
    # Create features
    print("\n2. Creating features...")
    
    # A. Mileage (cumulative distance - KEY FEATURE!)
    df['Mileage'] = df['Distance']  # Distance is already cumulative in F1 data
    df['Mileage_Normalized'] = df['Mileage'] / df['Mileage'].max()
    print("   ✓ Mileage features (2)")
    
    # B. Change features (delta)
    df['Speed_Change'] = df['Speed'].diff().fillna(0)
    df['Throttle_Change'] = df['Throttle'].diff().fillna(0)
    print("   ✓ Change features (2)")
    
    # C. Stress indicators
    df['Hard_Braking'] = ((df['Speed_Change'] < -20) & (df['Brake'] == 1)).astype(int)
    df['High_RPM'] = (df['RPM'] > df['RPM'].quantile(0.90)).astype(int)
    df['Full_Throttle'] = (df['Throttle'] == 100).astype(int)
    print("   ✓ Stress indicators (3)")
    
    # D. Cumulative wear metrics (based on mileage)
    df['RPM_Hours'] = (df['RPM'] / 60000).cumsum()  # Engine operating hours
    df['Brake_Usage'] = df['Brake'].cumsum()  # Total brake applications
    df['High_Speed_Miles'] = ((df['Speed'] > 200) * (df['Distance'].diff().fillna(0))).cumsum()
    print("   ✓ Cumulative wear (3)")
    
    # E. Stress score (includes mileage!)
    df['Stress_Score'] = (
        0.25 * (df['RPM'] / df['RPM'].max()) +
        0.20 * (df['Throttle'] / 100) +
        0.20 * df['Brake'] +
        0.20 * df['Mileage_Normalized'] +  # Mileage contributes to stress!
        0.15 * (df['Brake_Usage'] / (df['Brake_Usage'].max() + 1))
    )
    print("   ✓ Stress score with mileage (1)")
    
    # Create target variable (maintenance needed based on stress + mileage)
    print("\n3. Creating target variable...")
    
    # High stress OR high mileage = needs maintenance
    stress_threshold = df['Stress_Score'].quantile(0.70)
    mileage_threshold = df['Mileage'].quantile(0.75)
    
    df['Needs_Maintenance'] = (
        (df['Stress_Score'] >= stress_threshold) | 
        (df['Mileage'] >= mileage_threshold)
    ).astype(int)
    
    maintenance_count = df['Needs_Maintenance'].sum()
    maintenance_pct = maintenance_count / len(df) * 100
    print(f"   [OK] Target created")
    print(f"   [OK] Maintenance needed: {maintenance_count}/{len(df)} ({maintenance_pct:.1f}%)")
    
    # Save
    df.to_csv('data_with_features.csv', index=False)
    print(f"\n[OK] Features saved: data_with_features.csv")
    print(f"   Total features: {len(df.columns)}")
    
    # Show sample
    print("\n[DATA] Sample features:")
    print(df[['RPM', 'Stress_Score', 'Needs_Maintenance']].head())
    
    return df


if __name__ == "__main__":
    df = engineer_features()
    print("\n" + "="*50)
    print("STEP 2 COMPLETE [OK]")
    print("="*50)
    print("\nNext: Run 'python step3_training.py'")
