"""
STREAMLIT APP - Vehicle Maintenance Predictor
==============================================
Web interface with Manual Input & CSV Upload modes
"""

import streamlit as st
import pandas as pd
import pickle
import io
import numpy as np
from datetime import datetime

# Page config
st.set_page_config(page_title="Maintenance Predictor", page_icon="🚗", layout="wide")

# Load models - v2 with 27 physics features (cache busted)
@st.cache_resource(hash_funcs={type(lambda: None): lambda _: None})
def load_models():
    try:
        with open('tree_model.pkl', 'rb') as f:
            tree_model = pickle.load(f)
        with open('logistic_model.pkl', 'rb') as f:
            lr_model = pickle.load(f)
        with open('scaler.pkl', 'rb') as f:
            scaler = pickle.load(f)
        with open('features.pkl', 'rb') as f:
            features_list = pickle.load(f)
        # Verify we have the right number of features (should be 27)
        if len(features_list) != 27:
            st.warning(f"⚠️ Model has {len(features_list)} features, expected 27. Please retrain!")
        return tree_model, lr_model, scaler, features_list
    except Exception as e:
        st.error(f"Error loading models: {e}")
        return None, None, None, None

def calculate_traction_health(speed, rpm):
    """Calculate traction health from speed and RPM - measures tire slip."""
    # F1 tire effective radius approximately 0.33m
    r_eff = 0.33  # Fixed effective wheel radius in meters
    
    speed_mps = speed * (1000/3600)  # Convert km/h to m/s
    wheel_rpm = rpm / 8  # Approximate wheel RPM (engine RPM / average gear ratio)
    wheel_omega = (wheel_rpm / 60) * (2 * np.pi)  # Wheel angular velocity (rad/s)
    
    # Expected speed from wheel rotation
    expected_speed = wheel_omega * r_eff
    
    # Slip ratio: difference between wheel speed and vehicle speed
    if speed_mps > 0.1:  # Avoid division by zero
        slip_ratio = (expected_speed - speed_mps) / speed_mps
    else:
        slip_ratio = 0 if wheel_rpm < 100 else 1.0  # Burnout detection
    
    # Traction health decreases with slip
    traction_health = 1 - abs(slip_ratio)
    traction_health = max(0.3, min(1.0, traction_health))  # Range: 0.3 to 1.0
    return traction_health

# ============================================================================
# PHYSICS VALIDATION LAYER - Added for robustness
# ============================================================================

def validate_physics(rpm, speed, gear, throttle, brake):
    """
    Validate telemetry against mechanical physics.
    Returns: (is_valid, violations, severity)
    """
    violations = []
    severity = 0.0
    
    # F1 gear ratios
    gear_ratios = {1: 3.5, 2: 2.5, 3: 2.0, 4: 1.6, 5: 1.3, 6: 1.1, 7: 0.95, 8: 0.85}
    gear_ratio = gear_ratios.get(gear, 1.0)
    
    # 1. Check gear-speed-RPM consistency
    expected_rpm = speed * gear_ratio * 100
    rpm_deviation = abs(rpm - expected_rpm) / (expected_rpm + 1e-6)
    
    if rpm_deviation > 1.5:
        violations.append("EXTREME_RPM_MISMATCH")
        severity = max(severity, 0.9)
    elif rpm_deviation > 0.7:
        violations.append("RPM_MISMATCH")
        severity = max(severity, 0.7)
    
    # 2. Check impossible gear-speed combos
    if speed < 50 and gear > 3:
        violations.append("HIGH_GEAR_LOW_SPEED")
        severity = max(severity, 0.7)
    
    if speed > 200 and gear <= 4:
        violations.append("LOW_GEAR_HIGH_SPEED")
        severity = max(severity, 0.8)
    
    # 3. Check throttle-brake conflict
    if throttle > 20 and brake == 1:
        violations.append("THROTTLE_BRAKE_CONFLICT")
        severity = max(severity, 0.5)
    
    # 4. Check extreme RPM
    if rpm > 15000:
        violations.append("EXTREME_RPM")
        severity = max(severity, 0.8)
    
    # 5. Check impossible low RPM with high speed
    if speed > 100 and rpm < 2000:
        violations.append("IMPOSSIBLE_LOW_RPM")
        severity = max(severity, 0.9)
    
    is_valid = len(violations) == 0
    
    return is_valid, violations, severity, expected_rpm, rpm_deviation

def calibrate_confidence(risk, violations, severity):
    """
    Calibrate confidence based on physics violations.
    Reduces confidence for out-of-distribution inputs.
    """
    base_confidence = max(risk, 1 - risk)
    
    if len(violations) > 0:
        violation_penalty = min(len(violations) * 0.15, 0.4)
        severity_penalty = severity * 0.3
        calibrated = base_confidence * (1 - violation_penalty - severity_penalty)
        calibrated = max(calibrated, 0.5)
    else:
        calibrated = base_confidence
    
    return calibrated

def align_risk_stress(risk, stress, severity):
    """
    Ensure risk and stress are aligned for consistency.
    Physics violations should increase both.
    """
    if severity > 0.7:
        risk = max(risk, 0.7)
        stress = max(stress, 0.7)
    
    if stress > 0.8 and risk < 0.5:
        risk = max(risk, stress * 0.8)
    
    if risk > 0.8 and stress < 0.5:
        stress = max(stress, risk * 0.8)
    
    return risk, stress

# ============================================================================

def engineer_features(df):
    """Create features from raw data"""
    # Traction Health
    df['Traction_Health'] = df.apply(
        lambda row: calculate_traction_health(row['Speed'], row['RPM']), 
        axis=1
    )
    
    # Change features
    df['Speed_Change'] = df['Speed'].diff().fillna(0)
    df['Throttle_Change'] = df['Throttle'].diff().fillna(0)
    
    # Stress indicators
    df['Hard_Braking'] = ((df['Speed_Change'] < -20) & (df['Brake'] == 1)).astype(int)
    df['High_RPM'] = (df['RPM'] > 10000).astype(int)
    df['Full_Throttle'] = (df['Throttle'] >= 95).astype(int)
    
    # SAFETY FEATURES
    MAX_SAFE_RPM = 15000
    df['RPM_Danger'] = (df['RPM'] > MAX_SAFE_RPM).astype(int)
    df['Inconsistent_Combo'] = (
        ((df['RPM'] > 10000) & (df['Throttle'] < 30)) |
        ((df['Speed'] < 100) & (df['RPM'] > 12000))
    ).astype(int)
    
    # 🔥 PHYSICS-BASED FEATURES: Gear-Speed-RPM Mechanics
    gear_ratios = {1: 3.5, 2: 2.5, 3: 2.0, 4: 1.6, 5: 1.3, 6: 1.1, 7: 0.95, 8: 0.85}
    df['Gear_Ratio'] = df['nGear'].map(gear_ratios).fillna(1.0)
    
    SPEED_TO_RPM_FACTOR = 100
    df['Expected_RPM'] = df['Speed'] * df['Gear_Ratio'] * SPEED_TO_RPM_FACTOR
    df['RPM_Deviation'] = np.abs(df['RPM'] - df['Expected_RPM'])
    df['RPM_Deviation_Ratio'] = df['RPM_Deviation'] / (df['Expected_RPM'] + 1e-6)
    
    df['Gear_Speed_Mismatch'] = np.where(
        (df['RPM_Deviation_Ratio'] > 1.0) |
        ((df['Speed'] < 50) & (df['nGear'] > 3)) |
        ((df['Speed'] > 150) & (df['nGear'] < 3)),
        1, 0
    )
    
    df['RPM_per_Gear'] = df['RPM'] / (df['nGear'] + 1e-6)
    df['Speed_per_Gear'] = df['Speed'] / (df['nGear'] + 1e-6)
    df['RPM_Speed_Ratio'] = df['RPM'] / (df['Speed'] + 1e-6)
    df['Throttle_RPM_Product'] = df['Throttle'] * df['RPM'] / 1000000
    df['Throttle_Brake_Conflict'] = ((df['Throttle'] > 20) & (df['Brake'] == 1)).astype(int)
    
    # Cumulative wear
    df['RPM_Hours'] = (df['RPM'] / 60000).cumsum()
    df['Brake_Usage'] = df['Brake'].cumsum()
    df['High_Speed_Miles'] = ((df['Speed'] > 200) * df['Distance'].diff().fillna(0)).cumsum()
    
    # Stress score with physics-based penalties
    rpm_norm = df['RPM'] / df['RPM'].max()
    throttle_norm = df['Throttle'] / 100
    brake_norm = df['Brake']
    brake_usage_norm = df['Brake_Usage'] / (df['Brake_Usage'].max() + 1)
    
    base_stress = (
        0.30 * rpm_norm +
        0.25 * throttle_norm +
        0.25 * brake_norm +
        0.20 * brake_usage_norm
    )
    
    # Add penalties
    rpm_penalty = np.where(df['RPM'] > 15000, 0.3, 0)
    inconsistent_penalty = df['Inconsistent_Combo'] * 0.25
    mismatch_penalty = df['Gear_Speed_Mismatch'] * 0.35
    conflict_penalty = df['Throttle_Brake_Conflict'] * 0.20
    
    df['Stress_Score'] = (base_stress + rpm_penalty + inconsistent_penalty + mismatch_penalty + conflict_penalty).clip(0, 1)
    
    return df

tree_model, lr_model, scaler, features = load_models()

# Title
st.title("🚗 Vehicle Maintenance Predictor")

if tree_model is None or lr_model is None:
    st.error("⚠️ Models not found! Run: python run_all.py")
    st.stop()

# Mode selection
st.markdown("---")
mode = st.radio("Choose Prediction Mode:", ["🔢 Manual Input", "📁 CSV File Upload"], horizontal=True)

st.markdown("---")

# ==================== MANUAL INPUT MODE ====================
if mode == "🔢 Manual Input":
    st.subheader("Enter Vehicle Data:")
    st.info("🔑 **Safety Features:** RPM limits, inconsistent combination detection, realistic traction limits")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### � Engine")
        rpm = st.number_input("RPM", 0, 20000, 9000, 500, help="Engine revolutions per minute (Safe limit: 15,000)")
        throttle = st.slider("Throttle (%)", 0, 100, 50)
        
        # Safety warnings
        if rpm > 15000:
            st.error(f"⚠️ RPM DANGER: {rpm} > 15,000!")

    with col2:
        st.markdown("### 🏎️ Driving")
        speed = st.number_input("Speed (km/h)", 0, 400, 150, 10)
        gear = st.number_input("Gear", 1, 8, 4)
        brake = st.checkbox("🛑 Brake Applied")

    with col3:
        st.markdown("### 📊 Status")
        # Check for inconsistent combo
        inconsistent = (rpm > 10000 and throttle < 30) or (speed < 100 and rpm > 12000)
        
        # 🔥 Check gear-speed-RPM physics mismatch
        gear_ratios = {1: 3.5, 2: 2.5, 3: 2.0, 4: 1.6, 5: 1.3, 6: 1.1, 7: 0.95, 8: 0.85}
        gear_ratio = gear_ratios.get(gear, 1.0)
        expected_rpm = speed * gear_ratio * 100
        rpm_deviation_ratio = abs(rpm - expected_rpm) / (expected_rpm + 1e-6)
        gear_mismatch = (rpm_deviation_ratio > 1.0) or (speed < 50 and gear > 3) or (speed > 150 and gear < 3)
        
        if gear_mismatch:
            st.error("🔴 GEAR-SPEED-RPM MISMATCH!")
            st.caption(f"Expected RPM: ~{expected_rpm:.0f}")
            st.caption(f"Actual RPM: {rpm}")
            st.caption("Impossible drivetrain combo!")
        
        if inconsistent:
            st.warning("⚠️ INCONSISTENT COMBO!")
            if rpm > 10000 and throttle < 30:
                st.caption("High RPM + Low Throttle")
            if speed < 100 and rpm > 12000:
                st.caption("Low Speed + Very High RPM")
        
        # Throttle-brake conflict
        if throttle > 20 and brake:
            st.warning("⚠️ THROTTLE + BRAKE!")
            st.caption("Driver error or sensor issue")

    # Predict button
    if st.button("🔮 Predict Maintenance Need", type="primary", use_container_width=True):
        
        # ========== PHYSICS VALIDATION FIRST ==========
        is_valid, violations, severity, expected_rpm_calc, rpm_dev_ratio = validate_physics(
            rpm, speed, gear, throttle, int(brake)
        )
        
        physics_penalty = min(severity * 0.5, 0.5)  # Max 50% penalty
        # ===============================================
        
        # Calculate traction health
        traction_health = calculate_traction_health(speed, rpm)
        
        # Safety checks
        MAX_SAFE_RPM = 15000
        rpm_danger = 1 if rpm > MAX_SAFE_RPM else 0
        inconsistent_combo = 1 if inconsistent else 0
        
        # Calculate features
        brake_usage = 50  # Assume moderate for single prediction
        rpm_hours = 10
        high_speed_miles = 100 if speed > 200 else 0
        
        # 🔥 Physics-based features
        gear_ratios = {1: 3.5, 2: 2.5, 3: 2.0, 4: 1.6, 5: 1.3, 6: 1.1, 7: 0.95, 8: 0.85}
        gear_ratio = gear_ratios.get(gear, 1.0)
        expected_rpm = speed * gear_ratio * 100
        rpm_deviation = abs(rpm - expected_rpm)
        rpm_deviation_ratio = rpm_deviation / (expected_rpm + 1e-6)
        
        gear_speed_mismatch = 1 if (
            rpm_deviation_ratio > 1.0 or
            (speed < 50 and gear > 3) or
            (speed > 150 and gear < 3)
        ) else 0
        
        rpm_per_gear = rpm / (gear + 1e-6)
        speed_per_gear = speed / (gear + 1e-6)
        rpm_speed_ratio = rpm / (speed + 1e-6)
        throttle_rpm_product = throttle * rpm / 1000000
        throttle_brake_conflict = 1 if (throttle > 20 and brake) else 0
        
        # Calculate stress with ALL penalties
        rpm_norm = rpm / 15000
        throttle_norm = throttle / 100
        brake_norm = int(brake)
        
        base_stress = (
            0.30 * rpm_norm +
            0.25 * throttle_norm +
            0.25 * brake_norm +
            0.20 * 0.5  # Moderate brake usage
        )
        
        rpm_penalty = 0.3 if rpm > 15000 else 0
        inconsistent_penalty = inconsistent_combo * 0.25
        mismatch_penalty = gear_speed_mismatch * 0.35  # 🔥 NEW: Physics penalty
        conflict_penalty = throttle_brake_conflict * 0.20  # 🔥 NEW: Conflict penalty
        
        # ========== ADD PHYSICS PENALTY ==========
        stress = min(
            base_stress + 
            rpm_penalty + 
            inconsistent_penalty + 
            mismatch_penalty + 
            conflict_penalty +
            physics_penalty,  # From validation layer
            1.0
        )
        # =========================================
        
        # Create input
        input_data = {
            'RPM': rpm,
            'Speed': speed,
            'nGear': gear,
            'Throttle': throttle,
            'Brake': int(brake),
            'Traction_Health': traction_health,
            'Speed_Change': 0,
            'Throttle_Change': 0,
            'Hard_Braking': 0,
            'High_RPM': 1 if rpm > 10000 else 0,
            'Full_Throttle': 1 if throttle == 100 else 0,
            'RPM_Danger': rpm_danger,
            'Inconsistent_Combo': inconsistent_combo,
            'Gear_Ratio': gear_ratio,
            'Expected_RPM': expected_rpm,
            'RPM_Deviation': rpm_deviation,
            'RPM_Deviation_Ratio': rpm_deviation_ratio,
            'Gear_Speed_Mismatch': gear_speed_mismatch,
            'RPM_per_Gear': rpm_per_gear,
            'Speed_per_Gear': speed_per_gear,
            'RPM_Speed_Ratio': rpm_speed_ratio,
            'Throttle_RPM_Product': throttle_rpm_product,
            'Throttle_Brake_Conflict': throttle_brake_conflict,
            'RPM_Hours': rpm_hours,
            'Brake_Usage': brake_usage,
            'High_Speed_Miles': high_speed_miles,
            'Stress_Score': stress
        }
        
        # Make prediction
        input_df = pd.DataFrame([input_data])[features]
        input_scaled = scaler.transform(input_df)
        
        # Use Decision Tree for binary prediction
        prediction = tree_model.predict(input_scaled)[0]
        # Use Logistic Regression for nuanced risk probability
        risk = lr_model.predict_proba(input_scaled)[0][1]
        
        # ========== PHYSICS OVERRIDE & CALIBRATION ==========
        # Override for severe physics violations
        if severity > 0.7:
            risk = max(risk, 0.7)  # Force high risk
            prediction = 1  # Force maintenance
        
        # Align risk and stress
        risk, stress = align_risk_stress(risk, stress, severity)
        
        # Calibrate confidence
        confidence = calibrate_confidence(risk, violations, severity)
        # ====================================================
        
        risk_display = risk
        
        # Show results
        st.markdown("---")
        st.subheader("🎯 Results:")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if risk_display >= 0.7:
                st.error(f"### 🔴 HIGH RISK: {risk_display*100:.0f}%")
                st.error("⚠️ **Maintenance Required Immediately!**")
            elif risk_display >= 0.4:
                st.warning(f"### 🟡 MEDIUM RISK: {risk_display*100:.0f}%")
                st.warning("⚠️ **Monitor Closely**")
            else:
                st.success(f"### 🟢 LOW RISK: {risk_display*100:.1f}%")
                st.success("✅ **Acceptable Condition**")
        
        # Additional info
        st.markdown("---")
        
        # ========== PHYSICS VIOLATION WARNINGS ==========
        if len(violations) > 0:
            st.error(f"⚠️ **Physics Validation:** {len(violations)} violation(s) detected (Severity: {severity:.0%})")
        # ================================================
        
        st.markdown("*ℹ️ Risk probability from Logistic Regression (nuanced), Prediction from Decision Tree (accurate)*")
        st.markdown("---")
        st.subheader("📊 Details:")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🏥 Traction Health", f"{traction_health:.2f}")
        with col2:
            st.metric("⚙️ Stress Score", f"{stress:.2f}")
        with col3:
            st.metric("🎯 Prediction", "Maintenance" if prediction == 1 else "OK")
        with col4:
            st.metric("✓ Confidence", f"{confidence*100:.0f}%")
        
        # Contributing Factors
        st.markdown("---")
        st.subheader("🔍 Contributing Factors:")
        
        # ========== DETAILED PHYSICS VIOLATIONS ==========
        if len(violations) > 0:
            st.markdown("#### ⚠️ Physics Violations:")
            for violation in violations:
                if violation == "EXTREME_RPM_MISMATCH":
                    st.error(f"🔴 **Extreme RPM Mismatch** - Expected: ~{expected_rpm_calc:.0f}, Actual: {rpm} (Deviation: {rpm_dev_ratio*100:.0f}%)")
                    st.caption("   → RPM deviates >200% from expected - Possible clutch slip or sensor error")
                elif violation == "RPM_MISMATCH":
                    st.warning(f"🟡 **RPM Mismatch** - Expected: ~{expected_rpm_calc:.0f}, Actual: {rpm} (Deviation: {rpm_dev_ratio*100:.0f}%)")
                    st.caption("   → RPM deviates >100% from expected for speed/gear combination")
                elif violation == "HIGH_GEAR_LOW_SPEED":
                    st.error("🔴 **High Gear at Low Speed** - Mechanically strained, possible stall")
                elif violation == "LOW_GEAR_HIGH_SPEED":
                    st.error("🔴 **Low Gear at High Speed** - Engine over-revving danger")
                elif violation == "THROTTLE_BRAKE_CONFLICT":
                    st.warning("🟡 **Throttle + Brake Conflict** - Driver error or sensor malfunction")
                elif violation == "EXTREME_RPM":
                    st.error(f"� **Extreme RPM** - {rpm} > 15,000 RPM exceeds safe limits")
                elif violation == "IMPOSSIBLE_LOW_RPM":
                    st.error("🔴 **Impossible Low RPM** - Speed too high for RPM, drivetrain issue")
            st.markdown("---")
        # =================================================
        
        factors = []
        
        # 🔥 Physics mismatch - HIGHEST PRIORITY
        if gear_speed_mismatch:
            factors.append(("🔴 GEAR-SPEED-RPM MISMATCH", f"Expected RPM: ~{expected_rpm:.0f}, Actual: {rpm} (Deviation: {rpm_deviation_ratio*100:.0f}%) - MECHANICALLY IMPOSSIBLE!"))
        
        # Safety warnings
        if rpm_danger:
            factors.append(("🔴 RPM DANGER", f"{rpm} RPM > 15,000 (UNSAFE!)"))
        
        if inconsistent_combo:
            factors.append(("🔴 INCONSISTENT COMBO", f"High RPM ({rpm}) + Low Throttle ({throttle}%) OR Low Speed + High RPM"))
        
        if throttle_brake_conflict:
            factors.append(("🔴 THROTTLE + BRAKE CONFLICT", f"Throttle {throttle}% while braking - Driver error or sensor issue"))
        
        # Traction health
        if traction_health < 0.7:
            factors.append(("🔴 Poor Traction", f"{traction_health:.2f} (tire slip detected)"))
        elif traction_health < 0.85:
            factors.append(("🟡 Moderate Traction", f"{traction_health:.2f}"))
        else:
            factors.append(("🟢 Good Traction", f"{traction_health:.2f}"))
        
        # RPM analysis
        if rpm > 12000:
            factors.append(("🔴 Very High RPM", f"{rpm} RPM (extreme engine stress)"))
        elif rpm > 10000:
            factors.append(("� High RPM", f"{rpm} RPM (engine stress)"))
        elif rpm > 7500:
            factors.append(("🟡 Elevated RPM", f"{rpm} RPM"))
        
        # Speed analysis
        if speed > 250:
            factors.append(("🔴 Extreme Speed", f"{speed} km/h"))
        elif speed > 200:
            factors.append(("� Very High Speed", f"{speed} km/h"))
        elif speed > 150:
            factors.append(("🟡 High Speed", f"{speed} km/h"))
        
        # Throttle analysis
        if throttle > 90:
            factors.append(("🟡 Full Throttle", f"{throttle}%"))
        elif throttle > 80:
            factors.append(("🟡 High Throttle Usage", f"{throttle}%"))
        
        # Braking
        if brake:
            factors.append(("🟡 Active Braking", "Brake applied"))
        
        factors.append(("📊 Stress Score", f"{stress:.2f} (composite metric)"))
        
        for factor_name, factor_value in factors:
            st.write(f"• **{factor_name}:** {factor_value}")

# ==================== CSV UPLOAD MODE ====================
else:
    st.subheader("📁 Upload CSV File for Batch Predictions")
    
    st.info("""
    **Required columns in your CSV:**
    - `RPM` - Engine revolutions per minute
    - `Speed` - Vehicle speed (km/h)
    - `Throttle` - Throttle position (%)
    - `Brake` - Brake status (0 or 1)
    - `Distance` - Cumulative distance (km)
    """)
    
    uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])
    
    if uploaded_file is not None:
        try:
            # Load CSV
            df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ File loaded: {len(df)} rows, {len(df.columns)} columns")
            
            # Show preview
            with st.expander("📋 Preview Data (First 5 rows)"):
                st.dataframe(df.head())
            
            # Check required columns
            required_cols = ['RPM', 'Speed', 'Throttle', 'Brake', 'Distance']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                st.info(f"Your columns: {', '.join(df.columns)}")
            else:
                # Process button
                if st.button("🔮 Predict for All Rows", type="primary", use_container_width=True):
                    with st.spinner("Processing... Creating features and making predictions..."):
                        
                        # ========== VALIDATE PHYSICS FOR ALL ROWS ==========
                        # Ensure nGear exists (use default if not)
                        if 'nGear' not in df.columns:
                            df['nGear'] = 4  # Default gear
                        
                        validations = []
                        for idx, row in df.iterrows():
                            is_valid, violations, severity, _, _ = validate_physics(
                                row['RPM'], row['Speed'], row['nGear'], 
                                row['Throttle'], row['Brake']
                            )
                            validations.append({
                                'is_valid': is_valid,
                                'violations': '|'.join(violations) if violations else '',
                                'severity': severity
                            })
                        
                        validation_df = pd.DataFrame(validations)
                        # ==================================================
                        
                        # Engineer features
                        df = engineer_features(df)
                        
                        # Prepare features for prediction
                        X = df[features]
                        X_scaled = scaler.transform(X)
                        
                        # Use Decision Tree for binary predictions
                        predictions = tree_model.predict(X_scaled)
                        # Use Logistic Regression for nuanced risk scores
                        risk_scores = lr_model.predict_proba(X_scaled)[:, 1]
                        
                        # ========== APPLY PHYSICS OVERRIDES ==========
                        severe_violations = validation_df['severity'] > 0.7
                        risk_scores[severe_violations] = np.maximum(
                            risk_scores[severe_violations], 0.7
                        )
                        predictions[severe_violations] = 1
                        
                        # Calibrate confidence for each row
                        confidences = []
                        for i, (risk, val_row) in enumerate(zip(risk_scores, validation_df.itertuples())):
                            viols = val_row.violations.split('|') if val_row.violations else []
                            conf = calibrate_confidence(risk, viols, val_row.severity)
                            confidences.append(conf)
                        # =============================================
                        
                        # Add predictions to dataframe
                        df['Prediction'] = predictions
                        df['Risk_Score'] = (risk_scores * 100).round(1)
                        df['Confidence'] = (np.array(confidences) * 100).round(1)
                        df['Physics_Valid'] = validation_df['is_valid']
                        df['Violations'] = validation_df['violations']
                        df['Severity'] = (validation_df['severity'] * 100).round(1)
                        df['Risk_Level'] = pd.cut(
                            risk_scores,
                            bins=[0, 0.4, 0.7, 1.0],
                            labels=['🟢 LOW', '🟡 MEDIUM', '🔴 HIGH']
                        )
                        df['Needs_Maintenance'] = df['Prediction'].map({0: 'No', 1: 'Yes'})
                        
                        # Summary statistics
                        st.markdown("---")
                        st.subheader("📊 Prediction Summary")
                        
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric("Total Rows", len(df))
                        with col2:
                            st.metric("Needs Maintenance", f"{predictions.sum()} ({predictions.sum()/len(df)*100:.1f}%)")
                        with col3:
                            st.metric("OK", f"{len(df) - predictions.sum()} ({(len(df) - predictions.sum())/len(df)*100:.1f}%)")
                        with col4:
                            st.metric("Avg Risk", f"{risk_scores.mean()*100:.1f}%")
                        with col5:
                            invalid_count = (~validation_df['is_valid']).sum()
                            st.metric("Physics Issues", f"{invalid_count} ({invalid_count/len(df)*100:.1f}%)")
                        
                        # ========== PHYSICS VALIDATION SUMMARY ==========
                        if invalid_count > 0:
                            st.warning(f"⚠️ **Physics Validation:** {invalid_count} rows have physics violations")
                        # ================================================
                        
                        # Risk distribution
                        st.markdown("---")
                        st.subheader("📈 Risk Distribution")
                        
                        risk_dist = df['Risk_Level'].value_counts()
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.dataframe(risk_dist, use_container_width=True)
                        
                        with col2:
                            st.bar_chart(risk_dist)
                        
                        # High risk cases
                        high_risk = df[df['Risk_Score'] >= 70]
                        if len(high_risk) > 0:
                            st.markdown("---")
                            st.subheader(f"⚠️ High Risk Cases ({len(high_risk)} found)")
                            
                            display_cols = ['RPM', 'Speed', 'Throttle', 'Traction_Health', 
                                          'RPM_Danger', 'Inconsistent_Combo', 
                                          'Risk_Score', 'Risk_Level', 'Needs_Maintenance']
                            available_cols = [col for col in display_cols if col in df.columns]
                            
                            st.dataframe(high_risk[available_cols].head(20), use_container_width=True)
                        
                        # Full results preview
                        st.markdown("---")
                        st.subheader("📋 All Predictions (First 50 rows)")
                        
                        output_cols = ['RPM', 'Speed', 'Throttle', 'Brake', 'Traction_Health',
                                       'RPM_Danger', 'Inconsistent_Combo',
                                       'Stress_Score', 'Risk_Score', 'Risk_Level', 'Needs_Maintenance']
                        available_output_cols = [col for col in output_cols if col in df.columns]
                        
                        st.dataframe(df[available_output_cols].head(50), use_container_width=True)
                        
                        # Download button
                        st.markdown("---")
                        st.subheader("💾 Download Results")
                        
                        # Prepare CSV for download
                        csv_buffer = io.StringIO()
                        df.to_csv(csv_buffer, index=False)
                        csv_data = csv_buffer.getvalue()
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"predictions_{timestamp}.csv"
                        
                        st.download_button(
                            label="📥 Download Predictions CSV",
                            data=csv_data,
                            file_name=filename,
                            mime="text/csv",
                            use_container_width=True,
                            type="primary"
                        )
                        
                        st.success(f"✅ Predictions complete! Click above to download results.")
        
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.info("Please make sure your CSV has the required columns: RPM, Speed, Throttle, Brake, Distance")

# Footer
st.markdown("---")
st.caption("Built with Scikit-learn • Decision Tree (Binary Prediction) + Logistic Regression (Risk Probability) • Safety Thresholds • Traction Health • Physics-Based Features")
