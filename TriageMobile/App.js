import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TextInput, ScrollView, TouchableOpacity, Alert, Switch } from 'react-native';

export default function App() {
  // --- State for Patient Data ---
  const [age, setAge] = useState('45');
  const [sex, setSex] = useState('M');
  const [hr, setHr] = useState('75');
  const [spo2, setSpo2] = useState('98');
  const [sbp, setSbp] = useState('120');
  const [dbp, setDbp] = useState('80');
  const [temp, setTemp] = useState('37.0');
  const [pain, setPain] = useState('0');
  
  // Symptoms & Conditions (Simplified as text inputs for demo)
  const [conditions, setConditions] = useState(''); // Comma separated
  const [symptoms, setSymptoms] = useState('');     // Comma separated
  
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // --- API Call to Python Backend ---
  const runTriage = async () => {
    setLoading(true);
    setResult(null);

    // REPLACE 'x.x.x.x' with your computer's IP address if running on a real phone.
    // '10.0.2.2' is the special alias for localhost in Android Emulator.
    const API_URL = 'http://100.70.12.89:8000/predict';

    try {
      const payload = {
        age: parseInt(age),
        sex: sex,
        heart_rate: parseFloat(hr),
        systolic_bp: parseFloat(sbp),
        diastolic_bp: parseFloat(dbp),
        respiratory_rate: 16, // Default for now
        spo2: parseFloat(spo2),
        temperature_c: parseFloat(temp),
        blood_glucose: 100, // Default for now
        pain_score: parseInt(pain),
        pre_existing_conditions: conditions.split(',').map(s => s.trim()).filter(s => s),
        symptoms: symptoms.split(',').map(s => s.trim()).filter(s => s),
        current_medications: "None"
      };

      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      setResult(data);
      
    } catch (error) {
      Alert.alert("Connection Error", "Could not connect to AI Server. Is uvicorn running?");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.header}>🏥 AI Triage Mobile</Text>
      
      {/* --- Vitals Section --- */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Patient Vitals</Text>
        
        <View style={styles.row}>
          <View style={styles.inputGroup}>
            <Text>Age</Text>
            <TextInput style={styles.input} keyboardType="numeric" value={age} onChangeText={setAge} />
          </View>
          <View style={styles.inputGroup}>
            <Text>Sex (M/F)</Text>
            <TextInput style={styles.input} value={sex} onChangeText={setSex} />
          </View>
        </View>

        <View style={styles.row}>
          <View style={styles.inputGroup}>
            <Text>HR (BPM)</Text>
            <TextInput style={styles.input} keyboardType="numeric" value={hr} onChangeText={setHr} />
          </View>
          <View style={styles.inputGroup}>
            <Text>SpO2 (%)</Text>
            <TextInput style={styles.input} keyboardType="numeric" value={spo2} onChangeText={setSpo2} />
          </View>
        </View>

        <View style={styles.row}>
          <View style={styles.inputGroup}>
            <Text>Systolic BP</Text>
            <TextInput style={styles.input} keyboardType="numeric" value={sbp} onChangeText={setSbp} />
          </View>
          <View style={styles.inputGroup}>
            <Text>Temp (°C)</Text>
            <TextInput style={styles.input} keyboardType="numeric" value={temp} onChangeText={setTemp} />
          </View>
        </View>
      </View>

      {/* --- Context Section --- */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Clinical Context</Text>
        <Text style={styles.label}>Symptoms (comma separated)</Text>
        <TextInput 
          style={styles.textArea} 
          placeholder="e.g. Chest pain, Shortness of breath" 
          value={symptoms} 
          onChangeText={setSymptoms} 
        />
        
        <Text style={styles.label}>Conditions (comma separated)</Text>
        <TextInput 
          style={styles.textArea} 
          placeholder="e.g. Heart Disease, Asthma" 
          value={conditions} 
          onChangeText={setConditions} 
        />
      </View>

      <TouchableOpacity style={styles.button} onPress={runTriage} disabled={loading}>
        <Text style={styles.buttonText}>{loading ? "Analyzing..." : "RUN TRIAGE"}</Text>
      </TouchableOpacity>

      {/* --- Results Section --- */}
      {result && (
        <View style={[styles.resultCard, { borderColor: result.color_code }]}>
          <Text style={[styles.resultTitle, { color: result.color_code }]}>
            {result.priority.toUpperCase()}
          </Text>
          
          {result.reasoning.map((r, i) => (
            <Text key={i} style={styles.reason}>• {r}</Text>
          ))}
          
          {result.detected_interactions.map((int, i) => (
            <Text key={i} style={styles.interaction}>⚠️ {int}</Text>
          ))}
          
          {result.reasoning.length === 0 && result.detected_interactions.length === 0 && (
            <Text>Vitals are stable. Triage based on symptoms.</Text>
          )}
        </View>
      )}

      <View style={{height: 50}} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: '#f5f5f5', marginTop: 30 },
  header: { fontSize: 28, fontWeight: 'bold', textAlign: 'center', marginBottom: 20, color: '#333' },
  section: { backgroundColor: 'white', padding: 15, borderRadius: 10, marginBottom: 15, elevation: 2 },
  sectionTitle: { fontSize: 18, fontWeight: '600', marginBottom: 10, color: '#444' },
  row: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 10 },
  inputGroup: { width: '45%' },
  input: { borderWidth: 1, borderColor: '#ddd', padding: 10, borderRadius: 5, fontSize: 16, marginTop: 5 },
  label: { marginBottom: 5, marginTop: 10, color: '#666' },
  textArea: { borderWidth: 1, borderColor: '#ddd', padding: 10, borderRadius: 5, fontSize: 16, height: 60 },
  button: { backgroundColor: '#007AFF', padding: 15, borderRadius: 10, alignItems: 'center', marginTop: 10 },
  buttonText: { color: 'white', fontSize: 18, fontWeight: 'bold' },
  resultCard: { marginTop: 20, padding: 20, backgroundColor: 'white', borderRadius: 10, borderWidth: 3, elevation: 4 },
  resultTitle: { fontSize: 24, fontWeight: 'bold', textAlign: 'center', marginBottom: 10 },
  reason: { fontSize: 16, marginBottom: 5, color: '#444' },
  interaction: { fontSize: 16, marginBottom: 5, color: '#d9534f', fontWeight: 'bold' }
});
