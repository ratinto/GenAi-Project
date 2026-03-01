"""
STREAMLIT APP - Vehicle Maintenance Predictor
==============================================
Web interface with Manual Input & CSV Upload modes
"""

import streamlit as st
import pandas as pd
import pickle
import io
from datetime import datetime

# Page config
st.set_page_config(page_title="Maintenance Predictor", page_icon="🚗", layout="wide")

# Load models
@st.cache_resource
def load_models():
    try:
        with open('tree_model.pkl', 'rb') as f:
            model = pickle.load(f)
        with open('scaler.pkl', 'rb') as f:
            scaler = pickle.load(f)
        with open('features.pkl', 'rb') as f:
            features_list = pickle.load(f)
        return model, scaler, features_list
    except:
        return None, None, None

def engineer_features(df):
    """Create features from raw data"""
    # Mileage features
    df['Mileage'] = df['Distance']
    df['Mileage_Normalized'] = (df['Mileage'] - df['Mileage'].min()) / (df['Mileage'].max() - df['Mileage'].min() + 1e-6)
    
    # Change features
    df['Speed_Change'] = df['Speed'].diff().fillna(0)
    df['Throttle_Change'] = df['Throttle'].diff().fillna(0)
    
    # Stress indicators
    df['Hard_Braking'] = ((df['Speed_Change'] < -20) & (df['Brake'] == 1)).astype(int)
    df['High_RPM'] = (df['RPM'] > 10000).astype(int)
    df['Full_Throttle'] = (df['Throttle'] >= 95).astype(int)
    
    # Cumulative wear
    df['RPM_Hours'] = (df['RPM'] / 60000).cumsum()
    df['Brake_Usage'] = df['Brake'].cumsum()
    df['High_Speed_Miles'] = ((df['Speed'] > 200) * df['Distance'].diff().fillna(0)).cumsum()
    
    # Stress score with mileage
    rpm_norm = (df['RPM'] - df['RPM'].min()) / (df['RPM'].max() - df['RPM'].min() + 1e-6)
    throttle_norm = df['Throttle'] / 100
    brake_norm = df['Brake']
    mileage_norm = df['Mileage_Normalized']
    brake_wear = (df['Brake_Usage'] - df['Brake_Usage'].min()) / (df['Brake_Usage'].max() - df['Brake_Usage'].min() + 1e-6)
    
    df['Stress_Score'] = (
        0.25 * rpm_norm + 
        0.20 * throttle_norm + 
        0.20 * brake_norm + 
        0.20 * mileage_norm + 
        0.15 * brake_wear
    )
    
    return df

model, scaler, features = load_models()

# Title
st.title("🚗 Vehicle Maintenance Predictor")

if model is None:
    st.error("⚠️ Models not found! Run: python run_all.py")
    st.stop()

# Mode selection
st.markdown("---")
mode = st.radio("Choose Prediction Mode:", ["🔢 Manual Input", "📁 CSV File Upload"], horizontal=True)

st.markdown("---")

# ==================== MANUAL INPUT MODE ====================
if mode == "🔢 Manual Input":
    st.subheader("Enter Vehicle Data:")
    st.info("🔑 **Key Feature:** Mileage is used to predict component wear over time")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 📏 Mileage")
        mileage = st.number_input("Mileage (km)", 0, 10000, 3000, 100, 
                                  help="⭐ Total distance traveled - KEY FACTOR for maintenance!")
        st.caption(f"{'🟢 Low' if mileage < 2000 else '🟡 Medium' if mileage < 4000 else '🔴 High'} wear")

    with col2:
        st.markdown("### 🔧 Engine")
        rpm = st.number_input("RPM", 0, 15000, 9000, 500, help="Engine revolutions per minute")
        throttle = st.slider("Throttle (%)", 0, 100, 50)

    with col3:
        st.markdown("### 🏎️ Driving")
        speed = st.number_input("Speed (km/h)", 0, 400, 150, 10)
        gear = st.number_input("Gear", 1, 8, 4)
        brake = st.checkbox("🛑 Brake Applied")

    # Predict button
    if st.button("🔮 Predict Maintenance Need", type="primary", use_container_width=True):
        
        # Calculate features (including mileage!)
        mileage_norm = min(mileage / 5000, 1)
        brake_usage = mileage / 50
        rpm_hours = mileage / 100
        high_speed_miles = mileage * 0.3 if speed > 200 else 0
        
        stress = (0.25 * (rpm/15000) + 0.2 * (throttle/100) + 
                  0.2 * int(brake) + 0.2 * mileage_norm + 
                  0.15 * (brake_usage / max(brake_usage, 1)))
        
        # Create input
        input_data = {
            'RPM': rpm,
            'Speed': speed,
            'nGear': gear,
            'Throttle': throttle,
            'Brake': int(brake),
            'Mileage': mileage,
            'Mileage_Normalized': mileage_norm,
            'Speed_Change': 0,
            'Throttle_Change': 0,
            'Hard_Braking': 0,
            'High_RPM': 1 if rpm > 10000 else 0,
            'Full_Throttle': 1 if throttle == 100 else 0,
            'RPM_Hours': rpm_hours,
            'Brake_Usage': brake_usage,
            'High_Speed_Miles': high_speed_miles,
            'Stress_Score': stress
        }
        
        # Make prediction
        input_df = pd.DataFrame([input_data])[features]
        input_scaled = scaler.transform(input_df)
        
        prediction = model.predict(input_scaled)[0]
        risk = model.predict_proba(input_scaled)[0][1]
        
        # Show results
        st.markdown("---")
        st.subheader("🎯 Results:")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if risk >= 0.7:
                st.error(f"### 🔴 HIGH RISK: {risk*100:.0f}%")
                st.error("⚠️ **Maintenance Recommended!**")
            elif risk >= 0.4:
                st.warning(f"### 🟡 MEDIUM RISK: {risk*100:.0f}%")
                st.warning("⚠️ **Monitor Closely**")
            else:
                st.success(f"### 🟢 LOW RISK: {risk*100:.0f}%")
                st.success("✅ **Normal Operation**")
        
        # Additional info
        st.markdown("---")
        st.subheader("📊 Details:")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📏 Mileage", f"{mileage} km")
        with col2:
            st.metric("⚙️ Stress Score", f"{stress:.2f}")
        with col3:
            st.metric("🎯 Prediction", "Maintenance" if prediction == 1 else "OK")
        with col4:
            st.metric("✓ Confidence", f"{max(risk, 1-risk)*100:.0f}%")
        
        # Contributing Factors
        st.markdown("---")
        st.subheader("🔍 Contributing Factors:")
        
        factors = []
        if mileage > 4000:
            factors.append(("🔴 High Mileage", f"{mileage} km (>4000 km threshold)"))
        elif mileage > 2000:
            factors.append(("🟡 Moderate Mileage", f"{mileage} km"))
        else:
            factors.append(("🟢 Low Mileage", f"{mileage} km"))
        
        if rpm > 10000:
            factors.append(("🔴 High RPM", f"{rpm} RPM (engine stress)"))
        elif rpm > 7500:
            factors.append(("🟡 Elevated RPM", f"{rpm} RPM"))
        
        if speed > 200:
            factors.append(("🔴 Very High Speed", f"{speed} km/h"))
        elif speed > 150:
            factors.append(("🟡 High Speed", f"{speed} km/h"))
        
        if throttle > 80:
            factors.append(("🟡 High Throttle Usage", f"{throttle}%"))
        
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
                        
                        # Engineer features
                        df = engineer_features(df)
                        
                        # Prepare features for prediction
                        X = df[features]
                        X_scaled = scaler.transform(X)
                        
                        # Make predictions
                        predictions = model.predict(X_scaled)
                        risk_scores = model.predict_proba(X_scaled)[:, 1]
                        
                        # Add predictions to dataframe
                        df['Prediction'] = predictions
                        df['Risk_Score'] = (risk_scores * 100).round(1)
                        df['Risk_Level'] = pd.cut(
                            risk_scores,
                            bins=[0, 0.4, 0.7, 1.0],
                            labels=['🟢 LOW', '🟡 MEDIUM', '🔴 HIGH']
                        )
                        df['Needs_Maintenance'] = df['Prediction'].map({0: 'No', 1: 'Yes'})
                        
                        # Summary statistics
                        st.markdown("---")
                        st.subheader("📊 Prediction Summary")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Rows", len(df))
                        with col2:
                            st.metric("Needs Maintenance", f"{predictions.sum()} ({predictions.sum()/len(df)*100:.1f}%)")
                        with col3:
                            st.metric("OK", f"{len(df) - predictions.sum()} ({(len(df) - predictions.sum())/len(df)*100:.1f}%)")
                        with col4:
                            st.metric("Avg Risk", f"{risk_scores.mean()*100:.1f}%")
                        
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
                            
                            display_cols = ['Mileage', 'RPM', 'Speed', 'Throttle', 'Risk_Score', 'Risk_Level', 'Needs_Maintenance']
                            available_cols = [col for col in display_cols if col in df.columns]
                            
                            st.dataframe(high_risk[available_cols].head(20), use_container_width=True)
                        
                        # Full results preview
                        st.markdown("---")
                        st.subheader("📋 All Predictions (First 50 rows)")
                        
                        output_cols = ['RPM', 'Speed', 'Throttle', 'Brake', 'Mileage', 
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
st.caption("Built with Scikit-learn • Logistic Regression & Decision Tree • Mileage-based Predictions")
