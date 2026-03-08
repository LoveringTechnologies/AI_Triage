# 🏥 AI Emergency Triage System (v2.0.0)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![React Native](https://img.shields.io/badge/Mobile-React_Native-61DAFB.svg)](https://reactnative.dev/)

An advanced, multi-platform clinical triage suite that integrates **Machine Learning** with a **High-Fidelity Expert Logic Layer**. This system is designed to assist medical professionals in rapidly and accurately categorizing patients using a sophisticated 5-Zone Clinical Model.

---

## 🚀 Core Innovation: The Hybrid Intelligence Engine

Unlike standard ML models that act as a "black box," this system employs a **Hybrid Clinical Intelligence Engine** that provides a "Safety Floor" for patient care.

### 1. Layer 1: Machine Learning Core (Random Forest)
Trained on a high-fidelity dataset of over 50,000 clinical samples, the model analyzes non-linear relationships between 15+ variables including vitals, demographics, and medical history.

### 2. Layer 2: Physiological Coupling (Expert Rules)
Hard-coded clinical protocols ensure that critical patterns are never missed:
- **Sepsis Protocol**: Triggers on Fever + Tachycardia + Tachypnea + Hypotension.
- **Stroke (CVA) Alert**: Monitors "FAST" symptoms (Facial drooping, Speech, etc.) coupled with hypertensive crises.
- **Shock Index (SI)**: Calculates `HR / SBP` to detect hidden hypoperfusion before blood pressure crashes.
- **Cardiac Event Logic**: High-sensitivity detection for Chest Pain + Vital Instability.
- **Hypoglycemia Logic**: Critical alerts for blood glucose < 70 mg/dL.

### 3. Layer 3: Weighted Clinical Overlay
Specific high-risk symptoms (e.g., Confusion, Limb Numbness) and pre-existing conditions (e.g., Heart Disease, COPD) apply mathematical "boosts" to the final Zone assignment.

---

## 📊 The 5-Zone Clinical Model

The system maps all inputs to a globally recognized 5-tier priority system:

| Zone | Priority | Color | Clinical Action |
| :--- | :--- | :--- | :--- |
| **Zone 1** | **Resuscitation** | 🔴 Red | Immediate life-saving intervention |
| **Zone 2** | **Emergent** | 🟠 Orange | Evaluation within 15 minutes |
| **Zone 3** | **Urgent** | 🟡 Yellow | Evaluation within 30-60 minutes |
| **Zone 4** | **Less-Urgent** | 🔵 Blue | Evaluation within 60-120 minutes |
| **Zone 5** | **Non-Urgent** | 🟢 Green | Routine care / Discharge |

---

## 🛠 Tech Stack

- **Backend**: FastAPI (Python) with SQLite for high-concurrency log management.
- **ML Engine**: Scikit-Learn (Random Forest) with Tfidf-based symptom processing.
- **Mobile**: React Native / Expo (Cross-platform iOS & Android).
- **Dashboard**: Streamlit (Data visualization and staff oversight).

---

## 👥 Meet the Team

This project was engineered and developed by a dedicated team of innovators:

- **Hunter Lovering** - *Lead Architect & Full-Stack Developer*
- **Mike Shmelev** - *Lead Data Scientist & ML Engineering*
- **Kyle K.** - *Clinical Logic & Systems Integration*

---

## 🔧 Installation & Setup

### 1. Environment Setup
Create a virtual environment and install dependencies:
```bash
python -m venv "AI Triage System"
".\AI Triage System\Scripts\pip" install pandas numpy scikit-learn fastapi uvicorn pydantic
```

### 2. Generate Training Data
```bash
python generate_clinical_data.py
```

### 3. Start the API
```bash
uvicorn triage_api:app --host 0.0.0.0 --port 8000
```

### 4. Launch Mobile App
```bash
cd TriageMobile
npm install
npx expo start
```

---

## ⚖️ Disclaimer
*This system is a clinical decision support tool and is NOT intended to replace the clinical judgment of a qualified healthcare professional. All Zone assignments must be verified by licensed medical staff.*
