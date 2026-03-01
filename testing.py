"""
STEP 4: MODEL TESTING
=====================
Test the trained models and see predictions
"""

import pandas as pd
import pickle
import numpy as np

def calculate_traction_health(speed, rpm):
    """Calculate traction health from speed and RPM using fixed tire radius."""
    # F1 tire radius ~0.33m
    r_eff = 0.33  # Fixed tire radius in meters
    
    # Convert speed from km/h to m/s
    speed_mps = speed * (1000/3600)
    
    # Estimate wheel RPM (typical F1 gearing: engine RPM / 8 for wheel RPM)
    wheel_rpm = rpm / 8
    
    # Calculate wheel angular velocity (rad/s)
    wheel_omega = (wheel_rpm / 60) * (2 * np.pi)
    
    # Expected speed from wheel rotation
    expected_speed = wheel_omega * r_eff
    
    # Slip ratio calculation
    if expected_speed > 0:
        slip_ratio = abs((expected_speed - speed_mps) / expected_speed)
    else:
        slip_ratio = 0
    
    # Traction health (inverse of slip, normalized)
    # Good traction = low slip (close to 1.0)
    # Poor traction = high slip (close to 0.0)
    traction_health = max(0.3, min(1.0, 1.0 - slip_ratio))
    
    return traction_health

def calculate_physics_features(data):
    """Calculate physics-based features for a single test case."""
    rpm = data['RPM']
    speed = data['Speed']
    gear = data['nGear']
    throttle = data['Throttle']
    brake = data['Brake']
    
    # 1. Gear Ratio (approximation)
    data['Gear_Ratio'] = rpm / (speed + 1) if speed > 0 else 0
    
    # 2. Expected RPM based on gear and speed
    # F1 typical: gear 1-8, speed range 0-350 km/h
    if gear > 0:
        data['Expected_RPM'] = speed * gear * 30  # Rough approximation
    else:
        data['Expected_RPM'] = 0
    
    # 3. RPM Deviation
    data['RPM_Deviation'] = abs(rpm - data['Expected_RPM'])
    
    # 4. RPM Deviation Ratio
    if data['Expected_RPM'] > 0:
        data['RPM_Deviation_Ratio'] = data['RPM_Deviation'] / data['Expected_RPM']
    else:
        data['RPM_Deviation_Ratio'] = 0
    
    # 5. Gear-Speed Mismatch (categorical flag)
    # Flag impossible combinations
    if (speed > 200 and gear <= 4) or (speed < 50 and gear > 5):
        data['Gear_Speed_Mismatch'] = 1
    else:
        data['Gear_Speed_Mismatch'] = 0
    
    # 6. RPM per Gear
    data['RPM_per_Gear'] = rpm / (gear + 1)
    
    # 7. Speed per Gear
    data['Speed_per_Gear'] = speed / (gear + 1)
    
    # 8. RPM-Speed Ratio
    data['RPM_Speed_Ratio'] = rpm / (speed + 1)
    
    # 9. Throttle-RPM Product (stress indicator)
    data['Throttle_RPM_Product'] = (throttle / 100) * (rpm / 13000)
    
    # 10. Throttle-Brake Conflict
    if throttle > 50 and brake > 50:
        data['Throttle_Brake_Conflict'] = 1
    else:
        data['Throttle_Brake_Conflict'] = 0
    
    return data

def test_models():
    """Test the trained models."""
    
    print("="*50)
    print("STEP 4: MODEL TESTING")
    print("="*50)
    
    # Load models
    print("\n1. Loading trained models...")
    with open('tree_model.pkl', 'rb') as f:
        tree_model = pickle.load(f)
    with open('logistic_model.pkl', 'rb') as f:
        lr_model = pickle.load(f)
    with open('scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    with open('features.pkl', 'rb') as f:
        features = pickle.load(f)
    print("   [OK] Models loaded")
    print("   [OK] Decision Tree: Binary prediction (accurate)")
    print("   [OK] Logistic Regression: Risk probability (nuanced)")
    print(f"   [OK] Features: {features}")
    
    # Test examples
    print("\n2. Testing with example data...")
    
    test_cases = [
        {
            'name': 'Low Risk (Low Stress)',
            'RPM': 6000, 'Speed': 100, 'nGear': 3, 'Throttle': 40, 'Brake': 0,
            'Speed_Change': 0, 'Throttle_Change': 0, 'Hard_Braking': 0, 
            'High_RPM': 0, 'Full_Throttle': 0,
            'RPM_Danger': 0, 'Inconsistent_Combo': 0,
            'RPM_Hours': 2, 'Brake_Usage': 10, 'High_Speed_Miles': 0,
            'Stress_Score': 0.2
        },
        {
            'name': 'Medium Risk (Moderate Stress)',
            'RPM': 9000, 'Speed': 200, 'nGear': 5, 'Throttle': 70, 'Brake': 0,
            'Speed_Change': 10, 'Throttle_Change': 5, 'Hard_Braking': 0, 
            'High_RPM': 0, 'Full_Throttle': 0,
            'RPM_Danger': 0, 'Inconsistent_Combo': 0,
            'RPM_Hours': 10, 'Brake_Usage': 50, 'High_Speed_Miles': 100,
            'Stress_Score': 0.5
        },
        {
            'name': 'High Risk (High Stress)',
            'RPM': 11500, 'Speed': 280, 'nGear': 7, 'Throttle': 100, 'Brake': 1,
            'Speed_Change': -30, 'Throttle_Change': 20, 'Hard_Braking': 1, 
            'High_RPM': 1, 'Full_Throttle': 1,
            'RPM_Danger': 0, 'Inconsistent_Combo': 0,
            'RPM_Hours': 20, 'Brake_Usage': 150, 'High_Speed_Miles': 500,
            'Stress_Score': 0.85
        },
        {
            'name': 'DANGEROUS (Inconsistent Combo - High RPM, Low Throttle)',
            'RPM': 19000, 'Speed': 150, 'nGear': 4, 'Throttle': 10, 'Brake': 0,
            'Speed_Change': 0, 'Throttle_Change': 0, 'Hard_Braking': 0, 
            'High_RPM': 1, 'Full_Throttle': 0,
            'RPM_Danger': 1, 'Inconsistent_Combo': 1,  # FLAGGED!
            'RPM_Hours': 15, 'Brake_Usage': 80, 'High_Speed_Miles': 50,
            'Stress_Score': 0.9
        }
    ]
    
    print("\n" + "="*50)
    for test in test_cases:
        name = test.pop('name')
        
        # Calculate traction health
        test['Traction_Health'] = calculate_traction_health(test['Speed'], test['RPM'])
        
        # Calculate physics-based features
        test = calculate_physics_features(test)
        
        # Create dataframe with all features
        test_df = pd.DataFrame([test])[features]
        
        # Scale
        test_scaled = scaler.transform(test_df)
        
        # Predict: Use Decision Tree for binary, Logistic Regression for risk
        prediction = tree_model.predict(test_scaled)[0]
        risk_prob = lr_model.predict_proba(test_scaled)[0][1]
        
        # Display
        print(f"\n[DATA] Test Case: {name}")
        print(f"   RPM: {test['RPM']}, Speed: {test['Speed']}, Throttle: {test['Throttle']}%")
        print(f"   Traction Health: {test['Traction_Health']:.2f}")
        print(f"   Prediction: {'[WARNING] NEEDS MAINTENANCE' if prediction == 1 else '[OK] NO MAINTENANCE NEEDED'}")
        print(f"   Risk Score: {risk_prob*100:.1f}%")
        
        if risk_prob >= 0.7:
            print(f"   Status: [HIGH] RISK")
        elif risk_prob >= 0.4:
            print(f"   Status: [MEDIUM] RISK")
        else:
            print(f"   Status: [LOW] RISK")
    
    print("\n" + "="*50)
    print("\n[OK] Testing complete!")
    
    # Interactive testing
    print("\n" + "="*50)
    print("INTERACTIVE TEST")
    print("="*50)
    print("\nTry your own values:")
    
    try:
        rpm = int(input("Enter RPM (e.g., 9000): "))
        speed = int(input("Enter Speed km/h (e.g., 200): "))
        throttle = int(input("Enter Throttle % (e.g., 80): "))
        brake = int(input("Brake applied? (0=No, 1=Yes): "))
        
        # Calculate traction health
        traction_health = calculate_traction_health(speed, rpm)
        
        # IMPROVEMENT A: Check hard safety thresholds
        MAX_SAFE_RPM = 15000
        rpm_danger = 1 if rpm > MAX_SAFE_RPM else 0
        
        # IMPROVEMENT B: Detect inconsistent/dangerous combinations
        inconsistent_combo = 1 if (
            (rpm > 10000 and throttle < 30) or  # High RPM, low throttle
            (speed < 100 and rpm > 12000)        # Low speed, very high RPM
        ) else 0
        
        # Calculate stress score with safety penalties
        rpm_norm = rpm / 15000
        throttle_norm = throttle / 100
        brake_norm = brake
        
        base_stress = (
            0.30 * rpm_norm +
            0.25 * throttle_norm +
            0.25 * brake_norm +
            0.20 * 0.5  # Assume moderate brake usage
        )
        
        # Add penalties
        rpm_penalty = 0.3 if rpm > 15000 else 0
        inconsistent_penalty = inconsistent_combo * 0.25
        
        stress = min(base_stress + rpm_penalty + inconsistent_penalty, 1.0)
        
        # Create input
        user_test = {
            'RPM': rpm, 'Speed': speed, 'nGear': 4, 'Throttle': throttle, 'Brake': brake,
            'Traction_Health': traction_health,
            'Speed_Change': 0, 'Throttle_Change': 0, 'Hard_Braking': 0, 
            'High_RPM': 1 if rpm > 10000 else 0, 
            'Full_Throttle': 1 if throttle == 100 else 0,
            'RPM_Danger': rpm_danger,
            'Inconsistent_Combo': inconsistent_combo,
            'RPM_Hours': 10, 'Brake_Usage': 50, 
            'High_Speed_Miles': 100 if speed > 200 else 0,
            'Stress_Score': stress
        }
        
        test_df = pd.DataFrame([user_test])[features]
        test_scaled = scaler.transform(test_df)
        
        # Use Decision Tree for prediction, Logistic Regression for risk
        prediction = tree_model.predict(test_scaled)[0]
        risk_prob = lr_model.predict_proba(test_scaled)[0][1]
        
        print("\n" + "="*50)
        print("YOUR RESULT:")
        print("="*50)
        print(f"   Traction Health: {traction_health:.2f} (max 0.95)")
        print(f"   Stress Score: {stress:.2f}")
        
        # Show warnings for dangerous conditions
        if rpm_danger:
            print(f"   ⚠️  RPM DANGER: {rpm} > 15000 (UNSAFE!)")
        if inconsistent_combo:
            print(f"   ⚠️  INCONSISTENT: High RPM ({rpm}) with low throttle ({throttle}%)")
        
        print(f"   Prediction: {'[WARNING] NEEDS MAINTENANCE' if prediction == 1 else '[OK] NO MAINTENANCE NEEDED'}")
        print(f"   Risk Score: {risk_prob*100:.1f}% (from Logistic Regression)")
        
        if risk_prob >= 0.7:
            print(f"   Status: [HIGH] RISK - Schedule maintenance immediately!")
        elif risk_prob >= 0.4:
            print(f"   Status: [MEDIUM] RISK - Monitor closely")
        else:
            print(f"   Status: [LOW] RISK - Vehicle acceptable (but never 0% risk)")
            
    except KeyboardInterrupt:
        print("\n\n[OK] Testing cancelled by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")

if __name__ == "__main__":
    test_models()
    print("\n" + "="*50)
    print("STEP 4 COMPLETE [OK]")
    print("="*50)
    print("\nNext: Run 'streamlit run app.py'")
