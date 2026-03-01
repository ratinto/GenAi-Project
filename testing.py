"""
STEP 4: MODEL TESTING
=====================
Test the trained models and see predictions
"""

import pandas as pd
import pickle
import numpy as np

def calculate_traction_health(speed, rpm):
    """Calculate traction health from speed and RPM."""
    # Convert speed from km/h to m/s
    speed_mps = speed * (1000/3600)
    
    # Estimate wheel angular velocity
    wheel_omega = (rpm / 60) * (2 * np.pi)
    
    # Effective rolling radius
    r_eff = speed_mps / (wheel_omega + 1e-6)
    
    # Slip ratio
    slip_ratio = ((wheel_omega * r_eff - speed_mps) / (speed_mps + 1e-6))
    
    # Traction health (normalized inverse slip)
    # IMPROVEMENT: Clamp to 0.95 max (real systems never perfect)
    traction_health = 1 - abs(slip_ratio)
    traction_health = max(0, min(0.95, traction_health))  # Max 0.95, not 1.00
    
    return traction_health

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
        
        # Create dataframe
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
