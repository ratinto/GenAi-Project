"""
STEP 4: MODEL TESTING
=====================
Test the trained models and see predictions
"""

import pandas as pd
import pickle
import numpy as np

def test_models():
    """Test the trained models."""
    
    print("="*50)
    print("STEP 4: MODEL TESTING")
    print("="*50)
    
    # Load models
    print("\n1. Loading trained models...")
    with open('tree_model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    with open('features.pkl', 'rb') as f:
        features = pickle.load(f)
    print("   ✓ Models loaded")
    
    # Test examples
    print("\n2. Testing with example data...")
    
    test_cases = [
        {
            'name': 'Low Risk (Low Mileage)',
            'RPM': 6000, 'Speed': 100, 'nGear': 3, 'Throttle': 40, 'Brake': 0,
            'Mileage': 500, 'Mileage_Normalized': 0.1,
            'Speed_Change': 0, 'Throttle_Change': 0, 'Hard_Braking': 0, 
            'High_RPM': 0, 'Full_Throttle': 0,
            'RPM_Hours': 2, 'Brake_Usage': 10, 'High_Speed_Miles': 0,
            'Stress_Score': 0.2
        },
        {
            'name': 'Medium Risk (Moderate Mileage)',
            'RPM': 9000, 'Speed': 200, 'nGear': 5, 'Throttle': 70, 'Brake': 0,
            'Mileage': 3000, 'Mileage_Normalized': 0.5,
            'Speed_Change': 10, 'Throttle_Change': 5, 'Hard_Braking': 0, 
            'High_RPM': 0, 'Full_Throttle': 0,
            'RPM_Hours': 10, 'Brake_Usage': 50, 'High_Speed_Miles': 100,
            'Stress_Score': 0.5
        },
        {
            'name': 'High Risk (High Mileage + High Stress)',
            'RPM': 11500, 'Speed': 280, 'nGear': 7, 'Throttle': 100, 'Brake': 1,
            'Mileage': 5000, 'Mileage_Normalized': 0.9,
            'Speed_Change': -30, 'Throttle_Change': 20, 'Hard_Braking': 1, 
            'High_RPM': 1, 'Full_Throttle': 1,
            'RPM_Hours': 20, 'Brake_Usage': 150, 'High_Speed_Miles': 500,
            'Stress_Score': 0.85
        }
    ]
    
    print("\n" + "="*50)
    for test in test_cases:
        name = test.pop('name')
        
        # Create dataframe
        test_df = pd.DataFrame([test])[features]
        
        # Scale
        test_scaled = scaler.transform(test_df)
        
        # Predict
        prediction = model.predict(test_scaled)[0]
        risk_prob = model.predict_proba(test_scaled)[0][1]
        
        # Display
        print(f"\n[DATA] Test Case: {name}")
        print(f"   Mileage: {test['Mileage']:.0f} km")
        print(f"   RPM: {test['RPM']}, Speed: {test['Speed']}, Throttle: {test['Throttle']}%")
        print(f"   Prediction: {'[WARNING] NEEDS MAINTENANCE' if prediction == 1 else '[OK]'}")
        print(f"   Risk Score: {risk_prob*100:.0f}%")
        
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
        mileage = int(input("Enter Mileage km (e.g., 3000): "))
        rpm = int(input("Enter RPM (e.g., 9000): "))
        speed = int(input("Enter Speed km/h (e.g., 200): "))
        throttle = int(input("Enter Throttle % (e.g., 80): "))
        brake = int(input("Brake applied? (0=No, 1=Yes): "))
        
        # Calculate stress score with mileage
        mileage_norm = mileage / 5000  # Normalize to max expected
        stress = (0.25 * (rpm/15000) + 0.2 * (throttle/100) + 
                  0.2 * brake + 0.2 * min(mileage_norm, 1))
        
        # Create input
        user_test = {
            'RPM': rpm, 'Speed': speed, 'nGear': 4, 'Throttle': throttle, 'Brake': brake,
            'Mileage': mileage, 'Mileage_Normalized': min(mileage_norm, 1),
            'Speed_Change': 0, 'Throttle_Change': 0, 'Hard_Braking': 0, 
            'High_RPM': 1 if rpm > 10000 else 0, 
            'Full_Throttle': 1 if throttle == 100 else 0,
            'RPM_Hours': mileage / 100, 'Brake_Usage': mileage / 50, 
            'High_Speed_Miles': mileage * 0.3 if speed > 200 else 0,
            'Stress_Score': stress
        }
        
        test_df = pd.DataFrame([user_test])[features]
        test_scaled = scaler.transform(test_df)
        
        prediction = model.predict(test_scaled)[0]
        risk_prob = model.predict_proba(test_scaled)[0][1]
        
        print("\n" + "="*50)
        print("YOUR RESULT:")
        print("="*50)
        print(f"Mileage: {mileage} km")
        print(f"Prediction: {'[WARNING] NEEDS MAINTENANCE' if prediction == 1 else '[OK]'}")
        print(f"Risk Score: {risk_prob*100:.0f}%")
        
        if risk_prob >= 0.7:
            print(f"Status: [HIGH] RISK - Immediate maintenance recommended")
        elif risk_prob >= 0.4:
            print(f"Status: [MEDIUM] RISK - Monitor closely")
        else:
            print(f"Status: [LOW] RISK - Normal operation")
        print("="*50)
        
    except:
        print("\nSkipping interactive test...")


if __name__ == "__main__":
    test_models()
    print("\n" + "="*50)
    print("STEP 4 COMPLETE [OK]")
    print("="*50)
    print("\nNext: Run 'streamlit run app.py' for the UI")
