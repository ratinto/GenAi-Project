# Vehicle Maintenance Prediction System

## Hiraeth F1
🚀 [Hosted Link](https://hiraeth-f1.onrender.com/)

## Project Overview

Predicts vehicle maintenance needs using F1 telemetry data with Machine Learning.

### Requirements Met

[✓] **Input:** Vehicle telemetry/maintenance CSV (`f1_telemetry.csv`)  
[✓] **Output:** Maintenance risk score/prediction (0-100% risk)  
[✓] **Metrics:** Explanation of contributing factors (mileage, RPM, stress score, brake wear, etc.)

## How to Run

### Option 1: Run All At Once (Recommended)

```bash
python run_all.py
```

This automatically runs all 4 steps: cleaning → features → training → testing

### Option 2: Run Manually (Step by Step)

**Run these commands one by one:**

```bash
# Step 1: Clean the data
python cleaning.py

# Step 2: Create features
python feature_engineering.py

# Step 3: Train models
python training.py

# Step 4: Test models (optional)
python testing.py

# Step 5: Launch web app
streamlit run app.py
```

### What Each Script Does:

1. **cleaning.py** - Cleans raw F1 data → outputs `cleaned_data.csv`
2. **feature_engineering.py** - Creates 16 features including mileage → outputs `data_with_features.csv`
3. **training.py** - Trains Logistic Regression & Decision Tree → saves models as `.pkl` files
4. **testing.py** - Tests models with examples (optional)
5. **app.py** - Streamlit web interface with **2 modes:**
   - [MANUAL] Manual Input: Enter values one at a time
   - [UPLOAD] CSV Upload: Upload file & predict all rows at once

### Streamlit App Features:

**Mode 1: Manual Input**
- Enter telemetry values (Mileage, RPM, Speed, etc.)
- Get instant prediction with risk score
- See contributing factors (what's causing the risk)
- Get recommendations

**Mode 2: CSV Upload**
- Upload your CSV file
- Automatically predicts for ALL rows
- Shows summary statistics & risk distribution
- Download results as CSV file
- No manual entry needed

## Features Created

**16 Features Total** (including mileage-based features)

### Core Telemetry:
1. **RPM** - Engine speed
2. **Speed** - Vehicle speed (km/h)
3. **nGear** - Current gear
4. **Throttle** - Accelerator position (%)
5. **Brake** - Brake status (0/1)

### [KEY] Mileage Features:
6. **Mileage** - Total distance traveled (km)
7. **Mileage_Normalized** - Normalized mileage (0-1)

### Change Features:
8. **Speed_Change** - Speed delta
9. **Throttle_Change** - Throttle delta

### Stress Indicators:
10. **Hard_Braking** - Emergency braking events
11. **High_RPM** - High engine stress
12. **Full_Throttle** - Maximum acceleration

### Cumulative Wear (based on mileage):
13. **RPM_Hours** - Engine operating hours
14. **Brake_Usage** - Total brake applications
15. **High_Speed_Miles** - Distance at high speed

### Combined:
16. **Stress_Score** - Weighted score including mileage

## Models

- **Logistic Regression**: ~93% accuracy
- **Decision Tree**: ~98% accuracy [BEST]

**Key Innovation:** Uses **mileage** to predict component wear over time

## Project Structure

```
GenAi/
├── f1_telemetry.csv         # Input data
├── run_all.py               # [*] Run everything at once
├── cleaning.py              # Data cleaning
├── feature_engineering.py   # Feature creation
├── training.py              # Model training
├── testing.py               # Model testing
├── app.py                   # Streamlit app (interactive)
└── requirements.txt         # Dependencies
```

## For Capstone Project

This covers all Milestone 1 requirements:
- [✓] Data preprocessing
- [✓] Feature engineering (16 features including mileage)
- [✓] Logistic Regression model
- [✓] Decision Tree model
- [✓] Model evaluation (Accuracy, Precision, Recall, F1)
- [✓] Streamlit UI
- [✓] Maintenance risk predictions with mileage-based wear

### How Requirements Are Met:

| Requirement | Implementation |
|-------------|----------------|
| **Input:** Vehicle telemetry/maintenance CSV | [✓] `f1_telemetry.csv` with 285 records |
| **Output:** Maintenance risk score/prediction | [✓] 0-100% risk score + binary prediction |
| **Metrics:** Explanation of contributing factors | [✓] Shows: Mileage, RPM, Speed, Throttle, Brake, Stress Score |

The app displays:
- **Risk Score**: 0-100% (e.g., "HIGH RISK: 85%")
- **Contributing Factors**: Lists what's causing the risk (mileage, high RPM, speed, etc.)
- **Component Details**: Engine wear, brake wear, cumulative stress
- **Recommendations**: What action to take based on the risk

## Quick Start

**Run everything at once:**
```bash
python run_all.py
streamlit run app.py
```

**Or run manually:**
```bash
python cleaning.py
python feature_engineering.py
python training.py
python testing.py
streamlit run app.py
```

---

Built with Scikit-learn | Logistic Regression & Decision Tree
