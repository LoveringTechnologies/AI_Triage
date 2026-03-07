from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
from typing import List, Optional

app = FastAPI(title="AI Triage API", version="1.0")

# --- Global Variables for Model ---
model_pipeline = None
symptoms_list = []
conditions_list = []

# --- Interaction Weights ---
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

# --- Data Models ---
class PatientData(BaseModel):
    age: int
    sex: str  # "M" or "F"
    heart_rate: float
    systolic_bp: float
    diastolic_bp: float
    respiratory_rate: float
    spo2: float
    temperature_c: float
    blood_glucose: float
    pain_score: int
    pre_existing_conditions: List[str]
    symptoms: List[str]
    current_medications: str = "None"

class TriageResponse(BaseModel):
    priority: str  # "Non-urgent", "Urgent", "Emergency", "Immediate"
    color_code: str # "green", "blue", "orange", "red"
    reasoning: List[str]
    detected_interactions: List[str]

# --- Startup: Load & Train Model ---
@app.on_event("startup")
def load_model():
    global model_pipeline, symptoms_list, conditions_list
    print("Loading and training model...")
    
    # Load Data
    df = pd.read_csv('Model Training Data/ai_triage_balanced_dataset.csv')
    df['pre_existing_conditions'] = df['pre_existing_conditions'].fillna('None')
    df['current_medications'] = df['current_medications'].fillna('None')
    df['combined_text'] = df['pre_existing_conditions'] + " " + df['symptoms'] + " " + df['current_medications']
    df['sex_encoded'] = df['sex'].map({'M': 0, 'F': 1})
    
    # Target Mapping
    inv_priority_map = {'Non-urgent': 0, 'Urgent': 1, 'Emergency': 2, 'Immediate': 3}
    df['target'] = df['triage_priority'].map(inv_priority_map)

    # Features
    numeric_features = ['age', 'heart_rate', 'systolic_bp', 'diastolic_bp', 'respiratory_rate', 'spo2', 'temperature_c', 'blood_glucose', 'pain_score']
    X = df[numeric_features + ['sex_encoded', 'combined_text']]
    y = df['target']

    # Pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', 'passthrough', numeric_features + ['sex_encoded']),
            ('text', TfidfVectorizer(max_features=500), 'combined_text')
        ]
    )

    model_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
    ])

    model_pipeline.fit(X, y)
    
    # Metadata
    symptoms_list = sorted(list(set(df['symptoms'].str.split(';').explode().unique())))
    conditions_list = sorted(list(set(df['pre_existing_conditions'].str.split(';').explode().unique())))
    print("Model ready!")

# --- API Endpoints ---

@app.get("/")
def home():
    return {"status": "online", "service": "AI Triage API"}

@app.get("/metadata")
def get_metadata():
    """Return available symptoms and conditions for UI dropdowns"""
    return {
        "symptoms": symptoms_list,
        "conditions": [c for c in conditions_list if str(c) != 'nan']
    }

@app.post("/predict", response_model=TriageResponse)
def predict_triage(patient: PatientData):
    if not model_pipeline:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    # 1. Prepare Input for Model
    sex_enc = 0 if patient.sex == 'M' else 1
    combined_text = f"{';'.join(patient.pre_existing_conditions)} {';'.join(patient.symptoms)} {patient.current_medications}"
    
    input_df = pd.DataFrame([{
        'age': patient.age,
        'heart_rate': patient.heart_rate,
        'systolic_bp': patient.systolic_bp,
        'diastolic_bp': patient.diastolic_bp,
        'respiratory_rate': patient.respiratory_rate,
        'spo2': patient.spo2,
        'temperature_c': patient.temperature_c,
        'blood_glucose': patient.blood_glucose,
        'pain_score': patient.pain_score,
        'sex_encoded': sex_enc,
        'combined_text': combined_text
    }])
    
    # 2. AI Prediction
    probs = model_pipeline.predict_proba(input_df)[0]
    priority_idx = np.argmax(probs)
    
    # 3. Apply Weighting Logic
    weight_boost = 0.0
    detected_interactions = []
    
    for (cond, sym), boost in HIGH_RISK_INTERACTIONS.items():
        if cond in patient.pre_existing_conditions and sym in patient.symptoms:
            weight_boost += boost
            detected_interactions.append(f"{sym} + {cond} (+{boost} priority)")
            
    final_priority_idx = int(min(3, priority_idx + np.floor(weight_boost)))
    
    # 4. Format Response
    priority_map = {0: 'Non-urgent', 1: 'Urgent', 2: 'Emergency', 3: 'Immediate'}
    color_map = {0: 'green', 1: 'blue', 2: 'orange', 3: 'red'}
    
    result_priority = priority_map[final_priority_idx]
    
    # Reasoning
    reasons = []
    if patient.heart_rate > 120 or patient.heart_rate < 50: reasons.append(f"Abnormal HR: {patient.heart_rate}")
    if patient.spo2 < 92: reasons.append(f"Low SpO2: {patient.spo2}%")
    if patient.systolic_bp > 160: reasons.append(f"High BP: {patient.systolic_bp}")
    if patient.temperature_c > 38.5: reasons.append(f"High Temp: {patient.temperature_c}C")
    
    return {
        "priority": result_priority,
        "color_code": color_map[final_priority_idx],
        "reasoning": reasons,
        "detected_interactions": detected_interactions
    }
