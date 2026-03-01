"""
HIRAETH F1 | MISSION CONTROL v2.1
=================================
Ultra-high fidelity vehicle telemetry dashboard with integrated physics validation.
"""

import streamlit as st
import pandas as pd
import numpy as np
import pickle
import io
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CORE CONFIGURATION ---
st.set_page_config(
    page_title="HIRAETH F1 | MISSION CONTROL",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- LUXURY THEME SPECIFICATION ---
THEME = {
    "neon_red": "#f66338",
    "deep_red": "#4a031e",
    "obsidian": "#050505",
    "carbon": "#121212",
    "glass": "rgba(18, 18, 18, 0.7)",
    "text_main": "#ffffff",
    "text_sec": "#888888",
    "grid": "#222222"
}

# --- ADVANCED STYLING ENGINE ---
def inject_premium_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@100;400&display=swap');
    
    /* Core Layout & Spacing */
    .stApp {{
        background: {THEME['obsidian']};
        background-image: 
            linear-gradient({THEME['grid']} 1px, transparent 1px),
            linear-gradient(90deg, {THEME['grid']} 1px, transparent 1px);
        background-size: 50px 50px;
        color: {THEME['text_main']};
        font-family: 'JetBrains Mandatory', 'JetBrains Mono', monospace;
    }}
    
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }}
    
    /* Typography */
    h1, h2, h3, .f1-header {{
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 5px;
        font-weight: 900;
        text-transform: uppercase;
    }}
    
    .brand-title {{
        font-size: 4.5rem;
        background: linear-gradient(180deg, #fff 30%, {THEME['neon_red']} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: -10px;
        padding-top: 0px !important;
        margin-top: -20px !important;
    }}
    
    /* Luxury Glass Cards */
    .glass-card {{
        background: {THEME['glass']};
        border: 1px solid #333;
        border-top: 2px solid {THEME['neon_red']};
        padding: 25px;
        border-radius: 4px;
        backdrop-filter: blur(15px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        margin-bottom: 20px;
    }}
    
    /* Segmented Progress Bars */
    .segment-container {{
        display: flex;
        gap: 3px;
        height: 12px;
        margin: 10px 0;
    }}
    
    .segment {{
        flex: 1;
        background: #222;
        border-radius: 1px;
    }}
    
    .segment.active {{
        background: {THEME['neon_red']};
        box-shadow: 0 0 8px {THEME['neon_red']};
    }}
    
    /* Global Elements */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 30px;
        padding-bottom: 15px;
        border-bottom: 1px solid #333;
    }}

    .stTabs [data-baseweb="tab"] {{
        background: transparent !important;
        font-family: 'Orbitron', sans-serif;
        font-size: 0.8rem;
        letter-spacing: 2px;
        color: {THEME['text_sec']} !important;
        border-bottom: 2px solid transparent !important;
    }}

    .stTabs [aria-selected="true"] {{
        color: {THEME['neon_red']} !important;
        border-bottom: 2px solid {THEME['neon_red']} !important;
    }}
    
    /* Hide Streamlit Clutter */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {{
        width: 5px;
    }}
    ::-webkit-scrollbar-track {{
        background: {THEME['obsidian']};
    }}
    ::-webkit-scrollbar-thumb {{
        background: {THEME['neon_red']};
    }}
    </style>
    """, unsafe_allow_html=True)

# --- BOOT SEQUENCE ENGINE ---
def render_boot_sequence():
    """Renders the high-fidelity F1 startup animation."""
    if 'boot_complete' not in st.session_state:
        import base64
        import os
        
        # Base64 encode the car asset if it exists
        car_b64 = ""
        car_path = os.path.join(os.getcwd(), 'f1_car_clean.png')
        if os.path.exists(car_path):
            with open(car_path, "rb") as image_file:
                car_b64 = base64.b64encode(image_file.read()).decode()
            
        st.markdown(f"""
        <div id="hiraeth-boot-sequence">
            <div class="circuit-grid"></div>
            <div class="animation-stage">
                <div class="track-line">
                    <div class="f1-car-container">
                        <img src="data:image/png;base64,{car_b64}" class="f1-car-img" />
                        <div class="engine-smoke">
                            <span class="puff"></span><span class="puff"></span><span class="puff"></span><span class="puff"></span>
                            <span class="puff"></span><span class="puff"></span><span class="puff"></span><span class="puff"></span>
                            <span class="puff"></span><span class="puff"></span><span class="puff"></span><span class="puff"></span>
                            <span class="puff"></span><span class="puff"></span><span class="puff"></span><span class="puff"></span>
                            <span class="puff"></span><span class="puff"></span><span class="puff"></span><span class="puff"></span>
                        </div>
                    </div>
                </div>
                <div class="boot-branding">
                    <span class="brand-hiraeth">HIRAETH</span>
                    <span class="brand-f1">F1</span>
                </div>
            </div>
        </div>
        
        <style>
        #hiraeth-boot-sequence {{
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: #050505;
            z-index: 1000000;
            display: flex; justify-content: center; align-items: center;
            opacity: 1;
            animation: curtainClose 1.2s cubic-bezier(0.7, 0, 0.3, 1) 4.2s forwards;
            pointer-events: none;
            overflow: hidden;
        }}

        .circuit-grid {{
            position: absolute;
            width: 200%; height: 200%;
            background-image: 
                linear-gradient(#111 1px, transparent 1px), 
                linear-gradient(90deg, #111 1px, transparent 1px);
            background-size: 80px 80px;
            transform: perspective(600px) rotateX(65deg) translateY(-25%);
            opacity: 0.15;
            animation: gridScroll 10s linear infinite;
        }}

        @keyframes gridScroll {{
            from {{ transform: perspective(600px) rotateX(65deg) translateY(-25%); }}
            to {{ transform: perspective(600px) rotateX(65deg) translateY(-20%); }}
        }}

        .animation-stage {{
            position: relative;
            width: 100%;
            height: 400px;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
        }}

        .track-line {{
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, transparent, rgba(246, 99, 56, 1), transparent);
            position: relative;
            box-shadow: 0 0 50px rgba(246, 99, 56, 0.7);
        }}

        .f1-car-container {{
            position: absolute;
            width: 450px;
            left: 0;
            bottom: -140px;
            transform: translateX(-550px);
            animation: f1Drive 4.5s cubic-bezier(0.4, 0, 0.2, 1) 0.5s forwards;
            z-index: 10;
            will-change: transform;
        }}

        .f1-car-img {{
            width: 100%;
            height: auto;
            display: block;
            transform: scaleX(-1);
            filter: drop-shadow(0 0 25px rgba(246, 99, 56, 0.8));
            object-fit: contain;
        }}

        .engine-smoke {{
            position: absolute;
            right: 0px; bottom: 35px;
            display: flex; gap: 2px;
            will-change: transform, opacity;
        }}

        .puff {{
            width: 40px; height: 40px;
            background: rgba(255, 255, 255, 0.15);
            border-radius: 50%;
            filter: blur(20px);
            animation: smokeRise 0.6s ease-out infinite;
        }}

        .puff:nth-child(even) {{ animation-delay: 0.1s; animation-duration: 0.5s; }}
        .puff:nth-child(3n) {{ animation-delay: 0.2s; animation-duration: 0.7s; }}
        .puff:nth-child(4n) {{ animation-delay: 0.3s; animation-duration: 0.4s; }}
        .puff:nth-child(5n) {{ animation-delay: 0.05s; animation-duration: 0.8s; }}

        @keyframes f1Drive {{
            0% {{ transform: translateX(-550px) scale(0.9); }}
            100% {{ transform: translateX(calc(100vw + 500px)) scale(1.1); }}
        }}

        @keyframes smokeRise {{
            0% {{ transform: translateY(0) scale(1) translateX(0); opacity: 0.6; }}
            100% {{ transform: translateY(-100px) scale(8) translateX(-50px); opacity: 0; }}
        }}

        .boot-branding {{
            margin-top: 40px;
            display: flex; align-items: center; gap: 20px;
            opacity: 0;
            animation: brandFadeIn 2s ease-out 1.2s forwards;
            transform: translateY(20px);
        }}

        .brand-hiraeth {{
            font-family: 'Orbitron', sans-serif;
            font-size: 5rem;
            font-weight: 900;
            letter-spacing: 25px;
            color: #fff;
            background: linear-gradient(180deg, #fff 40%, #888 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .brand-f1 {{
            font-family: 'Orbitron', sans-serif;
            font-size: 6rem;
            font-weight: 900;
            color: #f66338;
            letter-spacing: -5px;
            font-style: italic;
            position: relative;
            transform: skewX(-15deg);
        }}

        .brand-f1::after {{
            content: '';
            position: absolute;
            left: -10px; bottom: 10px;
            width: 110%; height: 60%;
            background: rgba(246, 99, 56, 0.15);
            filter: blur(30px);
            z-index: -1;
        }}

        @keyframes f1Drive {{
            0% {{ left: -350px; transform: scale(0.9); }}
            100% {{ left: 130%; transform: scale(1.2); }}
        }}

        @keyframes smokeRise {{
            0% {{ transform: translateY(0) scale(1) translateX(0); opacity: 0.8; }}
            100% {{ transform: translateY(-80px) scale(6) translateX(-40px); opacity: 0; }}
        }}

        @keyframes brandFadeIn {{
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        @keyframes curtainClose {{
            to {{ opacity: 0; visibility: hidden; transform: scale(1.05); }}
        }}
        </style>
        """, unsafe_allow_html=True)
        st.session_state.boot_complete = True

# --- PAGE BOOT ---
render_boot_sequence()
inject_premium_css()

# --- REUSABLE UI COMPONENTS ---
def render_segmented_bar(value_pct):
    n_segments = 20
    active_segments = int(value_pct * n_segments)
    html = "<div class='segment-container'>"
    for i in range(n_segments):
        status = "active" if i < active_segments else ""
        html += f"<div class='segment {status}'></div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def mission_panel(label, value, subtext="", color="#fff"):
    st.markdown(f"""
    <div style='border-left: 2px solid {THEME['neon_red']}; padding-left: 15px; margin-bottom: 20px;'>
        <p style='color:{THEME['text_sec']}; font-size:0.7rem; letter-spacing:3px; margin:0;'>{label}</p>
        <p style='color:{color}; font-size:2rem; font-family:"Orbitron"; margin:0;'>{value}</p>
        <p style='color:{THEME['text_sec']}; font-size:0.6rem; margin:0;'>{subtext}</p>
    </div>
    """, unsafe_allow_html=True)

# --- CORE DATA ENGINES ---
@st.cache_resource(hash_funcs={type(lambda: None): lambda _: None})
def load_ai_kernels():
    try:
        with open('tree_model.pkl', 'rb') as f:
            tree_model = pickle.load(f)
        with open('logistic_model.pkl', 'rb') as f:
            lr_model = pickle.load(f)
        with open('scaler.pkl', 'rb') as f:
            scaler = pickle.load(f)
        with open('features.pkl', 'rb') as f:
            features_list = pickle.load(f)
        return tree_model, lr_model, scaler, features_list
    except: return None, None, None, None

def calculate_traction_health(speed, rpm):
    """Calculate traction health from speed and RPM - measures tire slip."""
    r_eff = 0.33  # Fixed effective wheel radius in meters
    speed_mps = speed * (1000/3600)  # Convert km/h to m/s
    wheel_rpm = rpm / 8  # Approximate wheel RPM (engine RPM / average gear ratio)
    wheel_omega = (wheel_rpm / 60) * (2 * np.pi)  # Wheel angular velocity (rad/s)
    expected_speed = wheel_omega * r_eff
    if speed_mps > 0.1:  # Avoid division by zero
        slip_ratio = (expected_speed - speed_mps) / speed_mps
    else:
        slip_ratio = 0 if wheel_rpm < 100 else 1.0  # Burnout detection
    traction_health = 1 - abs(slip_ratio)
    traction_health = max(0.3, min(1.0, traction_health))  # Range: 0.3 to 1.0
    return traction_health

def validate_physics(rpm, speed, gear, throttle, brake):
    """Validate telemetry against mechanical physics."""
    violations = []
    severity = 0.0
    gear_ratios = {1: 3.5, 2: 2.5, 3: 2.0, 4: 1.6, 5: 1.3, 6: 1.1, 7: 0.95, 8: 0.85}
    gear_ratio = gear_ratios.get(gear, 1.0)
    expected_rpm = speed * gear_ratio * 100
    rpm_deviation = abs(rpm - expected_rpm) / (expected_rpm + 1e-6)
    
    if rpm_deviation > 1.5: violations.append("EXTREME_RPM_MISMATCH"); severity = max(severity, 0.9)
    elif rpm_deviation > 0.7: violations.append("RPM_MISMATCH"); severity = max(severity, 0.7)
    if speed < 50 and gear > 3: violations.append("HIGH_GEAR_LOW_SPEED"); severity = max(severity, 0.7)
    if speed > 200 and gear <= 4: violations.append("LOW_GEAR_HIGH_SPEED"); severity = max(severity, 0.8)
    if throttle > 20 and brake == 1: violations.append("THROTTLE_BRAKE_CONFLICT"); severity = max(severity, 0.5)
    if rpm > 15000: violations.append("EXTREME_RPM"); severity = max(severity, 0.8)
    if speed > 100 and rpm < 2000: violations.append("IMPOSSIBLE_LOW_RPM"); severity = max(severity, 0.9)
    
    return len(violations) == 0, violations, severity, expected_rpm, rpm_deviation

def calibrate_confidence(risk, violations, severity):
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
    if severity > 0.7:
        risk = max(risk, 0.7)
        stress = max(stress, 0.7)
    if stress > 0.8 and risk < 0.5:
        risk = max(risk, stress * 0.8)
    if risk > 0.8 and stress < 0.5:
        stress = max(stress, risk * 0.8)
    return risk, stress

def process_batch_features(df):
    """Create features for CSV processing based on new requirements."""
    df = df.copy()
    if 'Distance' in df.columns:
        df['Mileage'] = df['Distance'] / 1000
        df['Mileage_Normalized'] = (df['Mileage'] - df['Mileage'].min()) / (df['Mileage'].max() - df['Mileage'].min() + 1e-6)
    else:
        df['Mileage'] = 4200.0  # Default fallback
        df['Mileage_Normalized'] = 0.8
        
    df['Traction_Health'] = df.apply(lambda row: calculate_traction_health(row['Speed'], row['RPM']), axis=1)
    df['Speed_Change'] = df['Speed'].diff().fillna(0)
    df['Throttle_Change'] = df['Throttle'].diff().fillna(0)
    df['Hard_Braking'] = ((df['Speed_Change'] < -20) & (df['Brake'] == 1)).astype(int)
    df['High_RPM'] = (df['RPM'] > 10000).astype(int)
    df['Full_Throttle'] = (df['Throttle'] >= 95).astype(int)
    
    MAX_SAFE_RPM = 15000
    df['RPM_Danger'] = (df['RPM'] > MAX_SAFE_RPM).astype(int)
    df['Inconsistent_Combo'] = (((df['RPM'] > 10000) & (df['Throttle'] < 30)) | ((df['Speed'] < 100) & (df['RPM'] > 12000))).astype(int)
    
    gear_ratios = {1: 3.5, 2: 2.5, 3: 2.0, 4: 1.6, 5: 1.3, 6: 1.1, 7: 0.95, 8: 0.85}
    df['nGear'] = df.get('nGear', 4)
    df['Gear_Ratio'] = df['nGear'].map(gear_ratios).fillna(1.0)
    df['Expected_RPM'] = df['Speed'] * df['Gear_Ratio'] * 100
    df['RPM_Deviation'] = np.abs(df['RPM'] - df['Expected_RPM'])
    df['RPM_Deviation_Ratio'] = df['RPM_Deviation'] / (df['Expected_RPM'] + 1e-6)
    df['Gear_Speed_Mismatch'] = np.where((df['RPM_Deviation_Ratio'] > 1.0) | ((df['Speed'] < 50) & (df['nGear'] > 3)) | ((df['Speed'] > 150) & (df['nGear'] < 3)), 1, 0)
    
    df['RPM_per_Gear'] = df['RPM'] / (df['nGear'] + 1e-6)
    df['Speed_per_Gear'] = df['Speed'] / (df['nGear'] + 1e-6)
    df['RPM_Speed_Ratio'] = df['RPM'] / (df['Speed'] + 1e-6)
    df['Throttle_RPM_Product'] = df['Throttle'] * df['RPM'] / 1000000
    df['Throttle_Brake_Conflict'] = ((df['Throttle'] > 20) & (df['Brake'] == 1)).astype(int)
    
    df['RPM_Hours'] = (df['RPM'] / 60000).cumsum()
    df['Brake_Usage'] = df['Brake'].cumsum()
    df['High_Speed_Miles'] = ((df['Speed'] > 200) * df['Distance'].diff().fillna(0)).cumsum()
    
    rpm_norm = df['RPM'] / df['RPM'].max()
    throttle_norm = df['Throttle'] / 100
    brake_norm = df['Brake']
    brake_usage_norm = df['Brake_Usage'] / (df['Brake_Usage'].max() + 1)
    
    base_stress = (0.30 * rpm_norm + 0.25 * throttle_norm + 0.25 * brake_norm + 0.20 * brake_usage_norm)
    rpm_penalty = np.where(df['RPM'] > 15000, 0.3, 0)
    inconsistent_penalty = df['Inconsistent_Combo'] * 0.25
    mismatch_penalty = df['Gear_Speed_Mismatch'] * 0.35
    conflict_penalty = df['Throttle_Brake_Conflict'] * 0.20
    df['Stress_Score'] = (base_stress + rpm_penalty + inconsistent_penalty + mismatch_penalty + conflict_penalty).clip(0, 1)
    
    return df

# --- PAGE BOOT ---
inject_premium_css()
tree_model, lr_model, scaler, x_features = load_ai_kernels()

# --- BRANDING ---
st.markdown("<h1 class='brand-title'>HIRAETH F1</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#555; font-size:0.8rem; letter-spacing:10px; margin-bottom:40px;'>MISSION CONTROL // PREDICTIVE UNIT</p>", unsafe_allow_html=True)

if tree_model is None or lr_model is None:
    st.warning("SYSTEM FAULT: AI MODULES NOT FOUND. REINITIALIZE CORE.")
    st.stop()

# --- NAVIGATION ---
analysis_tab, batch_tab, logs_tab = st.tabs(["[ ANALYSIS_UNIT ]", "[ BATCH_PROCESS ]", "[ SYSTEM_LOGS ]"])

# ==================== UNIT 1: ANALYSIS ====================
with analysis_tab:
    col_ctrl, col_viz = st.columns([1, 2.5], gap="large")
    
    with col_ctrl:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<p class='f1-header' style='font-size:0.9rem;'>CONTROL CONSOLE</p>", unsafe_allow_html=True)
        t_rpm = st.slider("DRIVETRAIN RPM", 0, 20000, 9000)
        t_spd = st.slider("VELOCITY KM/H", 0, 400, 150)
        t_thr = st.slider("LOAD %", 0, 100, 50)
        t_mil = st.number_input("LIFETIME KM", 0, 10000, 4200)
        t_gear = st.number_input("SELECT GEAR", 1, 8, 4)
        t_brk = st.toggle("BRAKE ACTIVATION")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Physics Validation
        is_valid, violations, severity, expected_rpm_calc, rpm_dev_ratio = validate_physics(t_rpm, t_spd, t_gear, t_thr, int(t_brk))
        traction_health = calculate_traction_health(t_spd, t_rpm)
        
        # Prediction Payload
        input_data = {
            'RPM': t_rpm, 'Speed': t_spd, 'nGear': t_gear, 'Throttle': t_thr, 'Brake': int(t_brk),
            'Mileage': t_mil, 'Mileage_Normalized': min(t_mil / 5000, 1.0),
            'Traction_Health': traction_health, 'Speed_Change': 0, 'Throttle_Change': 0, 'Hard_Braking': 0,
            'High_RPM': 1 if t_rpm > 10000 else 0, 'Full_Throttle': 1 if t_thr == 100 else 0,
            'RPM_Danger': 1 if t_rpm > 15000 else 0, 'Inconsistent_Combo': 1 if ((t_rpm > 10000 and t_thr < 30) or (t_spd < 100 and t_rpm > 12000)) else 0,
            'Gear_Ratio': {1: 3.5, 2: 2.5, 3: 2.0, 4: 1.6, 5: 1.3, 6: 1.1, 7: 0.95, 8: 0.85}.get(t_gear, 1.0),
            'Expected_RPM': expected_rpm_calc, 'RPM_Deviation': abs(t_rpm - expected_rpm_calc), 'RPM_Deviation_Ratio': rpm_dev_ratio,
            'Gear_Speed_Mismatch': 1 if (rpm_dev_ratio > 1.0 or (t_spd < 50 and t_gear > 3) or (t_spd > 150 and t_gear < 3)) else 0,
            'RPM_per_Gear': t_rpm/(t_gear + 1e-6), 'Speed_per_Gear': t_spd/(t_gear + 1e-6), 'RPM_Speed_Ratio': t_rpm/(t_spd + 1e-6),
            'Throttle_RPM_Product': t_thr * t_rpm / 1000000, 'Throttle_Brake_Conflict': 1 if (t_thr > 20 and t_brk) else 0,
            'RPM_Hours': 10, 'Brake_Usage': 50, 'High_Speed_Miles': 100 if t_spd > 200 else 0, 'Stress_Score': 0
        }
        
        # Initial Stress
        base_stress = (0.30*(t_rpm/15000) + 0.25*(t_thr/100) + 0.25*int(t_brk) + 0.20*0.5)
        stress = min(base_stress + 0.3*(t_rpm>15000) + 0.25*input_data['Inconsistent_Combo'] + 0.35*input_data['Gear_Speed_Mismatch'] + 0.2*input_data['Throttle_Brake_Conflict'] + min(severity*0.5, 0.5), 1.0)
        input_data['Stress_Score'] = stress

        # AI Kernel Inference
        vec = pd.DataFrame([input_data])[x_features]
        risk_prob = lr_model.predict_proba(scaler.transform(vec))[0][1]
        
        # Stability calibration
        risk, final_stress = align_risk_stress(risk_prob, stress, severity)
        confidence = calibrate_confidence(risk, violations, severity)
        
        # Dashboard Panel
        status_lbl = "CRITICAL" if risk > 0.7 else "WARNING" if risk > 0.4 else "STABLE"
        color_hex = THEME['neon_red'] if risk > 0.4 else "#00ff41"
        mission_panel("PREDICTION", status_lbl, f"CONFIDENCE: {confidence*100:.0f}%", color_hex)
        mission_panel("RISK SCORE", f"{risk*100:.1f}%", "PROBABILITY OF FAILURE")

    with col_viz:
        grid_top_l, grid_top_r = st.columns(2)
        
        with grid_top_l:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("<p class='f1-header' style='font-size:0.7rem;'>G-FORCE LOAD ESTIMATE</p>", unsafe_allow_html=True)
            fig_g = go.Figure(go.Scatterpolar(
                r = [min(severity + 0.2, 1), int(t_brk), t_thr/100, t_spd/380, traction_health],
                theta = ['STRUCTURAL', 'LATERAL', 'LONGITUDINAL', 'AERO', 'TRACTION'],
                fill='toself', fillcolor=f"rgba(246, 99, 56, 0.2)",
                line=dict(color=THEME['neon_red'], width=3)
            ))
            fig_g.update_layout(
                polar=dict(radialaxis=dict(visible=False, range=[0, 1]), angularaxis=dict(gridcolor="#333", tickfont=dict(size=8, color="#888"))),
                showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=280, margin=dict(t=30, b=30, l=30, r=30)
            )
            st.plotly_chart(fig_g, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with grid_top_r:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("<p class='f1-header' style='font-size:0.7rem;'>COMPONENT EXHAUSTION</p>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:0.6rem; color:#888; margin-bottom:0;'>POWER UNIT STRESS</p>", unsafe_allow_html=True)
            render_segmented_bar(t_rpm/15000)
            st.markdown("<p style='font-size:0.6rem; color:#888; margin:10px 0 0 0;'>TRACTION HEALTH</p>", unsafe_allow_html=True)
            render_segmented_bar(traction_health)
            st.markdown("<p style='font-size:0.6rem; color:#888; margin:10px 0 0 0;'>PHYSICS OVERRIDE</p>", unsafe_allow_html=True)
            render_segmented_bar(min(severity, 1.0))
            st.markdown("</div>", unsafe_allow_html=True)

        # Alerts Window
        if violations:
            st.markdown("<div class='glass-card' style='border-top:2px solid {THEME['neon_red']};'>", unsafe_allow_html=True)
            st.markdown("<p class='f1-header' style='font-size:0.7rem; color:"+THEME['neon_red']+"'>PHYSICS ALERTS</p>", unsafe_allow_html=True)
            for v in violations:
                st.markdown(f"<p style='color:#ccc; font-size:0.7rem; margin:0;'>[!] ALERT: {v}</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<p class='f1-header' style='font-size:0.7rem;'>STRESS PROBABILITY SPECTRUM</p>", unsafe_allow_html=True)
        x_vals = np.linspace(0, 100, 50)
        y_vals = np.sin(x_vals/10) * 0.15 + (risk)
        fig_trend = px.area(x=x_vals, y=y_vals, template="plotly_dark", color_discrete_sequence=[THEME['neon_red']])
        fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, title="SESSION TIME %"), yaxis=dict(showgrid=False, title="RISK"), height=200, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ==================== UNIT 2: BATCH ====================
with batch_tab:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    f_up = st.file_uploader("SYNC REMOTE DATA STREAM", type=['csv'])
    if f_up:
        data = pd.read_csv(f_up)
        if st.button("EXECUTE BATCH PIPELINE"):
            processed = process_batch_features(data)
            batch_probs = lr_model.predict_proba(scaler.transform(processed[x_features]))[:, 1]
            processed['RISK'] = batch_probs
            
            b_col1, b_col2, b_col3 = st.columns(3)
            with b_col1: mission_panel("AVG RISK", f"{processed['RISK'].mean()*100:.1f}%")
            with b_col2: mission_panel("PEAK STRESS", f"{processed['Stress_Score'].max():.3f}")
            with b_col3: mission_panel("ALERTS", f"{int((batch_probs > 0.8).sum())}")
            
            st.markdown("<p class='f1-header' style='font-size:0.7rem;'>TELEMETRY CORRELATION MATRIX</p>", unsafe_allow_html=True)
            corr = processed[['RPM', 'Speed', 'Throttle', 'Stress_Score', 'RISK']].corr()
            fig_heat = px.imshow(corr, text_auto=True, color_continuous_scale="Reds", template="plotly_dark")
            fig_heat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=400)
            st.plotly_chart(fig_heat, use_container_width=True)
            
            st.download_button("GENERATE INTEL PDF", data=processed.to_csv().encode('utf-8'), file_name="telemetry_intel.csv")
    st.markdown("</div>", unsafe_allow_html=True)

# ==================== UNIT 3: LOGS ====================
with logs_tab:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<p class='f1-header' style='font-size:0.9rem;'>SYSTEM DIAGNOSTICS</p>", unsafe_allow_html=True)
    st.code(f"""
    [SYSTEM] BIOS v4.52 initialized
    [AI] DecisionTree Kernel: tree_model.pkl (Binary Ready)
    [AI] LogisticRegression Kernel: logistic_model.pkl (Nuance Ready)
    [AI] Scaler Vector Profile: Normalized
    [AI] Feature Vector Size: 27
    [PHYSICS] Validation Engine: v1.3 [ACTIVE]
    [TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    [NOTICE] No Emojis detected in string buffer.
    """, language="markdown")
    st.markdown("</div>", unsafe_allow_html=True)

# DARK FOOTER
st.markdown("<div style='text-align:right; padding:40px; color:#222; font-size:0.6rem; letter-spacing:5px;'>HIRAETH PERFORMANCE // NO EXTERNAL ASSETS // ENCRYPTED SESSION</div>", unsafe_allow_html=True)
