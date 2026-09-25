import { useState, useRef, useEffect } from 'react';
import type { ViewState, Message, AlertItem, UserSession, ChatSession } from './types';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './components/Dashboard';
import { AlertsTriageView } from './components/AlertsTriageView';
import { AlertSummaryModal } from './components/AlertSummaryModal';
import { Login } from './components/Login';
import { Signup } from './components/Signup';

export default function App() {
  // --- AUTH SESSION STATE ---
  const [userSession, setUserSession] = useState<UserSession | null>(() => {
    const saved = localStorage.getItem('mednexus_session');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) { return null; }
    }
    return null;
  });

  const doctorName = userSession ? userSession.name : 'Aditee Srivastava';

  // --- VIEW STATE ---
  const [currentView, setCurrentView] = useState<ViewState>(() => userSession ? 'chat' : 'login');

  // --- CHAT SESSION & HISTORY STATE ---
  const [activeSessionId, setActiveSessionId] = useState<string>(() => `session_${Date.now()}`);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);

  const isRecordingRef = useRef(false);
  isRecordingRef.current = isRecording;

  // --- ALERTS STATE ---
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [selectedAlertModal, setSelectedAlertModal] = useState<AlertItem | null>(null);

  // --- UPLOAD STATE ---
  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [patientNameInput, setPatientNameInput] = useState('');
  const [patientIdInput, setPatientIdInput] = useState('');
  const [patientAgeInput, setPatientAgeInput] = useState<number>(30);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);

  // --- AUDIO CHIME PLAYER ---
  const playAudioChime = () => {
    try {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, audioCtx.currentTime);
      gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.8);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.8);
    } catch (e) {
      console.log("Audio play notice:", e);
    }
  };

  // --- AUTH HANDLERS ---
  const handleLoginSuccess = (session: UserSession) => {
    setUserSession(session);
    localStorage.setItem('mednexus_session', JSON.stringify(session));
    setCurrentView('chat');
  };

  const handleLogout = () => {
    setUserSession(null);
    localStorage.removeItem('mednexus_session');
    setCurrentView('login');
  };

  // --- FETCH CHAT SESSIONS FROM MONGODB ---
  const fetchChatSessions = async () => {
    const userId = userSession ? userSession.user_id : 'usr_default';
    try {
      const res = await fetch(`http://localhost:8000/api/chat/sessions?user_id=${userId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.sessions && Array.isArray(data.sessions)) {
          setChatSessions(data.sessions);
        }
      }
    } catch (e) {
      console.log("Fetch chat sessions notice:", e);
    }
  };

  // --- LOAD CHAT HISTORY FOR SELECTED SESSION ---
  const handleSelectSession = async (sessionId: string) => {
    setActiveSessionId(sessionId);
    setCurrentView('chat');
    try {
      const res = await fetch(`http://localhost:8000/api/chat/history/${sessionId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.messages && Array.isArray(data.messages)) {
          setMessages(data.messages);
        }
      }
    } catch (e) {
      console.log("Fetch chat history notice:", e);
    }
  };

  // --- FETCH ALERTS LIST ---
  const fetchAlerts = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/alerts');
      if (res.ok) {
        const data = await res.json();
        if (data.alerts && Array.isArray(data.alerts)) {
          setAlerts(data.alerts);
        }
      }
    } catch (e) {
      console.log("Could not fetch alerts list:", e);
    }
  };

  // --- ACKNOWLEDGE ALERT ---
  const handleAcknowledgeAlert = async (alertId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    try {
      const res = await fetch(`http://localhost:8000/api/alerts/${alertId}/acknowledge`, {
        method: 'POST'
      });
      if (res.ok) {
        setAlerts(prev => prev.map(a => a.alert_id === alertId ? { ...a, status: 'acknowledged', acknowledgedAt: new Date().toISOString() } : a));
        if (selectedAlertModal && selectedAlertModal.alert_id === alertId) {
          setSelectedAlertModal(prev => prev ? { ...prev, status: 'acknowledged', acknowledgedAt: new Date().toISOString() } : null);
        }
      }
    } catch (err) {
      console.error("Acknowledge alert error:", err);
    }
  };

  // --- FETCH PATIENTS LIST ---
  const fetchPatients = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/patients');
      if (res.ok) {
        const data = await res.json();
        if (data.patients && Array.isArray(data.patients) && data.patients.length > 0 && !selectedPatientId) {
          setSelectedPatientId(data.patients[0].patient_id);
          setPatientNameInput(data.patients[0].name);
          setPatientIdInput(data.patients[0].patient_id);
          setPatientAgeInput(data.patients[0].age || 30);
        }
      }
    } catch (e) {
      console.log("Could not fetch patients list:", e);
    }
  };

  useEffect(() => {
    if (userSession) {
      fetchPatients();
      fetchAlerts();
      fetchChatSessions();
    }
  }, [userSession]);

  // --- SMOOTH VOICE ENGINE WITH KEEP-ALIVE AUTO-RESTART & BUFFERING ---
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;

      let finalTranscriptBuffer = '';

      recognition.onresult = (event: any) => {
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscriptBuffer += transcript + ' ';
          } else {
            interim += transcript;
          }
        }
        setChatInput(finalTranscriptBuffer + interim);
      };

      recognition.onerror = (event: any) => {
        console.error("Speech recognition notice:", event.error);
        if (event.error !== 'no-speech') {
          setIsRecording(false);
        }
      };

      recognition.onend = () => {
        // Auto-restart keep-alive loop if dictation mode is still enabled by user
        if (isRecordingRef.current) {
          try {
            recognition.start();
          } catch (e) {
            console.log("Auto restart notice:", e);
            setIsRecording(false);
          }
        } else {
          setIsRecording(false);
        }
      };

      recognitionRef.current = recognition;
    }
  }, []);

  // --- HANDLERS ---
  const handleSend = async (customText?: string) => {
    const userText = customText || chatInput;

    // If a file is attached, trigger direct file ingestion
    if (selectedFile) {
      const fileToUpload = selectedFile;
      setSelectedFile(null);
      setChatInput('');
      setCurrentView('chat');
      await handleStartUpload(fileToUpload, userText.trim() ? userText : undefined);
      return;
    }

    if (!userText.trim()) return;

    const userId = userSession ? userSession.user_id : 'usr_default';

    setChatInput('');
    setCurrentView('chat');

    if (isRecording && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }

    setMessages(prev => [
      ...prev,
      { role: 'user', content: userText },
      { role: 'ai', content: 'Thinking...' }
    ]);

    try {
      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeSessionId,
          user_id: userId,
          user_query: userText
        }),
      });

      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);

      const data = await res.json();
      const aiReply = data.response || "No response received from agent.";

      setMessages(prev => {
        const updated = [...prev];
        if (updated.length > 0 && updated[updated.length - 1].content === 'Thinking...') {
          updated[updated.length - 1] = { role: 'ai', content: aiReply };
        } else {
          updated.push({ role: 'ai', content: aiReply });
        }
        return updated;
      });

      // Refresh chat sessions list in sidebar
      fetchChatSessions();

    } catch (err: any) {
      console.error("Agent Request Error:", err);
      setMessages(prev => {
        const updated = [...prev];
        const errorMsg = `⚠️ Error connecting to MedNexus Backend (${err.message}). Please verify python server is running.`;
        if (updated.length > 0 && updated[updated.length - 1].content === 'Thinking...') {
          updated[updated.length - 1] = { role: 'ai', content: errorMsg };
        } else {
          updated.push({ role: 'ai', content: errorMsg });
        }
        return updated;
      });
    }
  };

  const handleNewChat = () => {
    const newSessionId = `session_${Date.now()}`;
    setActiveSessionId(newSessionId);
    setMessages([]);
    setChatInput('');
    setCurrentView('chat');
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleStartUpload = async (fileToUpload: File, customPromptText?: string) => {
    const userPromptText = customPromptText || `📄 Ingest file: '${fileToUpload.name}'`;

    setMessages(prev => [
      ...prev,
      { role: 'user', content: userPromptText },
      { role: 'ai', content: 'Processing document ingestion & clinical risk scan...' }
    ]);

    try {
      const formData = new FormData();
      formData.append('patient_id', patientIdInput.trim());
      formData.append('name', patientNameInput.trim());
      formData.append('age', patientAgeInput.toString());
      formData.append('file', fileToUpload);

      const res = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        throw new Error(`Upload failed with status ${res.status}`);
      }

      const data = await res.json();
      const uploadedFileName = fileToUpload.name;
      setSelectedFile(null);
      setPatientIdInput('');
      setPatientNameInput('');
      
      const resolvedId = data.patient_id;
      const resolvedName = data.patient_name;
      const alertMsg = data.alert_status || '';

      if (alertMsg.includes('ALERT_CREATED')) {
        playAudioChime();
        fetchAlerts();
      }

      const successReply = `✅ **File for this patient is saved successfully.**\n\n- **Patient:** ${resolvedName} (ID: \`${resolvedId}\`)\n- **Document Ingested:** \`${uploadedFileName}\``;

      setMessages(prev => {
        const updated = [...prev];
        if (updated.length > 0 && updated[updated.length - 1].content.includes('Processing document ingestion')) {
          updated[updated.length - 1] = { role: 'ai', content: successReply };
        } else {
          updated.push({ role: 'ai', content: successReply });
        }
        return updated;
      });

      fetchPatients();

    } catch (err: any) {
      console.error("Upload Error:", err);
      const errorReply = `❌ **Upload Failed:** ${err.message}`;
      setMessages(prev => {
        const updated = [...prev];
        if (updated.length > 0 && updated[updated.length - 1].content.includes('Processing document ingestion')) {
          updated[updated.length - 1] = { role: 'ai', content: errorReply };
        } else {
          updated.push({ role: 'ai', content: errorReply });
        }
        return updated;
      });
    }
  };

  // --- RENDER AUTH SCREENS IF NOT LOGGED IN ---
  if (!userSession) {
    if (currentView === 'signup') {
      return <Signup onSignupSuccess={handleLoginSuccess} switchToLogin={() => setCurrentView('login')} />;
    }
    return <Login onLoginSuccess={handleLoginSuccess} switchToSignup={() => setCurrentView('signup')} />;
  }

  return (
    <div className="flex h-screen bg-slate-900 font-sans text-slate-200 overflow-hidden">
      
      {/* LEFT SIDEBAR */}
      <Sidebar
        currentView={currentView}
        setCurrentView={setCurrentView}
        handleNewChat={handleNewChat}
        alerts={alerts}
        fetchAlerts={fetchAlerts}
        doctorName={doctorName}
        chatSessions={chatSessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onLogout={handleLogout}
      />

      {/* VIEW 1 & VIEW 2: CHAT & DASHBOARD */}
      {currentView === 'chat' && (
        <Dashboard
          doctorName={doctorName}
          messages={messages}
          chatInput={chatInput}
          setChatInput={setChatInput}
          handleSend={handleSend}
          isRecording={isRecording}
          setIsRecording={setIsRecording}
          recognitionRef={recognitionRef}
          fileInputRef={fileInputRef}
          handleFileUpload={handleFileUpload}
          selectedFile={selectedFile}
          setSelectedFile={setSelectedFile}
        />
      )}

      {/* VIEW 3: CLINICAL ALERTS TRIAGE DASHBOARD */}
      {currentView === 'alerts' && (
        <AlertsTriageView
          alerts={alerts}
          fetchAlerts={fetchAlerts}
          setSelectedAlertModal={setSelectedAlertModal}
          handleAcknowledgeAlert={handleAcknowledgeAlert}
        />
      )}

      {/* VIEW 4: DOCTOR ACCOUNT & PREFERENCES */}
      {currentView === 'account' && (
        <div className="flex-1 overflow-y-auto p-8 pb-20 bg-slate-900">
          <div className="max-w-4xl mx-auto space-y-8">
            
            <div className="flex items-center justify-between border-b border-slate-800 pb-6">
              <div>
                <h1 className="text-2xl font-bold text-slate-100">Doctor Profile & Settings</h1>
                <p className="text-xs text-slate-400 mt-1">Manage clinician preferences and platform credentials.</p>
              </div>
              <button
                onClick={() => setCurrentView('chat')}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl border border-slate-700 transition-colors"
              >
                ← Back to Chat
              </button>
            </div>

            <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6 flex items-center gap-6 shadow-xl">
              <div className="w-20 h-20 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-2xl shadow-lg border-2 border-blue-400">
                {doctorName.split(' ').map(n => n[0]).join('').slice(0, 2)}
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-100">{doctorName}</h2>
                <p className="text-sm text-slate-400">{userSession.specialty} • {userSession.hospital_id}</p>
                <div className="flex gap-2 mt-3">
                  <span className="px-3 py-1 bg-blue-500/10 text-blue-400 text-xs rounded-md border border-blue-500/20 font-medium">Verified Clinician</span>
                  <span className="px-3 py-1 bg-slate-800 text-slate-300 text-xs rounded-md border border-slate-700 font-mono">Email: {userSession.email}</span>
                </div>
              </div>
            </div>

            <div className="pt-4">
              <button
                onClick={handleLogout}
                className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-xl shadow-lg shadow-red-950/30 transition-all border border-red-500"
              >
                🔒 Logout Session
              </button>
            </div>

          </div>
        </div>
      )}

      {/* AI CLINICAL SUMMARY MODAL */}
      <AlertSummaryModal
        selectedAlertModal={selectedAlertModal}
        setSelectedAlertModal={setSelectedAlertModal}
        handleAcknowledgeAlert={handleAcknowledgeAlert}
      />

    </div>
  );
}