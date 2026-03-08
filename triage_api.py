import sqlite3
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="AI Triage API", version="1.4.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "triage.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT, dept TEXT, role TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS triage_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, patient_name TEXT, age INTEGER, sex TEXT,
        priority TEXT, zone INTEGER, score_details TEXT, staff_id TEXT, vitals_json TEXT, symptoms_json TEXT,
        is_active INTEGER DEFAULT 1)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, staff_id TEXT, message TEXT, is_read INTEGER DEFAULT 0)''')
    
    # Staff Data
    staff_data = [
        ("NURSE101", "Sarah Jenkins", "Emergency Care", "Nurse"),
        ("NURSE102", "Michael Chen", "Triage Unit", "Nurse"),
        ("DR201", "Dr. James Wilson", "Critical Care", "Doctor")
    ]
    for s in staff_data:
        cursor.execute("INSERT OR REPLACE INTO users (id, name, dept, role) VALUES (?, ?, ?, ?)", s)
    conn.commit(); conn.close()

model_pipeline = None; symptoms_list = []; conditions_list = []

# --- CLINICAL INTELLIGENCE LAYER: WEIGHTS & COUPLING ---
CLINICAL_WEIGHTS = {
    "symptoms": {
        "Chest pain": 2.5, "Shortness of breath": 2.0, "Confusion": 2.5, 
        "Limb numbness": 2.0, "Dizziness": 1.0, "Fever": 0.5, "Abdominal pain": 1.0
    },
    "conditions": {
        "Heart Disease": 1.5, "COPD": 1.5, "Diabetes": 0.5, "Asthma": 1.0, "Cancer": 1.0
    }
}

def apply_physiological_coupling(patient: "PatientData"):
    """Expert system layer for physiological coupling and emergency patterns."""
    boost = 0.0
    reasoning = []
    
    # --- AGE-STRATIFIED THRESHOLDS (CTAS vs PaedCTAS) ---
    is_teen = patient.age < 18
    
    # Thresholds: [Normal_Upper, Critical_Upper, Hypotension_Lower]
    if is_teen:
        # Paediatric Teen (12-18) Modifiers
        hr_thresh = 100; hr_crit = 120
        rr_thresh = 20; rr_crit = 30
        sbp_hypo = 90
    else:
        # Adult (18+) Modifiers
        hr_thresh = 100; hr_crit = 130
        rr_thresh = 20; rr_crit = 26
        sbp_hypo = 90

    # Sepsis Pattern: Fever + HR Spike + RR Spike + BP Drop
    if patient.temperature_c > 38.5 and patient.heart_rate > hr_thresh and patient.respiratory_rate > rr_thresh:
        if patient.systolic_bp < sbp_hypo:
            boost += 3.0
            reasoning.append(f"Sepsis Protocol Triggered ({'Paed' if is_teen else 'Adult'})")
        else:
            boost += 1.5
            reasoning.append("SIRS Criteria Met (High HR/RR + Fever)")

    # Cardiac Pattern: Chest Pain + HR Spike or BP Abnormalities
    if "Chest pain" in patient.symptoms:
        if patient.heart_rate > hr_crit or patient.systolic_bp > 160 or patient.systolic_bp < sbp_hypo:
            boost += 2.5
            reasoning.append("Acute Cardiac Event Suspected (Chest Pain + Vital Instability)")

    # Respiratory Failure: Low SpO2 + High RR
    if patient.spo2 < 92:
        if patient.respiratory_rate > rr_crit:
            boost += 3.0
            reasoning.append(f"Respiratory Failure Risk ({'Paed' if is_teen else 'Adult'})")
        else:
            boost += 1.5
            reasoning.append("Hypoxia Detected")

    # Fever/HR Coupling check (Clinical Context)
    temp_elevation = max(0, patient.temperature_c - 37.0)
    expected_hr_increase = temp_elevation * 10
    if patient.heart_rate > (hr_thresh + expected_hr_increase):
        boost += 1.0
        reasoning.append("Uncompensated Tachycardia (HR disproportionately high for temperature)")

    # Stroke Protocol (FAST + Hypertension)
    neuro_symptoms = ["Slurred speech", "Facial drooping", "Limb numbness", "Weakness", "Confusion", "Vision changes"]
    has_neuro = any(s in patient.symptoms for s in neuro_symptoms)
    if has_neuro:
        if patient.systolic_bp > 180 or patient.diastolic_bp > 110:
            boost += 3.0
            reasoning.append("Stroke Alert (Neuro Symptoms + Hypertensive Crisis)")
        elif patient.systolic_bp > 140:
            boost += 2.0
            reasoning.append("Possible CVA (Neuro Symptoms + Hypertension)")
        else:
            boost += 1.5
            reasoning.append("Neurological Deficit Detected")

    # Shock Index (SI) = HR / SBP
    # Normal: 0.5-0.7. > 0.9 indicates shock potential. > 1.0 is critical.
    if patient.systolic_bp > 0:
        shock_index = patient.heart_rate / patient.systolic_bp
        if shock_index > 1.0:
            boost += 2.5
            reasoning.append(f"Critical Shock Index ({shock_index:.2f}) - Hidden Hypoperfusion Risk")
        elif shock_index > 0.9:
            boost += 1.5
            reasoning.append(f"Elevated Shock Index ({shock_index:.2f})")

    # Hypoglycemia Protocol
    if patient.blood_glucose < 70:
        if patient.blood_glucose < 50:
            boost += 3.0
            reasoning.append(f"Critical Hypoglycemia ({patient.blood_glucose} mg/dL)")
        else:
            boost += 2.0
            reasoning.append(f"Hypoglycemia ({patient.blood_glucose} mg/dL)")

    return boost, reasoning

class PatientData(BaseModel):
    name: str = "Anonymous"
    age: int; sex: str; heart_rate: float; systolic_bp: float; diastolic_bp: float
    respiratory_rate: float; spo2: float; temperature_c: float; blood_glucose: float
    pain_score: int; pain_location: str = "Body"; pain_specific_area: str = "General"
    pre_existing_conditions: List[str]; symptoms: List[str]; current_medications: str = "None"
    staff_id: Optional[str] = None 
    manual_boost: float = 0.0

class TriageResponse(BaseModel):
    priority: str; zone: int; color_code: str; reasoning: List[str]; detected_interactions: List[str]
    next_steps: List[str] = []

@app.on_event("startup")
def startup():
    global model_pipeline, symptoms_list, conditions_list
    init_db()
    # Use the new high-fidelity clinical dataset
    df = pd.read_csv('Model Training Data/ai_triage_clinical_v2.csv')
    df['pre_existing_conditions'] = df['pre_existing_conditions'].fillna('None')
    df['combined_text'] = df['pre_existing_conditions'] + " " + df['symptoms']
    df['sex_encoded'] = df['sex'].map({'M': 0, 'F': 1})
    
    # 5-Zone Target Mapping
    target_map = {
        'Zone 1 (Resuscitation)': 4,
        'Zone 2 (Emergent)': 3,
        'Zone 3 (Urgent)': 2,
        'Zone 4 (Less-Urgent)': 1,
        'Zone 5 (Non-Urgent)': 0
    }
    df['target'] = df['triage_priority'].map(target_map)
    
    numeric_features = ['age', 'heart_rate', 'systolic_bp', 'diastolic_bp', 'respiratory_rate', 'spo2', 'temperature_c', 'blood_glucose', 'pain_score']
    X = df[numeric_features + ['sex_encoded', 'combined_text']]
    y = df['target']
    
    preprocessor = ColumnTransformer([
        ('num', 'passthrough', numeric_features + ['sex_encoded']),
        ('text', TfidfVectorizer(max_features=500), 'combined_text')
    ])
    
    model_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])
    
    model_pipeline.fit(X, y)
    symptoms_list = sorted(list(set(df['symptoms'].str.split(';').explode().unique())))
    conditions_list = sorted(list(set(df['pre_existing_conditions'].str.split(';').explode().unique())))

@app.get("/metadata")
def get_metadata():
    return {"symptoms": symptoms_list, "conditions": [c for c in conditions_list if str(c) != 'nan']}

@app.get("/verify-staff/{staff_id}")
def verify_staff(staff_id: str):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT id, name, dept, role FROM users WHERE id = ?", (staff_id.upper(),))
    user = cursor.fetchone(); conn.close()
    if user: return {"id": user[0], "name": user[1], "dept": user[2], "role": user[3]}
    raise HTTPException(status_code=404, detail="Invalid Staff ID")

@app.get("/notifications/{staff_id}")
def get_notifications(staff_id: str):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("SELECT id, message, timestamp FROM notifications WHERE (staff_id = ? OR staff_id IS NULL) AND is_read = 0 ORDER BY id DESC", (staff_id.upper(),))
    notes = cursor.fetchall()
    # Mark as read immediately to stop repeat alerts
    if notes:
        ids = [str(n[0]) for n in notes]
        cursor.execute(f"UPDATE notifications SET is_read = 1 WHERE id IN ({','.join(ids)})")
    conn.commit(); conn.close()
    return [{"id": n[0], "message": n[1], "time": n[2]} for n in notes]

@app.post("/predict", response_model=TriageResponse)
def predict_triage(patient: PatientData):
    if not model_pipeline: raise HTTPException(status_code=503, detail="Model not loaded")
    
    # 1. Prepare ML Prediction
    sex_enc = 0 if patient.sex == 'M' else 1
    combined_text = f"{';'.join(patient.pre_existing_conditions)} {';'.join(patient.symptoms)} {patient.current_medications}"
    input_df = pd.DataFrame([{
        'age': patient.age, 'heart_rate': patient.heart_rate, 'systolic_bp': patient.systolic_bp, 
        'diastolic_bp': patient.diastolic_bp, 'respiratory_rate': patient.respiratory_rate, 
        'spo2': patient.spo2, 'temperature_c': patient.temperature_c, 
        'blood_glucose': patient.blood_glucose, 'pain_score': patient.pain_score, 
        'sex_encoded': sex_enc, 'combined_text': combined_text
    }])
    
    # ML predicted base level (0 to 4)
    ml_priority_idx = model_pipeline.predict(input_df)[0]
    
    # 2. Apply Clinical Intelligence Overlay
    clinical_boost = patient.manual_boost
    detected_interactions = []
    
    # A. Static Weights
    for sym in patient.symptoms:
        if sym in CLINICAL_WEIGHTS["symptoms"]:
            weight = CLINICAL_WEIGHTS["symptoms"][sym]
            clinical_boost += weight
            detected_interactions.append(f"High-Risk Symptom: {sym} (+{weight})")
            
    for cond in patient.pre_existing_conditions:
        if cond in CLINICAL_WEIGHTS["conditions"]:
            weight = CLINICAL_WEIGHTS["conditions"][cond]
            clinical_boost += weight
            detected_interactions.append(f"Condition Risk: {cond} (+{weight})")

    # B. Physiological Coupling (The "Safety Floor")
    coupling_boost, coupling_reasons = apply_physiological_coupling(patient)
    clinical_boost += coupling_boost
    detected_interactions.extend(coupling_reasons)
    
    # C. Anatomical Location Boost
    if patient.pain_location in ["Head & Spine", "Chest", "Neck"] and patient.pain_score >= 7:
        clinical_boost += 1.5
        detected_interactions.append(f"Critical Anatomy: {patient.pain_location} Trauma")

    # 3. Final Zone Calculation
    # We round the boost. Every +1.0 boost shifts the zone up (closer to Zone 1).
    final_score = ml_priority_idx + np.floor(clinical_boost)
    final_priority_idx = int(max(0, min(4, final_score)))
    
    # Map index 4 -> Zone 1, 3 -> Zone 2, 2 -> Zone 3, 1 -> Zone 4, 0 -> Zone 5
    zone_map = {4: 1, 3: 2, 2: 3, 1: 4, 0: 5}
    priority_map = {4: 'Resuscitation', 3: 'Emergent', 2: 'Urgent', 1: 'Less-Urgent', 0: 'Non-Urgent'}
    color_map = {1: 'red', 2: 'orange', 3: '#f1c40f', 4: 'blue', 5: 'green'}
    
    res_zone = zone_map[final_priority_idx]
    res_priority = priority_map[final_priority_idx]

    # 4. Protocol Checklists (Next Steps)
    next_steps = []
    if res_zone == 1:
        next_steps = ["🚀 Life-Saving Intervention", "🩸 Type & Cross (2 units)", "🏥 Immediate MD Evaluation", "📈 Continuous Cardiac Monitoring"]
    elif res_zone == 2:
        next_steps = ["🕒 Physician Review within 15m", "💉 Start Peripheral IV", "🧪 Stat Labs (CBC, Lytes, Trop)", "🩺 Re-evaluate vitals every 15m"]
    
    # Specific condition protocols
    for reason in coupling_reasons:
        if "Sepsis" in reason:
            next_steps.extend(["💧 30mL/kg Fluid Bolus", "💊 Stat Antibiotics", "🧪 Draw Blood Cultures x2", "📊 Monitor Lactate"])
        if "Stroke" in reason:
            next_steps.extend(["🧠 Activate Code Stroke", "☢️ Stat CT Head (Non-contrast)", "🩸 Point of Care Glucose", "⏱ Last Known Well Time?"])
        if "Cardiac" in reason:
            next_steps.extend(["💓 Stat 12-Lead EKG", "🍬 Aspirin 324mg PO", "🧪 Serial Troponins", "🫁 Monitor SpO2 (>94%)"])

    # Remove duplicates but keep order
    next_steps = list(dict.fromkeys(next_steps))

    # Database Logging
    try:
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        vitals_data = f"HR:{patient.heart_rate}, BP:{patient.systolic_bp}/{patient.diastolic_bp}, SpO2:{patient.spo2}"
        cursor.execute('''INSERT INTO triage_logs (timestamp, patient_name, age, sex, priority, zone, score_details, staff_id, vitals_json, symptoms_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                       (datetime.now().isoformat(), patient.name, patient.age, patient.sex, res_priority, res_zone, ", ".join(detected_interactions), patient.staff_id, vitals_data, ";".join(patient.symptoms)))
        
        # High-priority notification
        if res_zone <= 2:
            msg = f"ALERT: Patient {patient.name} assigned to {res_priority} (Zone {res_zone})"
            cursor.execute("INSERT INTO notifications (timestamp, message) VALUES (?, ?)", (datetime.now().isoformat(), msg))
            
        conn.commit(); conn.close()
    except Exception as e: print(f"DB Error: {e}")

    return {
        "priority": res_priority, 
        "zone": res_zone, 
        "color_code": color_map[res_zone], 
        "reasoning": coupling_reasons, 
        "detected_interactions": detected_interactions,
        "next_steps": next_steps
    }

@app.get("/census")
def get_census():
    """Returns patients currently in the system (active)."""
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute('''SELECT patient_name, zone, priority, timestamp, vitals_json FROM triage_logs 
                      WHERE is_active = 1 
                      ORDER BY zone ASC, timestamp DESC''')
    rows = cursor.fetchall(); conn.close()
    
    census = {1: [], 2: [], 3: [], 4: [], 5: []}
    for r in rows:
        census[r[1]].append({"name": r[0], "priority": r[2], "time": r[3], "vitals": r[4]})
    return census

@app.post("/discharge/{name}")
def discharge_patient(name: str):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute("UPDATE triage_logs SET is_active = 0 WHERE patient_name = ?", (name,))
    conn.commit(); conn.close()
    return {"status": "success", "message": f"Patient {name} discharged"}

@app.get("/logs")
def get_logs():
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute('''SELECT l.id, l.timestamp, l.priority, u.name, u.role, l.score_details, l.patient_name, l.zone FROM triage_logs l LEFT JOIN users u ON l.staff_id = u.id ORDER BY l.id DESC LIMIT 50''')
    logs = cursor.fetchall(); conn.close()
    return [{"id": r[0], "time": r[1], "priority": r[2], "staff": r[3] or "System", "role": r[4] or "N/A", "notes": r[5], "patient": r[6], "zone": r[7]} for r in logs]
