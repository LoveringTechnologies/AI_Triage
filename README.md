# 🏥 AI Emergency Triage System (v2.1.0)

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

### 4. Layer 4: Age-Stratified Logic (CTAS vs PaedCTAS)
Physiology is adjusted for age groups:
- **Adult (18+)**: Standard CTAS vital thresholds.
- **Teen (12-18)**: Paediatric CTAS modifiers for heart rate and respiratory rate normalization.

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

## 📱 Mobile App Key Features

- **Live ER Census**: A real-time dashboard showing all active patients sorted by priority.
- **Next-Action Protocols**: Instant clinical checklists (e.g., *Stat Labs*, *EKG*, *Fluids*) based on detected conditions.
- **Patient Discharge**: One-tap "Clear" functionality to manage active zone volume.
- **Professional Date Selector**: High-fidelity DOB selection with automatic age calculation.
- **Android Support**: Full hardware "Back" button integration for all modals and pickers.
- **Camera Scan (v2.1 Alpha)**: Infrastructure for future AI physical assessment module.

---

## 🔧 Installation & Setup

### 1. Python Dependencies
The backend requires Python 3.9+ and the following libraries:
- `fastapi` & `uvicorn`: Web API framework and server.
- `pandas` & `numpy`: Data processing and numerical analysis.
- `scikit-learn`: Machine Learning (Random Forest) implementation.
- `pydantic`: Data validation and settings management.
- `sqlite3`: Local database management (Standard Library).

### 2. Environment Setup
```bash
python -m venv "AI Triage System"
& ".\AI Triage System\Scripts\pip" install pandas numpy scikit-learn fastapi uvicorn pydantic
```

### 3. Generate Training Data
```bash
& ".\AI Triage System\Scripts\python" generate_clinical_data.py
```

### 4. Start the API
```bash
& ".\AI Triage System\Scripts\python" -m uvicorn triage_api:app --host 0.0.0.0 --port 8000
```

### 5. Launch Mobile App (Expo)
```bash
cd TriageMobile
npm install
npx expo start
```

---

## 👥 Meet the Team

This project was engineered and developed by a dedicated team of innovators:

- **Hunter Lovering** - *Lead Architect & Full-Stack Developer*
- **Mike Shmelev** - *Lead Data Scientist & ML Engineering*
- **Kyle K.** - *Clinical Logic & Systems Integration*

---

## ⚖️ Disclaimer
*This system is a clinical decision support tool and is NOT intended to replace the clinical judgment of a qualified healthcare professional. All Zone assignments must be verified by licensed medical staff.*
