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
        priority TEXT, zone INTEGER, score_details TEXT, staff_id TEXT, vitals_json TEXT, symptoms_json TEXT)''')
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

HIGH_RISK_INTERACTIONS = {
    ("Asthma", "Wheezing"): 1.5, ("Asthma", "Shortness of breath"): 2.0,
    ("COPD", "Shortness of breath"): 2.0, ("Heart Disease", "Chest pain"): 2.5,
    ("Type 2 Diabetes", "Confusion"): 2.0, ("Immunosuppression", "Fever"): 2.0
}

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

@app.on_event("startup")
def startup():
    global model_pipeline, symptoms_list, conditions_list
    init_db()
    df = pd.read_csv('Model Training Data/ai_triage_balanced_dataset.csv')
    df['pre_existing_conditions'] = df['pre_existing_conditions'].fillna('None')
    df['combined_text'] = df['pre_existing_conditions'] + " " + df['symptoms']
    df['sex_encoded'] = df['sex'].map({'M': 0, 'F': 1})
    df['target'] = df['triage_priority'].map({'Non-urgent': 0, 'Urgent': 1, 'Emergency': 2, 'Immediate': 3})
    numeric_features = ['age', 'heart_rate', 'systolic_bp', 'diastolic_bp', 'respiratory_rate', 'spo2', 'temperature_c', 'blood_glucose', 'pain_score']
    X = df[numeric_features + ['sex_encoded', 'combined_text']]
    y = df['target']
    preprocessor = ColumnTransformer([('num', 'passthrough', numeric_features + ['sex_encoded']),('text', TfidfVectorizer(max_features=500), 'combined_text')])
    model_pipeline = Pipeline([('preprocessor', preprocessor),('classifier', RandomForestClassifier(n_estimators=100, random_state=42))])
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
    sex_enc = 0 if patient.sex == 'M' else 1
    combined_text = f"{';'.join(patient.pre_existing_conditions)} {';'.join(patient.symptoms)} {patient.current_medications}"
    input_df = pd.DataFrame([{'age': patient.age, 'heart_rate': patient.heart_rate, 'systolic_bp': patient.systolic_bp, 'diastolic_bp': patient.diastolic_bp, 'respiratory_rate': patient.respiratory_rate, 'spo2': patient.spo2, 'temperature_c': patient.temperature_c, 'blood_glucose': patient.blood_glucose, 'pain_score': patient.pain_score, 'sex_encoded': sex_enc, 'combined_text': combined_text}])
    probs = model_pipeline.predict_proba(input_df)[0]
    priority_idx = np.argmax(probs)
    
    weight_boost = patient.manual_boost
    detected_interactions = []
    if patient.manual_boost != 0: detected_interactions.append(f"Clinical Override: {patient.manual_boost:+}")
    if patient.pain_location == "Head & Spine" and patient.pain_score >= 7:
        weight_boost += 1.0; detected_interactions.append(f"Severe {patient.pain_location} Pain")
    
    final_priority_idx = int(min(3, priority_idx + np.floor(weight_boost)))
    zone_map = {3: 1, 2: 2, 1: 3, 0: 4}
    priority_map = {3: 'Resuscitation', 2: 'Emergent', 1: 'Urgent', 0: 'Less-Urgent'}
    res_zone = zone_map[final_priority_idx]
    res_priority = priority_map[final_priority_idx]
    if final_priority_idx == 0 and patient.pain_score < 3:
        res_zone = 5; res_priority = "Non-Urgent"

    color_map = {1: 'red', 2: 'orange', 3: '#f1c40f', 4: 'blue', 5: 'green'}

    try:
        conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
        vitals_data = f"HR:{patient.heart_rate}, BP:{patient.systolic_bp}/{patient.diastolic_bp}"
        cursor.execute('''INSERT INTO triage_logs (timestamp, patient_name, age, sex, priority, zone, score_details, staff_id, vitals_json, symptoms_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (datetime.now().isoformat(), patient.name, patient.age, patient.sex, res_priority, res_zone, ", ".join(detected_interactions), patient.staff_id, vitals_data, ";".join(patient.symptoms)))
        msg = f"Patient {patient.name} assigned Zone {res_zone}"
        cursor.execute("INSERT INTO notifications (timestamp, message) VALUES (?, ?)", (datetime.now().isoformat(), msg))
        conn.commit(); conn.close()
    except Exception as e: print(f"DB Error: {e}")

    return {"priority": res_priority, "zone": res_zone, "color_code": color_map[res_zone], "reasoning": [], "detected_interactions": detected_interactions}

@app.get("/logs")
def get_logs():
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    cursor.execute('''SELECT l.id, l.timestamp, l.priority, u.name, u.role, l.score_details, l.patient_name, l.zone FROM triage_logs l LEFT JOIN users u ON l.staff_id = u.id ORDER BY l.id DESC LIMIT 50''')
    logs = cursor.fetchall(); conn.close()
    return [{"id": r[0], "time": r[1], "priority": r[2], "staff": r[3] or "System", "role": r[4] or "N/A", "notes": r[5], "patient": r[6], "zone": r[7]} for r in logs]
