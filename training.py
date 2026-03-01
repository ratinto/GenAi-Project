"""
STEP 3: MODEL TRAINING
======================
Train Logistic Regression and Decision Tree models
"""

import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

def train_models():
    """Train and save ML models."""
    
    print("="*50)
    print("STEP 3: MODEL TRAINING")
    print("="*50)
    
    # Load data
    print("\n1. Loading data with features...")
    df = pd.read_csv('data_with_features.csv')
    print(f"   Loaded: {df.shape}")
    
    # Select features (INCLUDING MILEAGE!)
    print("\n2. Selecting features...")
    features = [
        'RPM', 'Speed', 'nGear', 'Throttle', 'Brake',
        'Mileage', 'Mileage_Normalized',  # KEY: Mileage features
        'Speed_Change', 'Throttle_Change', 
        'Hard_Braking', 'High_RPM', 'Full_Throttle',
        'RPM_Hours', 'Brake_Usage', 'High_Speed_Miles',  # Cumulative wear
        'Stress_Score'
    ]
    
    X = df[features].fillna(0)
    y = df['Needs_Maintenance']
    print(f"   Features selected: {len(features)}")
    
    # Split data
    print("\n3. Splitting data (80% train, 20% test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"   Training: {len(X_train)} samples")
    print(f"   Testing:  {len(X_test)} samples")
    
    # Scale features
    print("\n4. Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print("   ✓ Features scaled")
    
    # Train Model 1: Logistic Regression
    print("\n5. Training Logistic Regression...")
    lr_model = LogisticRegression(random_state=42, max_iter=1000)
    lr_model.fit(X_train_scaled, y_train)
    
    lr_pred = lr_model.predict(X_test_scaled)
    print(f"   ✓ Model trained")
    print(f"   Accuracy:  {accuracy_score(y_test, lr_pred):.3f}")
    print(f"   Precision: {precision_score(y_test, lr_pred):.3f}")
    print(f"   Recall:    {recall_score(y_test, lr_pred):.3f}")
    print(f"   F1 Score:  {f1_score(y_test, lr_pred):.3f}")
    
    # Train Model 2: Decision Tree
    print("\n6. Training Decision Tree...")
    dt_model = DecisionTreeClassifier(max_depth=5, random_state=42)
    dt_model.fit(X_train_scaled, y_train)
    
    dt_pred = dt_model.predict(X_test_scaled)
    print(f"   ✓ Model trained")
    print(f"   Accuracy:  {accuracy_score(y_test, dt_pred):.3f}")
    print(f"   Precision: {precision_score(y_test, dt_pred):.3f}")
    print(f"   Recall:    {recall_score(y_test, dt_pred):.3f}")
    print(f"   F1 Score:  {f1_score(y_test, dt_pred):.3f}")
    
    # Save models
    print("\n7. Saving models...")
    with open('logistic_model.pkl', 'wb') as f:
        pickle.dump(lr_model, f)
    print("   [OK] Saved: logistic_model.pkl")
    
    with open('tree_model.pkl', 'wb') as f:
        pickle.dump(dt_model, f)
    print("   [OK] Saved: tree_model.pkl")
    
    with open('scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    print("   [OK] Saved: scaler.pkl")
    
    with open('features.pkl', 'wb') as f:
        pickle.dump(features, f)
    print("   [OK] Saved: features.pkl")
    
    print(f"\n[OK] All models saved!")
    
    return lr_model, dt_model, scaler, features


if __name__ == "__main__":
    train_models()
    print("\n" + "="*50)
    print("STEP 3 COMPLETE [OK]")
    print("="*50)
    print("\nNext: Run 'python testing.py'")
