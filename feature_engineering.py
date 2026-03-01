"""
STEP 2: FEATURE ENGINEERING
===========================
Create physics-based features from cleaned telemetry data.
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

    # A. Traction Health
    # Convert speed from km/h to m/s
    df['Speed_mps'] = df['Speed'] * (1000/3600)

    # Estimate wheel angular velocity (assuming driven wheels)
    # If no wheel speed available, approximate using RPM & gear ratio (simplified)
    df['Wheel_Omega'] = (df['RPM'] / 60) * (2 * np.pi)

    # Effective rolling radius (dynamic approximation)
    df['R_eff'] = df['Speed_mps'] / (df['Wheel_Omega'] + 1e-6)

    # Slip Ratio
    df['Slip_Ratio'] = (
    (df['Wheel_Omega'] * df['R_eff'] - df['Speed_mps']) /
    (df['Speed_mps'] + 1e-6)
)

    # Traction Health Index (normalized inverse slip)
    # IMPROVEMENT: Clamp max to 0.95 (real systems never perfect)
    df['Traction_Health'] = 1 - df['Slip_Ratio'].abs()
    df['Traction_Health'] = df['Traction_Health'].clip(0, 0.95)  # Max 0.95, not 1.00

    # B. Change features (delta)
    df['Speed_Change'] = df['Speed'].diff().fillna(0)
    df['Throttle_Change'] = df['Throttle'].diff().fillna(0)
    print("   ✓ Change features (2)")
    
    # C. Stress indicators
    df['Hard_Braking'] = ((df['Speed_Change'] < -20) & (df['Brake'] == 1)).astype(int)
    df['High_RPM'] = (df['RPM'] > df['RPM'].quantile(0.90)).astype(int)
    df['Full_Throttle'] = (df['Throttle'] == 100).astype(int)
    
    # IMPROVEMENT A: Hard safety thresholds
    MAX_SAFE_RPM = 15000  # F1 max safe RPM
    df['RPM_Danger'] = (df['RPM'] > MAX_SAFE_RPM).astype(int)
    
    # IMPROVEMENT B: Detect inconsistent/dangerous combinations
    # High RPM + Low throttle = engine over-revving (dangerous!)
    df['Inconsistent_Combo'] = (
        ((df['RPM'] > 10000) & (df['Throttle'] < 30)) |  # High RPM, low throttle
        ((df['Speed'] < 100) & (df['RPM'] > 12000))       # Low speed, very high RPM
    ).astype(int)
    
    # 🔥 NEW CRITICAL FEATURES: Gear-Speed-RPM Physics
    # These features detect mechanically impossible combinations
    
    # Expected RPM based on speed and gear (simplified F1 gearbox ratios)
    # F1 gear ratios (approximate): G1=3.5, G2=2.5, G3=2.0, G4=1.6, G5=1.3, G6=1.1, G7=0.95, G8=0.85
    gear_ratios = {1: 3.5, 2: 2.5, 3: 2.0, 4: 1.6, 5: 1.3, 6: 1.1, 7: 0.95, 8: 0.85}
    df['Gear_Ratio'] = df['nGear'].map(gear_ratios).fillna(1.0)
    
    # Expected RPM = Speed * Gear_Ratio * constant (simplified)
    # At 100 km/h in gear 4, expect ~6500 RPM
    SPEED_TO_RPM_FACTOR = 100  # Calibration factor
    df['Expected_RPM'] = df['Speed'] * df['Gear_Ratio'] * SPEED_TO_RPM_FACTOR
    
    # RPM Deviation (how far from expected)
    df['RPM_Deviation'] = np.abs(df['RPM'] - df['Expected_RPM'])
    df['RPM_Deviation_Ratio'] = df['RPM_Deviation'] / (df['Expected_RPM'] + 1e-6)
    
    # Gear-Speed Mismatch Score (0=perfect, 1=severe mismatch)
    # If RPM is >2x or <0.5x expected, it's a mismatch
    df['Gear_Speed_Mismatch'] = np.where(
        (df['RPM_Deviation_Ratio'] > 1.0) |  # RPM way too high/low for gear-speed combo
        ((df['Speed'] < 50) & (df['nGear'] > 3)) |  # High gear at low speed
        ((df['Speed'] > 150) & (df['nGear'] < 3)),  # Low gear at high speed
        1, 0
    )
    
    # RPM per Gear (should increase with gear)
    df['RPM_per_Gear'] = df['RPM'] / (df['nGear'] + 1e-6)
    
    # Speed per Gear (should increase with gear)
    df['Speed_per_Gear'] = df['Speed'] / (df['nGear'] + 1e-6)
    
    # RPM to Speed Ratio (mechanical consistency)
    df['RPM_Speed_Ratio'] = df['RPM'] / (df['Speed'] + 1e-6)
    
    # Throttle-RPM interaction (high throttle should match RPM)
    df['Throttle_RPM_Product'] = df['Throttle'] * df['RPM'] / 1000000  # Normalized
    
    # Throttle & Brake simultaneously (driver error or data issue)
    df['Throttle_Brake_Conflict'] = ((df['Throttle'] > 20) & (df['Brake'] == 1)).astype(int)
    
    print("   ✓ Stress indicators (5 - added safety thresholds)")
    print("   ✓ Physics-based features (9 - gear-speed-RPM mechanics)")
    
    # D. Cumulative wear metrics
    df['RPM_Hours'] = (df['RPM'] / 60000).cumsum()  # Engine operating hours
    df['Brake_Usage'] = df['Brake'].cumsum()  # Total brake applications
    df['High_Speed_Miles'] = ((df['Speed'] > 200) * (df['Distance'].diff().fillna(0))).cumsum()
    print("   ✓ Cumulative wear (3)")
    
    # E. Stress score (with safety penalties)
    # IMPROVEMENT: Add penalties for dangerous conditions
    rpm_norm = df['RPM'] / df['RPM'].max()
    throttle_norm = df['Throttle'] / 100
    brake_norm = df['Brake']
    brake_usage_norm = df['Brake_Usage'] / (df['Brake_Usage'].max() + 1)
    
    # Base stress
    base_stress = (
        0.30 * rpm_norm +
        0.25 * throttle_norm +
        0.25 * brake_norm +
        0.20 * brake_usage_norm
    )
    
    # IMPROVEMENT: Penalty for dangerous RPM (>15000)
    rpm_penalty = np.where(df['RPM'] > 15000, 0.3, 0)  # +30% stress if RPM too high
    
    # IMPROVEMENT: Penalty for inconsistent combos
    inconsistent_penalty = df['Inconsistent_Combo'] * 0.25  # +25% stress
    
    # 🔥 NEW: Penalty for gear-speed-RPM mismatch
    mismatch_penalty = df['Gear_Speed_Mismatch'] * 0.35  # +35% stress for physics violations
    
    # NEW: Penalty for throttle-brake conflict
    conflict_penalty = df['Throttle_Brake_Conflict'] * 0.20  # +20% stress
    
    df['Stress_Score'] = base_stress + rpm_penalty + inconsistent_penalty + mismatch_penalty + conflict_penalty
    df['Stress_Score'] = df['Stress_Score'].clip(0, 1)  # Keep in [0, 1] range
    
    print("   ✓ Stress score with physics-based penalties (1)")
    
    # Create target variable (maintenance needed based on stress)
    print("\n3. Creating target variable...")
    
    # High stress = needs maintenance
    stress_threshold = df['Stress_Score'].quantile(0.70)
    
    df['Needs_Maintenance'] = (
        df['Stress_Score'] >= stress_threshold
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
