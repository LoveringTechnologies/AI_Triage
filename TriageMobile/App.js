import React, { useState, useEffect, useRef } from 'react';
import { 
  StyleSheet, Text, View, TextInput, ScrollView, 
  TouchableOpacity, Alert, ActivityIndicator, Modal, FlatList, Animated, Dimensions, useWindowDimensions
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// --- Components ---
const DatePicker = ({ label, value, onSelect }) => {
  const [modalVisible, setModalVisible] = useState(false);
  const years = [];
  const currentYear = new Date().getFullYear();
  for (let i = currentYear; i >= currentYear - 100; i--) years.push(i.toString());

  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const days = Array.from({ length: 31 }, (_, i) => (i + 1).toString());

  const [selYear, setSelYear] = useState(value ? value.split('-')[0] : currentYear.toString());
  const [selMonth, setSelMonth] = useState(value ? months[parseInt(value.split('-')[1]) - 1] : "Jan");
  const [selDay, setSelDay] = useState(value ? parseInt(value.split('-')[2]).toString() : "1");

  const confirmDate = () => {
    const mIdx = months.indexOf(selMonth) + 1;
    const formatted = `${selYear}-${mIdx.toString().padStart(2, '0')}-${selDay.padStart(2, '0')}`;
    onSelect(formatted);
    setModalVisible(false);
  };

  return (
    <View style={styles.inputGroup}>
      <Text style={styles.label}>{label}</Text>
      <TouchableOpacity style={styles.input} onPress={() => setModalVisible(true)}>
        <Text style={[styles.inputText, !value && styles.placeholderTextMain]}>{value || "Select DOB"}</Text>
      </TouchableOpacity>
      <Modal visible={modalVisible} animationType="slide" transparent={true} onRequestClose={() => setModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContentSmall}>
            <Text style={styles.modalHeader}>Select Date of Birth</Text>
            <View style={{ flexDirection: 'row', justifyContent: 'space-around', height: 200 }}>
              <FlatList data={years} keyExtractor={i => i} renderItem={({ item }) => (
                <TouchableOpacity onPress={() => setSelYear(item)} style={[styles.datePart, selYear === item && styles.itemSelected]}>
                  <Text style={selYear === item ? { fontWeight: 'bold', color: '#3498db' } : {}}>{item}</Text>
                </TouchableOpacity>
              )} />
              <FlatList data={months} keyExtractor={i => i} renderItem={({ item }) => (
                <TouchableOpacity onPress={() => setSelMonth(item)} style={[styles.datePart, selMonth === item && styles.itemSelected]}>
                  <Text style={selMonth === item ? { fontWeight: 'bold', color: '#3498db' } : {}}>{item}</Text>
                </TouchableOpacity>
              )} />
              <FlatList data={days} keyExtractor={i => i} renderItem={({ item }) => (
                <TouchableOpacity onPress={() => setSelDay(item)} style={[styles.datePart, selDay === item && styles.itemSelected]}>
                  <Text style={selDay === item ? { fontWeight: 'bold', color: '#3498db' } : {}}>{item}</Text>
                </TouchableOpacity>
              )} />
            </View>
            <TouchableOpacity style={styles.closeButton} onPress={confirmDate}><Text style={styles.closeButtonText}>Confirm Date</Text></TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const Dropdown = ({ label, options, selectedValue, onSelect, style, disabled = false }) => {
  const [modalVisible, setModalVisible] = useState(false);
  const isSelected = selectedValue && selectedValue !== "";
  return (
    <View style={[styles.inputGroup, style, disabled && { opacity: 0.5 }]}>
      <Text style={styles.label}>{label}</Text>
      <TouchableOpacity style={styles.input} onPress={() => !disabled && setModalVisible(true)} disabled={disabled}>
        <Text style={[styles.inputText, !isSelected && styles.placeholderTextMain]}>{isSelected ? selectedValue : "<Select>"}</Text>
      </TouchableOpacity>
      <Modal visible={modalVisible} animationType="fade" transparent={true} onRequestClose={() => setModalVisible(false)}>
        <TouchableOpacity style={styles.modalOverlay} activeOpacity={1} onPress={() => setModalVisible(false)}>
          <View style={styles.modalContentSmall}>
            <Text style={styles.modalHeader}>{label}</Text>
            <ScrollView>
              {options.map((opt) => (
                <TouchableOpacity key={opt} style={[styles.itemRow, selectedValue === opt && styles.itemSelected]}
                  onPress={() => { onSelect(opt); setModalVisible(false); }}>
                  <Text style={selectedValue === opt ? styles.itemTextSelected : styles.itemText}>{opt}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        </TouchableOpacity>
      </Modal>
    </View>
  );
};

const MultiSelect = ({ label, items, selectedItems, onToggle }) => {
  const [modalVisible, setModalVisible] = useState(false);
  return (
    <View style={styles.inputGroupFull}>
      <Text style={styles.label}>{label}</Text>
      <TouchableOpacity style={styles.multiSelectTrigger} onPress={() => setModalVisible(true)}>
        <Text style={[styles.multiSelectText, selectedItems.length === 0 && styles.placeholderTextMain]}>{selectedItems.length > 0 ? `${selectedItems.length} selected` : `<Select ${label}>`}</Text>
      </TouchableOpacity>
      <Modal visible={modalVisible} animationType="slide" transparent={true} onRequestClose={() => setModalVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalHeader}>{label}</Text>
            <FlatList data={items} keyExtractor={(item) => item} renderItem={({ item }) => (
              <TouchableOpacity style={[styles.itemRow, selectedItems.includes(item) && styles.itemSelected]} onPress={() => onToggle(item)}>
                <Text style={selectedItems.includes(item) ? styles.itemTextSelected : styles.itemText}>{item}</Text>
              </TouchableOpacity>
            )} />
            <TouchableOpacity style={styles.closeButton} onPress={() => setModalVisible(false)}><Text style={styles.closeButtonText}>Done</Text></TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const CensusModal = ({ visible, data, onClose, onDischarge }) => {
  const renderZone = (zone, color) => (
    <View style={styles.censusZone}>
      <View style={[styles.zoneTag, { backgroundColor: color }]}><Text style={styles.zoneTagText}>ZONE {zone}</Text></View>
      {data[zone] && data[zone].length === 0 ? <Text style={styles.emptyZone}>No active patients</Text> : 
        data[zone]?.map((p, i) => (
          <View key={i} style={styles.censusPatient}>
            <View style={{flex: 1}}>
              <Text style={styles.censusName}>{p.name}</Text>
              <Text style={styles.censusVitals}>{p.vitals} | {p.priority}</Text>
            </View>
            <TouchableOpacity onPress={() => onDischarge(p.name)} style={styles.dischargeBtn}>
              <Ionicons name="checkmark-done-circle" size={24} color="#27ae60" />
              <Text style={styles.dischargeText}>Clear</Text>
            </TouchableOpacity>
          </View>
        ))
      }
    </View>
  );

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <View style={{ flex: 1, backgroundColor: '#f0f2f5', padding: 20, paddingTop: 50 }}>
        <View style={styles.row}>
          <Text style={styles.modalHeader}>Live ER Census</Text>
          <TouchableOpacity onPress={onClose}><Ionicons name="close-circle" size={32} color="#e74c3c" /></TouchableOpacity>
        </View>
        <ScrollView>
          {renderZone(1, 'red')}
          {renderZone(2, 'orange')}
          {renderZone(3, '#f1c40f')}
          {renderZone(4, 'blue')}
          {renderZone(5, 'green')}
        </ScrollView>
      </View>
    </Modal>
  );
};

export default function App() {
  const { width } = useWindowDimensions();
  const drawerWidth = width > 600 ? 300 : width * 0.75;

  const [staff, setStaff] = useState(null);
  const [empId, setEmpId] = useState('');
  const [isMenuVisible, setMenuVisible] = useState(false);
  const [isLogsVisible, setLogsVisible] = useState(false);
  const [isCensusVisible, setCensusVisible] = useState(false);
  const [logs, setLogs] = useState([]);
  const [census, setCensus] = useState({1:[], 2:[], 3:[], 4:[], 5:[]});
  
  // Patient Info
  const [patientName, setPatientName] = useState('');
  const [dob, setDob] = useState('');
  const [sex, setSex] = useState('');
  const [hr, setHr] = useState('');
  const [spo2, setSpo2] = useState('');
  const [sbp, setSbp] = useState('');
  const [dbp, setDbp] = useState('');
  const [rr, setRr] = useState('');
  const [temp, setTemp] = useState('');
  const [glucose, setGlucose] = useState('');
  const [pain, setPain] = useState('');
  const [painLocation, setPainLocation] = useState('');
  const [painSpecificArea, setPainSpecificArea] = useState('');
  const [selectedConditions, setSelectedConditions] = useState([]);
  const [selectedSymptoms, setSelectedSymptoms] = useState([]);
  const [meds, setMeds] = useState('');
  
  // Clinical Weighting
  const [manualBoost, setManualBoost] = useState('0.0');

  const [metadata, setMetadata] = useState({ symptoms: [], conditions: [] });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const API_BASE = 'http://67.58.209.30:8591'; 

  // Polling for notifications
  useEffect(() => {
    let interval;
    if (staff) {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`${API_BASE}/notifications/${staff.id}`);
          const notes = await res.json();
          if (notes.length > 0) {
            notes.forEach(n => {
              Alert.alert("🚨 Patient Alert", n.message);
            });
          }
        } catch (e) {}
      }, 10000);
    }
    return () => clearInterval(interval);
  }, [staff]);

  useEffect(() => { fetchMetadata(); }, []);
  
  const fetchMetadata = async () => {
    try {
      const response = await fetch(`${API_BASE}/metadata`);
      const data = await response.json();
      setMetadata(data);
    } catch (e) { console.log("Metadata failed", e); }
  };

  const handleLogin = async () => {
    try {
      const response = await fetch(`${API_BASE}/verify-staff/${empId}`);
      if (response.ok) {
        setStaff(await response.json());
        setEmpId(''); setMenuVisible(false);
      } else { Alert.alert("Denied", "Invalid ID"); }
    } catch (e) { Alert.alert("Error", "Server unreachable"); }
  };

  const handleDischarge = async (name) => {
    try {
      await fetch(`${API_BASE}/discharge/${name}`, { method: 'POST' });
      // Refresh Census
      const res = await fetch(`${API_BASE}/census`);
      setCensus(await res.json());
    } catch (e) { Alert.alert("Error", "Failed to clear patient"); }
  };

  const getCalculatedAge = () => {
    if (!dob || dob.length < 10) return "--";
    const birthDate = new Date(dob);
    const age = new Date().getFullYear() - birthDate.getFullYear();
    return Math.max(0, age);
  };

  const runTriage = async () => {
    if (!dob || !sex || !patientName) { Alert.alert("Missing Info", "Name, DOB, and Sex required."); return; }
    setLoading(true);
    try {
      const payload = {
        name: patientName, age: parseInt(getCalculatedAge()) || 0, sex, heart_rate: parseFloat(hr) || 70, 
        systolic_bp: parseFloat(sbp) || 120, diastolic_bp: parseFloat(dbp) || 80, 
        respiratory_rate: parseFloat(rr) || 16, spo2: parseFloat(spo2) || 98,
        temperature_c: parseFloat(temp) || 37.0, blood_glucose: parseFloat(glucose) || 100, 
        pain_score: parseInt(pain) || 0, pain_location: painLocation || "Body", 
        pain_specific_area: painSpecificArea || "General",
        pre_existing_conditions: selectedConditions, symptoms: selectedSymptoms, 
        current_medications: meds || "None", staff_id: staff ? staff.id : null,
        manual_boost: parseFloat(manualBoost) || 0.0
      };
      const response = await fetch(`${API_BASE}/predict`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
      });
      setResult(await response.json());
    } catch (e) { Alert.alert("Error", "Triage failed"); }
    finally { setLoading(false); }
  };

  return (
    <View style={{flex: 1, backgroundColor: '#f0f2f5'}}>
      <View style={styles.headerBar}>
        <TouchableOpacity onPress={() => setMenuVisible(true)}><Ionicons name="menu" size={32} color="#2c3e50" /></TouchableOpacity>
        <Text style={styles.headerTitle}>AI TRIAGE</Text>
        {staff && <View style={styles.onlineDot} />}
        {!staff && <View style={{width: 32}} />}
      </View>

      {/* --- SIDE MENU --- */}
      <Modal visible={isMenuVisible} animationType="none" transparent={true} onRequestClose={() => setMenuVisible(false)}>
        <View style={styles.drawerOverlay}>
          <Animated.View style={[styles.drawerContent, { width: drawerWidth }]}>
            <View style={styles.drawerHeader}>
              <Text style={styles.drawerTitle}>Staff Portal</Text>
              <TouchableOpacity onPress={() => setMenuVisible(false)}><Ionicons name="close" size={28} color="#fff" /></TouchableOpacity>
            </View>
            <View style={styles.drawerBody}>
              {!staff ? (
                <View>
                  <TextInput style={styles.drawerInput} placeholder="Staff ID" value={empId} onChangeText={setEmpId} secureTextEntry={true} />
                  <TouchableOpacity style={styles.drawerBtn} onPress={handleLogin}><Text style={styles.drawerBtnText}>Access Clinical Suite</Text></TouchableOpacity>
                </View>
              ) : (
                <View style={styles.nurseCard}>
                  <Ionicons name={staff.role === 'Doctor' ? "medical" : "person-circle"} size={60} color="#27ae60" />
                  <Text style={styles.nurseName}>{staff.name}</Text>
                  <Text style={styles.nurseDept}>{staff.role} | {staff.dept}</Text>
                  <TouchableOpacity style={styles.drawerMenuItem} onPress={() => { fetch(`${API_BASE}/logs`).then(r=>r.json()).then(d=>{setLogs(d);setLogsVisible(true);}); }}>
                    <Ionicons name="list" size={24} color="#3498db" /><Text style={styles.drawerMenuText}>Audit Logs</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.drawerMenuItem} onPress={() => { fetch(`${API_BASE}/census`).then(r=>r.json()).then(d=>{setCensus(d);setCensusVisible(true);}); }}>
                    <Ionicons name="grid" size={24} color="#f39c12" /><Text style={styles.drawerMenuText}>Live ER Census</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.drawerMenuItem} onPress={() => Alert.alert("Camera Module", "AI Physical Assessment (Stroke/Rash) coming in v2.1")}>
                    <Ionicons name="camera" size={24} color="#9b59b6" /><Text style={styles.drawerMenuText}>Camera Scan</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.drawerMenuItem} onPress={() => { setStaff(null); setMenuVisible(false); }}>
                    <Ionicons name="log-out" size={24} color="#e74c3c" /><Text style={[styles.drawerMenuText, {color: '#e74c3c'}]}>Logout</Text>
                  </TouchableOpacity>
                </View>
              )}
            </View>
          </Animated.View>
          <TouchableOpacity style={{flex: 1}} onPress={() => setMenuVisible(false)} />
        </View>
      </Modal>

      <ScrollView style={styles.container}>
        {/* 1. Patient Profile */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>👤 Patient Profile</Text>
          <TextInput style={styles.inputFull} placeholder="Patient Full Name" value={patientName} onChangeText={setPatientName} />
          <View style={styles.row}>
            <DatePicker label="Date of Birth" value={dob} onSelect={setDob} />
            <Dropdown label="Sex" options={["M", "F"]} selectedValue={sex} onSelect={setSex} />
          </View>
        </View>

        {/* 2. Patient History */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📋 Patient History</Text>
          <MultiSelect label="Symptoms" items={metadata.symptoms} selectedItems={selectedSymptoms} onToggle={(item) => setSelectedSymptoms(prev => prev.includes(item) ? prev.filter(i => i !== item) : [...prev, item])} />
          <MultiSelect label="Conditions" items={metadata.conditions} selectedItems={selectedConditions} onToggle={(item) => setSelectedConditions(prev => prev.includes(item) ? prev.filter(i => i !== item) : [...prev, item])} />
          <TextInput style={styles.inputFull} value={meds} onChangeText={setMeds} placeholder="Current Medications" />
        </View>

        <View style={styles.divider} />

        {/* 3. Clinical Section */}
        <View style={[styles.section, !staff && styles.lockedSection]}>
          <Text style={styles.sectionTitle}>🩺 Clinical Vitals</Text>
          {staff ? (
            <>
              <View style={styles.row}>
                <Dropdown label="Location" options={["None", "Head & Spine", "Body"]} selectedValue={painLocation} onSelect={(val) => {
                  setPainLocation(val);
                  if (val === "None") {
                    setPain("0");
                    setPainSpecificArea("None");
                  }
                }} />
                <Dropdown label="Specific Area" options={painLocation && painLocation !== "None" ? ["Chest", "Neck", "Head", "Abdomen", "Back", "Limbs"] : ["None"]} 
                  selectedValue={painSpecificArea} onSelect={setPainSpecificArea} disabled={!painLocation || painLocation === "None"} />
              </View>
              <View style={styles.row}>
                <View style={styles.inputGroup}><Text style={styles.label}>Pain (0-10)</Text><TextInput style={[styles.input, (painLocation === "None") && {backgroundColor: '#eee'}]} keyboardType="numeric" value={pain} onChangeText={setPain} editable={painLocation !== "None"} /></View>
                <View style={styles.inputGroup}><Text style={styles.label}>HR (BPM)</Text><TextInput style={styles.input} keyboardType="numeric" value={hr} onChangeText={setHr} /></View>
              </View>
              <View style={styles.row}>
                <View style={styles.inputGroup}><Text style={styles.label}>SpO2 (%)</Text><TextInput style={styles.input} keyboardType="numeric" value={spo2} onChangeText={setSpo2} /></View>
                <View style={styles.inputGroup}><Text style={styles.label}>Manual Weight</Text><TextInput style={styles.input} keyboardType="numeric" value={manualBoost} onChangeText={setManualBoost} placeholder="+1.0" /></View>
              </View>
            </>
          ) : (
            <View style={styles.lockedPlaceholder}><Text style={styles.placeholderText}>Staff Auth Required for Vitals.</Text></View>
          )}
        </View>

        <TouchableOpacity style={[styles.button, loading && styles.buttonDisabled]} onPress={runTriage} disabled={loading}>
          {loading ? <ActivityIndicator color="white" /> : <Text style={styles.buttonText}>GENERATE TRIAGE REPORT</Text>}
        </TouchableOpacity>

        {result && (
          <View style={[styles.resultCard, { borderColor: result.color_code }]}>
            <Text style={[styles.resultTitle, { color: result.color_code }]}>
              {staff ? result.priority.toUpperCase() : `ZONE ${result.zone}`}
            </Text>
            <Text style={styles.zoneInstruction}>Please move to Zone {result.zone}</Text>
            
            {result.detected_interactions.length > 0 && (
              <View style={styles.interactionList}>
                {result.detected_interactions.map((int, i) => <Text key={i} style={styles.interaction}>⚠️ {int}</Text>)}
              </View>
            )}

            {staff && result.next_steps && result.next_steps.length > 0 && (
              <View style={styles.protocolSection}>
                <Text style={styles.protocolTitle}>📋 CLINICAL PROTOCOL (NEXT STEPS)</Text>
                {result.next_steps.map((step, i) => (
                  <View key={i} style={styles.protocolRow}>
                    <Ionicons name="square-outline" size={20} color="#7f8c8d" />
                    <Text style={styles.protocolText}>{step}</Text>
                  </View>
                ))}
              </View>
            )}
          </View>
        )}
        <View style={{height: 50}} />
      </ScrollView>

      {/* Census Modal */}
      <CensusModal visible={isCensusVisible} data={census} onClose={() => setCensusVisible(false)} onDischarge={handleDischarge} />

      {/* Audit Logs Modal */}
      <Modal visible={isLogsVisible} animationType="slide" onRequestClose={() => setLogsVisible(false)}>
        <View style={{flex: 1, padding: 20, paddingTop: 50, backgroundColor: '#f8f9fa'}}>
          <TouchableOpacity onPress={() => setLogsVisible(false)}><Ionicons name="close-circle" size={32} color="#e74c3c" /></TouchableOpacity>
          <FlatList data={logs} keyExtractor={item => item.id.toString()} renderItem={({item}) => (
            <View style={styles.logCard}>
              <Text style={{fontWeight: 'bold'}}>{item.patient} -> Zone {item.zone}</Text>
              <Text style={{fontSize: 12, color: '#7f8c8d'}}>{item.time} | Verified by: {item.staff}</Text>
            </View>
          )} />
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  headerBar: { height: 100, backgroundColor: 'white', flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', paddingHorizontal: 20, paddingBottom: 15, elevation: 4 },
  headerTitle: { fontSize: 20, fontWeight: '900', color: '#2c3e50', letterSpacing: 2 },
  onlineDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: '#27ae60', marginBottom: 15 },
  drawerOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', flexDirection: 'row' },
  drawerContent: { height: '100%', backgroundColor: '#fdfdfd', elevation: 16 },
  drawerHeader: { height: 120, backgroundColor: '#2c3e50', justifyContent: 'space-between', padding: 20, paddingTop: 50, flexDirection: 'row' },
  drawerTitle: { color: 'white', fontSize: 18, fontWeight: 'bold' },
  drawerBody: { flex: 1, padding: 20 },
  drawerInput: { borderWidth: 1, borderColor: '#ecf0f1', padding: 12, borderRadius: 10, marginBottom: 15 },
  drawerBtn: { backgroundColor: '#3498db', padding: 15, borderRadius: 10, alignItems: 'center' },
  drawerBtnText: { color: 'white', fontWeight: 'bold' },
  nurseCard: { alignItems: 'center' },
  nurseName: { fontSize: 18, fontWeight: 'bold', marginTop: 10 },
  nurseDept: { fontSize: 12, color: '#7f8c8d', marginBottom: 20 },
  drawerMenuItem: { flexDirection: 'row', alignItems: 'center', paddingVertical: 15, borderTopWidth: 1, borderTopColor: '#f1f2f6', width: '100%' },
  drawerMenuText: { fontSize: 16, fontWeight: '600', marginLeft: 15 },
  container: { flex: 1, padding: 15 },
  section: { backgroundColor: 'white', padding: 18, borderRadius: 15, marginBottom: 15, elevation: 3 },
  sectionTitle: { fontSize: 17, fontWeight: '700', color: '#34495e', marginBottom: 10 },
  row: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12 },
  inputGroup: { width: '48%' },
  inputGroupFull: { width: '100%', marginBottom: 12 },
  label: { fontSize: 13, color: '#7f8c8d', marginBottom: 5 },
  input: { borderWidth: 1, borderColor: '#e1e8ed', padding: 13, borderRadius: 10, backgroundColor: '#f9f9f9' },
  inputFull: { borderWidth: 1, borderColor: '#e1e8ed', padding: 13, borderRadius: 10, backgroundColor: '#f9f9f9', marginBottom: 12 },
  inputText: { fontSize: 16 },
  placeholderTextMain: { color: '#bdc3c7' },
  divider: { height: 1, backgroundColor: '#dcdde1', marginVertical: 15 },
  lockedSection: { backgroundColor: '#f8f9fa', borderStyle: 'dashed', borderWidth: 1, borderColor: '#bdc3c7' },
  lockedPlaceholder: { paddingVertical: 15, alignItems: 'center' },
  placeholderText: { color: '#95a5a6' },
  multiSelectTrigger: { borderWidth: 1, borderColor: '#e1e8ed', padding: 13, borderRadius: 10, backgroundColor: '#f9f9f9' },
  multiSelectText: { color: '#2c3e50' },
  button: { backgroundColor: '#3498db', padding: 20, borderRadius: 15, alignItems: 'center' },
  buttonText: { color: 'white', fontSize: 16, fontWeight: '800' },
  resultCard: { marginTop: 25, padding: 22, backgroundColor: 'white', borderRadius: 20, borderWidth: 6 },
  resultTitle: { fontSize: 26, fontWeight: '900', textAlign: 'center' },
  zoneInstruction: { textAlign: 'center', fontSize: 18, marginVertical: 10, fontWeight: 'bold' },
  interactionList: { marginTop: 10, marginBottom: 15 },
  interaction: { color: '#e74c3c', fontWeight: 'bold', marginTop: 5, textAlign: 'center' },
  protocolSection: { borderTopWidth: 1, borderTopColor: '#f1f2f6', paddingTop: 15, marginTop: 10 },
  protocolTitle: { fontSize: 14, fontWeight: '800', color: '#2c3e50', marginBottom: 10 },
  protocolRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  protocolText: { fontSize: 14, color: '#34495e', marginLeft: 10, fontWeight: '600' },
  logCard: { backgroundColor: 'white', padding: 15, borderRadius: 10, marginBottom: 10, elevation: 2 },
  censusZone: { backgroundColor: 'white', borderRadius: 15, padding: 15, marginBottom: 15, elevation: 2 },
  zoneTag: { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 10, alignSelf: 'flex-start', marginBottom: 10 },
  zoneTagText: { color: 'white', fontWeight: 'bold', fontSize: 12 },
  emptyZone: { color: '#bdc3c7', fontSize: 14, fontStyle: 'italic' },
  censusPatient: { borderBottomWidth: 1, borderBottomColor: '#f1f2f6', paddingVertical: 10, flexDirection: 'row', alignItems: 'center' },
  censusName: { fontSize: 16, fontWeight: 'bold', color: '#2c3e50' },
  censusVitals: { fontSize: 12, color: '#7f8c8d', marginTop: 2 },
  dischargeBtn: { alignItems: 'center', marginLeft: 10 },
  dischargeText: { fontSize: 10, color: '#27ae60', fontWeight: 'bold' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center' },
  modalContent: { width: '92%', height: '75%', backgroundColor: 'white', borderRadius: 25, padding: 20 },
  modalContentSmall: { width: '80%', backgroundColor: 'white', borderRadius: 25, padding: 20 },
  modalHeader: { fontSize: 20, fontWeight: '800', marginBottom: 20, textAlign: 'center' },
  itemRow: { padding: 18, borderBottomWidth: 1, borderBottomColor: '#f1f2f6' },
  itemSelected: { backgroundColor: '#f0f9ff' },
  itemText: { fontSize: 16 },
  itemTextSelected: { fontSize: 16, color: '#3498db', fontWeight: '800' },
  datePart: { padding: 10, alignItems: 'center', borderRadius: 10 },
  closeButton: { backgroundColor: '#3498db', padding: 18, borderRadius: 15, marginTop: 15, alignItems: 'center' },
  closeButtonText: { color: 'white', fontWeight: '800', fontSize: 16 }
});
