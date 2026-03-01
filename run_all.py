#!/usr/bin/env python3
"""
Run All Steps - Vehicle Maintenance Prediction System
Executes all steps in order: cleaning → feature engineering → training → testing
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and display status"""
    print("\n" + "="*70)
    print(f"[RUN] {description}")
    print("="*70)
    
    result = subprocess.run(command, shell=True)
    
    if result.returncode != 0:
        print(f"\n[ERROR] Error in: {description}")
        print(f"Command failed: {command}")
        sys.exit(1)
    
    print(f"[OK] {description} - COMPLETED")
    return result

def main():
    print("\n" + "="*70)
    print("[TARGET] VEHICLE MAINTENANCE PREDICTION SYSTEM")
    print("="*70)
    print("Running all steps automatically...\n")
    
    # Get the Python executable path
    python_cmd = sys.executable
    
    # Step 1: Data Cleaning
    run_command(
        f"{python_cmd} cleaning.py",
        "Step 1: Data Cleaning"
    )
    
    # Step 2: Feature Engineering
    run_command(
        f"{python_cmd} feature_engineering.py",
        "Step 2: Feature Engineering"
    )
    
    # Step 3: Model Training
    run_command(
        f"{python_cmd} training.py",
        "Step 3: Model Training"
    )
    
    # Step 4: Model Testing
    run_command(
        f"{python_cmd} testing.py",
        "Step 4: Model Testing"
    )
    
    # Final summary
    print("\n" + "="*70)
    print("[SUCCESS] ALL STEPS COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\n[DATA] Generated Files:")
    print("  [OK] cleaned_data.csv")
    print("  [OK] data_with_features.csv")
    print("  [OK] logistic_model.pkl")
    print("  [OK] tree_model.pkl")
    print("  [OK] scaler.pkl")
    print("  [OK] features.pkl")
    print("\n[WEB] To launch the web app, run:")
    print(f"  streamlit run app.py")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
