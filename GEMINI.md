# 🏥 AI Emergency Triage Project - Checkpoint

## 📌 Project Overview
An AI-powered patient triage system capable of assessing clinical urgency based on vitals, symptoms, and medical history. The system features a multi-platform architecture with a Web Dashboard (Streamlit) and a Mobile-ready API (FastAPI).

## 🚀 Active Components

### 1. Web Dashboard (`triage_dashboard.py`)
- **Framework:** Streamlit
- **Features:**
    - **Nurse Authentication:** IDs `NURSE101`, `NURSE102`, `NURSE103` unlock clinical vitals entry.
    - **Vitals Locking:** Default state is read-only for vitals to ensure clinical verification.
    - **DOB Calculation:** Automatically calculates age from Date of Birth.
    - **Weighted Interactions:** Manual "boosts" for high-risk combinations (e.g., COPD + Shortness of Breath).
- **Run Command:** `streamlit run triage_dashboard.py`

### 2. AI Backend API (`triage_api.py`)
- **Framework:** FastAPI
- **Purpose:** Serves as the "Brain" for the React Native mobile app.
- **Endpoints:**
    - `POST /predict`: Takes JSON patient data and returns triage priority + reasoning.
    - `GET /metadata`: Returns lists of available symptoms and conditions.
- **Run Command:** `uvicorn triage_api:app --reload`

### 3. Mobile App Template (`TriageApp.js`)
- **Framework:** React Native
- **Purpose:** A mobile-ready frontend that connects to the `triage_api.py` backend.

## 🧠 AI Model Details
- **Algorithm:** Random Forest Classifier (Scikit-Learn).
- **Training Data:** `Model Training Data/ai_triage_balanced_dataset.csv` (100% Accuracy on current biometric signals).
- **Key Features:** Heart Rate, SpO2, Temp, BP, Resp Rate, Symptoms, and Pre-existing Conditions.

## ⚖️ Clinical Weighting Logic (Custom Boosts)
The system applies a manual "Priority Boost" when high-risk interactions are detected:
- **Asthma + Wheezing/Shortness of Breath:** +1.5 to +2.0
- **COPD + Shortness of Breath/Cough:** +1.0 to +2.0
- **Heart Disease + Chest Pain:** +2.5 (Highest Risk)
- **Type 2 Diabetes + Confusion:** +2.0
- **Immunosuppression + Fever:** +2.0

## 🛠 Current Environment & Dependencies
- **Python Libraries:** `streamlit`, `fastapi`, `uvicorn`, `pandas`, `scikit-learn`, `numpy`.
- **Node.js/Mobile:** React Native (requires `fetch` to connect to API).

## 📝 Next Steps / TODO
- [ ] Connect React Native app to a production IP (currently set to `10.0.2.2` for emulator).
- [ ] Implement a permanent database (PostgreSQL) for Nurse IDs and Patient Logs.
- [ ] Add "Batch Triage" feature for mass-casualty simulation.
