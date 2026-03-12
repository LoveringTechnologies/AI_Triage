import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from datetime import date, datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import os

# --- Page configuration ---
st.set_page_config(page_title="AI Emergency Triage System", layout="wide", page_icon="🏥")

# --- Custom CSS for Mobile-App Look ---
st.markdown("""
<style>
    .main {
        background-color: #f0f2f5;
    }
    .stApp {
        background-color: #f0f2f5;
    }
    div.stButton > button {
        background-color: #3498db;
        color: white;
        border-radius: 15px;
        padding: 15px 25px;
        font-weight: 800;
        border: none;
        width: 100%;
        margin-top: 10px;
    }
    div.stButton > button:hover {
        background-color: #2980b9;
        color: white;
    }
    .section-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .header-bar {
        background-color: white;
        padding: 15px 20px;
        border-bottom: 1px solid #e1e8ed;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .header-title {
        font-size: 24px;
        font-weight: 900;
        color: #2c3e50;
        letter-spacing: 2px;
    }
    .online-dot {
        height: 12px;
        width: 12px;
        background-color: #27ae60;
        border-radius: 50%;
        display: inline-block;
        margin-left: 10px;
    }
    .result-card {
        padding: 25px;
        background-color: white;
        border-radius: 20px;
        border: 6px solid #3498db;
        margin-top: 25px;
    }
    .protocol-step {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
        font-size: 14px;
        color: #34495e;
        font-weight: 600;
    }
    .protocol-checkbox {
        margin-right: 10px;
    }
    .staff-badge {
        background-color: #f8f9fa;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 12px;
        color: #7f8c8d;
        border: 1px solid #ecf0f1;
    }
</style>
""", unsafe_allow_html=True)

DB_PATH = "triage.db"

# --- Database Helper ---
def get_db_connection():
    return sqlite3.connect(DB_PATH)

# --- Staff Authentication ---
def verify_staff(staff_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, dept, role FROM users WHERE id = ?", (staff_id.upper(),))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"id": user[0], "name": user[1], "dept": user[2], "role": user[3]}
    return None

# --- Clinical Intelligence Layer (Aligned with API) ---
CLINICAL_WEIGHTS = {
    "symptoms": {
        "Chest pain": 2.5, "Shortness of breath": 2.0, "Confusion": 2.5, 
        "Limb numbness": 2.0, "Dizziness": 1.0, "Fever": 0.5, "Abdominal pain": 1.0
    },
    "conditions": {
        "Heart Disease": 1.5, "COPD": 1.5, "Diabetes": 0.5, "Asthma": 1.0, "Cancer": 1.0
    }
}

def apply_physiological_coupling(age, hr, sbp, dbp, rr, spo2, temp, glucose, symptoms):
    """Expert system layer for physiological coupling and emergency patterns."""
    boost = 0.0
    reasoning = []
    is_teen = age < 18
    
    if is_teen:
        hr_thresh = 100; hr_crit = 120; rr_thresh = 20; rr_crit = 30; sbp_hypo = 90
    else:
        hr_thresh = 100; hr_crit = 130; rr_thresh = 20; rr_crit = 26; sbp_hypo = 90

    if temp > 38.5 and hr > hr_thresh and rr > rr_thresh:
        if sbp < sbp_hypo:
            boost += 3.0
            reasoning.append(f"Sepsis Protocol Triggered ({'Paed' if is_teen else 'Adult'})")
        else:
            boost += 1.5
            reasoning.append("SIRS Criteria Met (High HR/RR + Fever)")

    if "Chest pain" in symptoms:
        if hr > hr_crit or sbp > 160 or sbp < sbp_hypo:
            boost += 2.5
            reasoning.append("Acute Cardiac Event Suspected (Chest Pain + Vital Instability)")

    if spo2 < 92:
        if rr > rr_crit:
            boost += 3.0
            reasoning.append(f"Respiratory Failure Risk ({'Paed' if is_teen else 'Adult'})")
        else:
            boost += 1.5
            reasoning.append("Hypoxia Detected")

    if sbp > 0:
        shock_index = hr / sbp
        if shock_index > 1.0:
            boost += 2.5
            reasoning.append(f"Critical Shock Index ({shock_index:.2f}) - Hidden Hypoperfusion Risk")

    if glucose < 70:
        if glucose < 50:
            boost += 3.0
            reasoning.append(f"Critical Hypoglycemia ({glucose} mg/dL)")
        else:
            boost += 2.0
            reasoning.append(f"Hypoglycemia ({glucose} mg/dL)")

    neuro_symptoms = ["Slurred speech", "Facial drooping", "Limb numbness", "Weakness", "Confusion", "Vision changes"]
    if any(s in symptoms for s in neuro_symptoms):
        if sbp > 180 or dbp > 110:
            boost += 3.0
            reasoning.append("Stroke Alert (Neuro Symptoms + Hypertensive Crisis)")
        else:
            boost += 1.5
            reasoning.append("Neurological Deficit Detected")

    return boost, reasoning

# --- Model Training ---
@st.cache_resource
def load_and_train_model():
    df = pd.read_csv('Model Training Data/ai_triage_clinical_v2.csv')
    df['pre_existing_conditions'] = df['pre_existing_conditions'].fillna('None')
    df['combined_text'] = df['pre_existing_conditions'] + " " + df['symptoms']
    df['sex_encoded'] = df['sex'].map({'M': 0, 'F': 1})
    
    target_map = {
        'Zone 1 (Resuscitation)': 4, 'Zone 2 (Emergent)': 3, 'Zone 3 (Urgent)': 2,
        'Zone 4 (Less-Urgent)': 1, 'Zone 5 (Non-Urgent)': 0
    }
    df['target'] = df['triage_priority'].map(target_map)
    
    numeric_features = ['age', 'heart_rate', 'systolic_bp', 'diastolic_bp', 'respiratory_rate', 'spo2', 'temperature_c', 'blood_glucose', 'pain_score']
    X = df[numeric_features + ['sex_encoded', 'combined_text']]
    y = df['target']
    
    preprocessor = ColumnTransformer([
        ('num', 'passthrough', numeric_features + ['sex_encoded']),
        ('text', TfidfVectorizer(max_features=500), 'combined_text')
    ])
    
    model = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    
    model.fit(X, y)
    symptoms = sorted(list(set(df['symptoms'].str.split(';').explode().unique())))
    conditions = sorted(list(set(df['pre_existing_conditions'].str.split(';').explode().unique())))
    return model, symptoms, [c for c in conditions if str(c) != 'nan']

# --- Session State ---
if 'staff' not in st.session_state:
    st.session_state.staff = None

# Initialize model
with st.spinner("🏥 Initializing AI Clinical Suite..."):
    model, symptoms_list, conditions_list = load_and_train_model()

# --- Header ---
st.markdown(f"""
<div class="header-bar">
    <div class="header-title">🏥 AI TRIAGE {f'<span class="online-dot"></span>' if st.session_state.staff else ''}</div>
    <div class="staff-badge">{st.session_state.staff['name'] if st.session_state.staff else 'Guest Access'}</div>
</div>
""", unsafe_allow_html=True)

# --- Sidebar Staff Portal ---
with st.sidebar:
    st.header("🔑 Staff Portal")
    if not st.session_state.staff:
        emp_id = st.text_input("Enter Staff ID (e.g., NURSE101)", type="password")
        if st.button("Access Clinical Suite"):
            user = verify_staff(emp_id)
            if user:
                st.session_state.staff = user
                st.rerun()
            else:
                st.error("Invalid Staff ID")
    else:
        st.success(f"Verified: {st.session_state.staff['name']}")
        st.info(f"{st.session_state.staff['role']} | {st.session_state.staff['dept']}")
        if st.button("Logout"):
            st.session_state.staff = None
            st.rerun()
    
    st.divider()
    st.markdown("### 📊 Operational View")
    view_mode = st.radio("Switch View", ["Triage Assessment", "Live ER Census", "Audit Logs"])

if view_mode == "Triage Assessment":
    # --- Main Triage Form ---
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("👤 Patient Profile")
        patient_name = st.text_input("Patient Full Name", placeholder="e.g. John Doe")
        
        vcol1, vcol2 = st.columns(2)
        with vcol1:
            dob = st.date_input("Date of Birth", value=date(1990, 1, 1), min_value=date(1900, 1, 1), max_value=date.today())
            age = date.today().year - dob.year - ((date.today().month, date.today().day) < (dob.month, dob.day))
        with vcol2:
            sex = st.selectbox("Sex", ["M", "F"])
        
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("📋 Patient History")
        sel_symptoms = st.multiselect("Presenting Symptoms", symptoms_list)
        sel_conditions = st.multiselect("Pre-existing Conditions", conditions_list)
        meds = st.text_input("Current Medications", "None")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        is_clinical = st.session_state.staff is not None
        locked_style = ' style="opacity: 0.5; border: 2px dashed #bdc3c7;"' if not is_clinical else ""
        
        st.markdown(f'<div class="section-card"{locked_style}>', unsafe_allow_html=True)
        st.subheader("🩺 Clinical Vitals" + (" (Staff Only)" if not is_clinical else ""))
        
        vcol1, vcol2 = st.columns(2)
        with vcol1:
            pain_loc = st.selectbox("Pain Location", ["None", "Head & Spine", "Chest", "Neck", "Body"], disabled=not is_clinical)
            pain_area = st.selectbox("Specific Area", ["None", "Chest", "Neck", "Head", "Abdomen", "Back", "Limbs"], disabled=not is_clinical or pain_loc == "None")
            pain_score = st.slider("Pain Score (0-10)", 0, 10, 0, disabled=not is_clinical)
            hr = st.number_input("Heart Rate (BPM)", 30, 250, 75, disabled=not is_clinical)
            sbp = st.number_input("Systolic BP", 50, 250, 120, disabled=not is_clinical)
        with vcol2:
            dbp = st.number_input("Diastolic BP", 30, 150, 80, disabled=not is_clinical)
            temp = st.number_input("Temp (°C)", 34.0, 43.0, 37.0, step=0.1, disabled=not is_clinical)
            spo2 = st.slider("SpO2 (%)", 50, 100, 98, disabled=not is_clinical)
            rr = st.number_input("Resp Rate", 8, 60, 16, disabled=not is_clinical)
            glucose = st.number_input("Glucose (mg/dL)", 50, 500, 100, disabled=not is_clinical)
            manual_boost = st.number_input("Manual Weight", -5.0, 5.0, 0.0, step=0.5, help="Emergency Override", disabled=not is_clinical)

        if not is_clinical:
            st.warning("Staff authentication required to input vitals.")
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("GENERATE TRIAGE REPORT"):
        if not patient_name:
            st.error("Please enter Patient Name")
        else:
            # 1. ML Prediction
            sex_enc = 0 if sex == 'M' else 1
            combined_text = f"{';'.join(sel_conditions)} {';'.join(sel_symptoms)}"
            input_df = pd.DataFrame([{
                'age': age, 'heart_rate': hr, 'systolic_bp': sbp, 'diastolic_bp': dbp, 
                'respiratory_rate': rr, 'spo2': spo2, 'temperature_c': temp, 
                'blood_glucose': glucose, 'pain_score': pain_score, 
                'sex_encoded': sex_enc, 'combined_text': combined_text
            }])
            
            ml_priority_idx = model.predict(input_df)[0]
            
            # 2. Clinical Overlay
            clinical_boost = manual_boost
            detected_interactions = []
            
            for sym in sel_symptoms:
                if sym in CLINICAL_WEIGHTS["symptoms"]:
                    weight = CLINICAL_WEIGHTS["symptoms"][sym]
                    clinical_boost += weight
                    detected_interactions.append(f"High-Risk Symptom: {sym} (+{weight})")
            
            for cond in sel_conditions:
                if cond in CLINICAL_WEIGHTS["conditions"]:
                    weight = CLINICAL_WEIGHTS["conditions"][cond]
                    clinical_boost += weight
                    detected_interactions.append(f"Condition Risk: {cond} (+{weight})")

            coupling_boost, coupling_reasons = apply_physiological_coupling(age, hr, sbp, dbp, rr, spo2, temp, glucose, sel_symptoms)
            clinical_boost += coupling_boost
            detected_interactions.extend(coupling_reasons)
            
            if pain_loc in ["Head & Spine", "Chest", "Neck"] and pain_score >= 7:
                clinical_boost += 1.5
                detected_interactions.append(f"Critical Anatomy: {pain_loc} Trauma")

            # 3. Final Zone
            final_score = ml_priority_idx + np.floor(clinical_boost)
            final_priority_idx = int(max(0, min(4, final_score)))
            
            zone_map = {4: 1, 3: 2, 2: 3, 1: 4, 0: 5}
            priority_map = {4: 'Resuscitation', 3: 'Emergent', 2: 'Urgent', 1: 'Less-Urgent', 0: 'Non-Urgent'}
            color_map = {1: 'red', 2: 'orange', 3: '#f1c40f', 4: 'blue', 5: 'green'}
            
            res_zone = zone_map[final_priority_idx]
            res_priority = priority_map[final_priority_idx]
            res_color = color_map[res_zone]

            # 4. Protocols
            next_steps = []
            if res_zone == 1:
                next_steps = ["🚀 Life-Saving Intervention", "🩸 Type & Cross (2 units)", "🏥 Immediate MD Evaluation", "📈 Continuous Cardiac Monitoring"]
            elif res_zone == 2:
                next_steps = ["🕒 Physician Review within 15m", "💉 Start Peripheral IV", "🧪 Stat Labs (CBC, Lytes, Trop)", "🩺 Re-evaluate vitals every 15m"]
            
            for reason in coupling_reasons:
                if "Sepsis" in reason: next_steps.extend(["💧 30mL/kg Fluid Bolus", "💊 Stat Antibiotics", "🧪 Draw Blood Cultures x2"])
                if "Stroke" in reason: next_steps.extend(["🧠 Activate Code Stroke", "☢️ Stat CT Head", "🩸 POC Glucose"])
                if "Cardiac" in reason: next_steps.extend(["💓 Stat 12-Lead EKG", "🍬 Aspirin 324mg PO", "🧪 Serial Troponins"])

            # Remove duplicates
            next_steps = list(dict.fromkeys(next_steps))

            # Result UI
            st.markdown(f"""
            <div class="result-card" style="border-color: {res_color}">
                <h1 style="color: {res_color}; text-align: center; font-weight: 900; margin-bottom: 0;">{res_priority.upper()}</h1>
                <h3 style="text-align: center; margin-top: 0;">Please move to Zone {res_zone}</h3>
            </div>
            """, unsafe_allow_html=True)

            rcol1, rcol2 = st.columns(2)
            with rcol1:
                st.subheader("🧠 Clinical Reasoning")
                if detected_interactions:
                    for item in detected_interactions:
                        st.markdown(f"⚠️ {item}")
                else:
                    st.write("Vitals and context are within stable ranges.")
            
            with rcol2:
                st.subheader("📋 Next Steps Protocol")
                if next_steps:
                    for step in next_steps:
                        st.markdown(f'<div class="protocol-step">⬜ {step}</div>', unsafe_allow_html=True)
                else:
                    st.write("Follow standard assessment protocols.")

            # Database Logging
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                vitals_data = f"HR:{hr}, BP:{sbp}/{dbp}, SpO2:{spo2}"
                cursor.execute('''INSERT INTO triage_logs (timestamp, patient_name, age, sex, priority, zone, score_details, staff_id, vitals_json, symptoms_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                               (datetime.now().isoformat(), patient_name, age, sex, res_priority, res_zone, ", ".join(detected_interactions), st.session_state.staff['id'] if st.session_state.staff else None, vitals_data, ";".join(sel_symptoms)))
                conn.commit()
                conn.close()
            except Exception as e:
                st.error(f"Failed to log to database: {e}")

elif view_mode == "Live ER Census":
    st.subheader("🏥 Live ER Census")
    try:
        conn = get_db_connection()
        df_census = pd.read_sql_query("SELECT patient_name, zone, priority, timestamp, vitals_json FROM triage_logs WHERE is_active = 1 ORDER BY zone ASC, timestamp DESC", conn)
        conn.close()
        
        if df_census.empty:
            st.info("No active patients in census.")
        else:
            for zone in range(1, 6):
                z_data = df_census[df_census['zone'] == zone]
                color_map = {1: 'red', 2: 'orange', 3: '#f1c40f', 4: 'blue', 5: 'green'}
                
                with st.expander(f"ZONE {zone} ({len(z_data)} Patients)", expanded=zone <= 2):
                    if z_data.empty:
                        st.write("No active patients")
                    else:
                        for _, row in z_data.iterrows():
                            ccol1, ccol2 = st.columns([4, 1])
                            with ccol1:
                                st.markdown(f"**{row['patient_name']}** | {row['vitals_json']} | {row['priority']}")
                                st.caption(f"Triage Time: {row['timestamp']}")
                            with ccol2:
                                if st.button("Discharge", key=f"dis_{row['patient_name']}"):
                                    conn = get_db_connection()
                                    conn.execute("UPDATE triage_logs SET is_active = 0 WHERE patient_name = ?", (row['patient_name'],))
                                    conn.commit()
                                    conn.close()
                                    st.rerun()
    except Exception as e:
        st.error(f"Census Error: {e}")

elif view_mode == "Audit Logs":
    st.subheader("📋 Clinical Audit Logs")
    try:
        conn = get_db_connection()
        # Join with users to get staff name
        query = """
            SELECT l.timestamp, l.patient_name, l.priority, l.zone, u.name as staff_name, l.score_details 
            FROM triage_logs l 
            LEFT JOIN users u ON l.staff_id = u.id 
            ORDER BY l.timestamp DESC 
            LIMIT 50
        """
        df_logs = pd.read_sql_query(query, conn)
        conn.close()
        st.dataframe(df_logs, use_container_width=True)
    except Exception as e:
        st.error(f"Logs Error: {e}")

st.divider()
st.caption("AI Clinical Prototype v2.1.0 | Standard of Care: CTAS/PaedCTAS Hybrid Engine")
