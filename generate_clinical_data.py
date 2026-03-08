import pandas as pd
import numpy as np
import uuid

def generate_realistic_data(n_samples=50000):
    data = []
    
    symptoms_pool = ['Cough', 'Fever', 'Shortness of breath', 'Chest pain', 'Abdominal pain', 
                     'Headache', 'Dizziness', 'Nausea', 'Vomiting', 'Rash', 'Confusion', 
                     'Weakness', 'Limb numbness', 'Sore throat', 'Runny nose', 'Wheezing']
    
    conditions_pool = ['Hypertension', 'Diabetes', 'Asthma', 'COPD', 'Heart Disease', 
                       'Chronic Kidney Disease', 'Obesity', 'Cancer', 'Immunosuppression']

    for _ in range(n_samples):
        # Baseline Vitals
        age = np.random.randint(12, 95) # Focusing on 12+ for this model update
        sex = np.random.choice(['M', 'F'])
        
        # Age-stratified Baseline ranges
        if age < 18:
            # Teen ranges (12-18)
            hr_base, hr_std = 80, 12
            sbp_base, sbp_std = 115, 10
            rr_base, rr_std = 16, 2
        else:
            # Adult ranges (18+)
            hr_base, hr_std = 72, 10
            sbp_base, sbp_std = 122, 15
            rr_base, rr_std = 14, 2

        hr = np.random.normal(hr_base, hr_std)
        sbp = np.random.normal(sbp_base, sbp_std)
        dbp = np.random.normal(80, 10)
        rr = np.random.normal(rr_base, rr_std)
        spo2 = np.random.normal(98, 1.5)
        temp = np.random.normal(36.6, 0.4)
        glucose = np.random.normal(95, 15)
        pain = np.random.randint(0, 4)
        
        symptoms = np.random.choice(symptoms_pool, size=np.random.randint(1, 4), replace=False).tolist()
        conditions = np.random.choice(conditions_pool, size=np.random.randint(0, 3), replace=False).tolist()
        
        # --- PHYSIOLOGY COUPLING & CRITICAL SCENARIOS ---
        scenario = np.random.choice(['Normal', 'Sepsis', 'MI', 'RespFailure', 'Fever', 'Hypoglycemia', 'Stroke', 'Shock'], 
                                    p=[0.65, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05])
        
        priority_score = 5 # Default Zone 5 (Green)
        
        if scenario == 'Sepsis':
            temp = np.random.uniform(38.5, 40.5)
            hr = np.random.uniform(105, 140)
            rr = np.random.uniform(22, 35)
            sbp = np.random.uniform(70, 95)
            if 'Fever' not in symptoms: symptoms.append('Fever')
            if 'Confusion' not in symptoms: symptoms.append('Confusion')
            priority_score = 1
            
        elif scenario == 'MI':
            hr = np.random.uniform(110, 150)
            sbp = np.random.uniform(140, 190)
            pain = np.random.randint(7, 11)
            if 'Chest pain' not in symptoms: symptoms.append('Chest pain')
            priority_score = 1
            
        elif scenario == 'RespFailure':
            spo2 = np.random.uniform(75, 89)
            rr = np.random.uniform(28, 45)
            if 'Shortness of breath' not in symptoms: symptoms.append('Shortness of breath')
            priority_score = 2
            
        elif scenario == 'Fever':
            temp = np.random.uniform(38.0, 39.5)
            hr += 10 # Heart rate spike with fever
            if 'Fever' not in symptoms: symptoms.append('Fever')
            priority_score = 3
            
        elif scenario == 'Hypoglycemia':
            glucose = np.random.uniform(30, 55)
            hr = np.random.uniform(100, 120)
            if 'Dizziness' not in symptoms: symptoms.append('Dizziness')
            if 'Confusion' not in symptoms: symptoms.append('Confusion')
            priority_score = 2
            
        elif scenario == 'Stroke':
            sbp = np.random.uniform(160, 220)
            dbp = np.random.uniform(100, 130)
            if 'Slurred speech' not in symptoms_pool: symptoms.append('Slurred speech') # Inject if missing
            if 'Limb numbness' not in symptoms: symptoms.append('Limb numbness')
            if 'Confusion' not in symptoms: symptoms.append('Confusion')
            priority_score = 1
            
        elif scenario == 'Shock':
            # High Shock Index: HR > SBP
            sbp = np.random.uniform(80, 100)
            hr = np.random.uniform(110, 140)
            rr = np.random.uniform(22, 30)
            priority_score = 1

        # Final Logic Adjustment based on vitals outside scenarios
        if spo2 < 92 or hr > 130 or sbp < 90 or sbp > 200 or temp > 40:
            priority_score = min(priority_score, 2)
        elif hr > 110 or rr > 24 or temp > 38.5 or pain > 7:
            priority_score = min(priority_score, 3)

        priority_map = {1: 'Zone 1 (Resuscitation)', 2: 'Zone 2 (Emergent)', 3: 'Zone 3 (Urgent)', 4: 'Zone 4 (Less-Urgent)', 5: 'Zone 5 (Non-Urgent)'}
        
        data.append({
            'patient_id': str(uuid.uuid4()),
            'age': age,
            'sex': sex,
            'heart_rate': round(hr, 1),
            'systolic_bp': round(sbp, 1),
            'diastolic_bp': round(dbp, 1),
            'respiratory_rate': round(rr, 1),
            'spo2': round(spo2, 1),
            'temperature_c': round(temp, 1),
            'blood_glucose': round(glucose, 1),
            'pain_score': pain,
            'pre_existing_conditions': ";".join(conditions) if conditions else "None",
            'symptoms': ";".join(symptoms),
            'triage_priority': priority_map[priority_score]
        })
        
    return pd.DataFrame(data)

if __name__ == "__main__":
    df = generate_realistic_data(50000)
    df.to_csv('Model Training Data/ai_triage_clinical_v2.csv', index=False)
    print("New clinical dataset generated: ai_triage_clinical_v2.csv")
