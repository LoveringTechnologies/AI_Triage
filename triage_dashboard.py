import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# Page config
st.set_page_config(page_title="AI Triage Dashboard", layout="wide")

# --- Mock Employee Database ---
NURSE_DB = {
    "NURSE101": {"name": "Sarah Jenkins", "dept": "Emergency Care"},
    "NURSE102": {"name": "Michael Chen", "dept": "Triage Unit"},
    "NURSE103": {"name": "Elena Rodriguez", "dept": "Critical Care"}
}

# --- Interaction Weights (High Risk Combinations) ---
HIGH_RISK_INTERACTIONS = {
    ("Asthma", "Wheezing"): 1.5,
    ("Asthma", "Shortness of breath"): 2.0,
    ("COPD", "Shortness of breath"): 2.0,
    ("COPD", "Cough"): 1.0,
    ("Heart Disease", "Chest pain"): 2.5,
    ("Heart Disease", "Shortness of breath"): 1.5,
    ("Type 2 Diabetes", "Confusion"): 2.0,
    ("Type 2 Diabetes", "Dizziness"): 1.0,
    ("Immunosuppression", "Fever"): 2.0,
    ("Hypertension", "Headache"): 1.0,
    ("Chronic Kidney Disease", "Nausea"): 1.0
}

# Initialize session state for login
if 'nurse_info' not in st.session_state:
    st.session_state.nurse_info = None

# --- Model Training Section ---
@st.cache_resource
def load_and_train_model():
    df = pd.read_csv('Model Training Data/ai_triage_balanced_dataset.csv')
    df['pre_existing_conditions'] = df['pre_existing_conditions'].fillna('None')
    df['current_medications'] = df['current_medications'].fillna('None')
    df['combined_text'] = df['pre_existing_conditions'] + " " + df['symptoms'] + " " + df['current_medications']
    df['sex_encoded'] = df['sex'].map({'M': 0, 'F': 1})
    
    inv_priority_map = {'Non-urgent': 0, 'Urgent': 1, 'Emergency': 2, 'Immediate': 3}
    df['target'] = df['triage_priority'].map(inv_priority_map)

    numeric_features = ['age', 'heart_rate', 'systolic_bp', 'diastolic_bp', 'respiratory_rate', 'spo2', 'temperature_c', 'blood_glucose', 'pain_score']
    X = df[numeric_features + ['sex_encoded', 'combined_text']]
    y = df['target']

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', 'passthrough', numeric_features + ['sex_encoded']),
            ('text', TfidfVectorizer(max_features=500), 'combined_text')
        ]
    )

    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])

    model.fit(X, y)
    
    all_symptoms = sorted(list(set(df['symptoms'].str.split(';').explode().unique())))
    all_conditions = sorted(list(set(df['pre_existing_conditions'].str.split(';').explode().unique())))
    
    return model, all_symptoms, all_conditions

# Initialize model
with st.spinner("Initializing AI Triage System..."):
    model, symptoms_list, conditions_list = load_and_train_model()

# --- Sidebar Login ---
st.sidebar.header("🔐 Staff Access")
if st.session_state.nurse_info is None:
    with st.sidebar:
        emp_id = st.sidebar.text_input("Enter Nurse Employee ID")
        if st.sidebar.button("Login"):
            if emp_id in NURSE_DB:
                st.session_state.nurse_info = NURSE_DB[emp_id]
                st.rerun()
            else:
                st.sidebar.error("Invalid Employee ID")
    st.sidebar.warning("Vitals entry is LOCKED. Please log in as a Nurse to input clinical data.")
else:
    st.sidebar.success(f"Logged in: {st.session_state.nurse_info['name']}")
    st.sidebar.info(f"Department: {st.session_state.nurse_info['dept']}")
    if st.sidebar.button("Logout"):
        st.session_state.nurse_info = None
        st.rerun()

# --- UI Layout ---
st.title("🏥 AI Emergency Triage System")
st.markdown("Enter patient information below. **Vital signs must be verified and entered by a registered nurse.**")

is_nurse = st.session_state.nurse_info is not None

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("👤 Patient Profile")
    dob = st.date_input("Date of Birth", value=date(1980, 1, 1), min_value=date(1900, 1, 1), max_value=date.today())
    
    # Calculate age
    today = date.today()
    calculated_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    st.info(f"Calculated Age: **{calculated_age} years**")
    
    sex = st.selectbox("Sex", ["M", "F"])
    
    st.write("---")
    st.subheader("🩺 Clinical Vitals" + (" (Locked)" if not is_nurse else " (Unlocked)"))
    vcol1, vcol2 = st.columns(2)
    with vcol1:
        hr = st.number_input("Heart Rate (BPM)", 30, 250, 75, disabled=not is_nurse)
        sbp = st.number_input("Systolic BP", 50, 250, 120, disabled=not is_nurse)
        dbp = st.number_input("Diastolic BP", 30, 150, 80, disabled=not is_nurse)
        temp = st.number_input("Temperature (°C)", 34.0, 43.0, 37.0, step=0.1, disabled=not is_nurse)
    with vcol2:
        spo2 = st.slider("SpO2 (%)", 50, 100, 98, disabled=not is_nurse)
        rr = st.number_input("Respiratory Rate", 8, 60, 16, disabled=not is_nurse)
        glucose = st.number_input("Blood Glucose (mg/dL)", 50, 500, 100, disabled=not is_nurse)
        pain = st.slider("Pain Score (0-10)", 0, 10, 0, disabled=not is_nurse)

with col2:
    st.subheader("📋 Patient-Provided Info")
    conditions = st.multiselect("Pre-existing Conditions", [c for c in conditions_list if str(c) != 'nan'])
    symptoms = st.multiselect("Presenting Symptoms", symptoms_list)
    meds = st.text_input("Current Medications (comma separated)", "None")
    
    st.write("---")
    if st.button("RUN TRIAGE ASSESSMENT", type="primary", use_container_width=True):
        # 1. AI Model Prediction
        sex_enc = 0 if sex == 'M' else 1
        combined_text = f"{';'.join(conditions)} {';'.join(symptoms)} {meds}"
        
        input_data = pd.DataFrame([{
            'age': calculated_age,
            'heart_rate': hr,
            'systolic_bp': sbp,
            'diastolic_bp': dbp,
            'respiratory_rate': rr,
            'spo2': spo2,
            'temperature_c': temp,
            'blood_glucose': glucose,
            'pain_score': pain,
            'sex_encoded': sex_enc,
            'combined_text': combined_text
        }])
        
        # Get raw probabilities from model
        probs = model.predict_proba(input_data)[0]
        # Current priority index
        priority_idx = np.argmax(probs)
        
        # 2. Apply Custom Weighting (Interaction logic)
        detected_interactions = []
        weight_boost = 0.0
        
        for (cond, sym), boost in HIGH_RISK_INTERACTIONS.items():
            if cond in conditions and sym in symptoms:
                weight_boost += boost
                detected_interactions.append(f"**High Risk Interaction**: {sym} + {cond} (+{boost} priority weight)")
        
        final_priority_idx = int(min(3, priority_idx + np.floor(weight_boost)))
        
        priority_map = {0: 'Non-urgent', 1: 'Urgent', 2: 'Emergency', 3: 'Immediate'}
        result = priority_map[final_priority_idx]
        
        colors = {"Non-urgent": "green", "Urgent": "blue", "Emergency": "orange", "Immediate": "red"}
        icons = {"Non-urgent": "✅", "Urgent": "⚠️", "Emergency": "🚨", "Immediate": "🆘"}
        
        st.header(f"Result: :{colors[result]}[{icons[result]} {result.upper()}]")
        
        if is_nurse:
            st.info(f"✅ Assessment verified by: {st.session_state.nurse_info['name']} ({st.session_state.nurse_info['dept']})")
        else:
            st.warning("⚠️ PROVISIONAL RESULT: Vitals have not been verified by clinical staff.")

        # AI & Interaction Reasoning
        st.subheader("Clinical Reasoning:")
        if detected_interactions:
            for interaction in detected_interactions:
                st.markdown(interaction)
        
        reasons = []
        if hr > 120 or hr < 50: reasons.append(f"Abnormal Heart Rate: {hr} BPM")
        if spo2 < 92: reasons.append(f"Low Oxygen Saturation: {spo2}%")
        if sbp > 160 or sbp < 90: reasons.append(f"Abnormal Systolic BP: {sbp}")
        if temp > 38.5 or temp < 35.5: reasons.append(f"Abnormal Temperature: {temp}°C")
        if rr > 25 or rr < 10: reasons.append(f"Critical Respiratory Rate: {rr}")
        
        if reasons:
            for r in reasons:
                st.write(f"- {r}")
        elif not detected_interactions:
            st.write("Patient vitals and clinical context are within stable ranges. Triage based on presenting symptoms and history.")

st.sidebar.info("This is an AI prototype for triage support. Clinical decisions should always be verified by medical professionals.")
