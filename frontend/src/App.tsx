import { useState, useRef, useEffect } from 'react';

interface Message {
  role: 'user' | 'ai';
  content: string;
}

// We merged profile and settings into one view: 'account'
type ViewState = 'chat' | 'account';

export default function App() {
  // --- STATE ---
  const [currentView, setCurrentView] = useState<ViewState>('chat');

  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    { role: 'ai', content: 'Hello Dr. Srivastava. MedNexus AI is online. What would you like to analyze today?' }
  ]);
  const [isRecording, setIsRecording] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);

  // --- VOICE TYPING SETUP ---
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onresult = (event: any) => {
        let interimTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          interimTranscript += event.results[i][0].transcript;
        }
        setChatInput(prev => prev + (prev.endsWith(' ') ? '' : ' ') + interimTranscript.trim());
      };

      recognition.onerror = (event: any) => {
        console.error("Speech recognition error:", event.error);
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  // --- HANDLERS ---
  const handleSend = async (customText?: string) => {
    // If a custom string is passed (like from the Scan button), use it. Otherwise, use chatInput.
    const userText = customText || chatInput;
    if (!userText.trim()) return;

    setChatInput('');
    setCurrentView('chat'); // Instantly switch to chat view if they were in settings

    if (isRecording && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }

    // 1. Put user message and "Thinking..." on screen immediately
    setMessages(prev => [
      ...prev,
      { role: 'user', content: userText },
      { role: 'ai', content: 'Thinking...' }
    ]);

    try {
      // 2. The Actual Connection to your FastAPI Backend!
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: 'doc-session-123',
          user_query: userText
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // 3. Swap "Thinking..." with the real AI response
      setMessages(prev => {
        const updatedMessages = [...prev];
        updatedMessages[updatedMessages.length - 1] = { role: 'ai', content: data.response };
        return updatedMessages;
      });

    } catch (error) {
      console.error("Failed to fetch AI response:", error);
      setMessages(prev => {
        const updatedMessages = [...prev];
        updatedMessages[updatedMessages.length - 1] = {
          role: 'ai',
          content: '⚠️ Connection Error: Could not reach the MedNexus Python backend. Make sure FastAPI is running on port 8000.'
        };
        return updatedMessages;
      });
    }
  };

  const handleRunScan = () => {
    // Triggers the AI automatically to scan the database
    handleSend("Run a complete time-period risk scan across all patient records and highlight any critical anomalies.");
  };

  const handleNewChat = () => {
    setMessages([{ role: 'ai', content: 'Hello Dr. Srivastava. MedNexus AI is online. What would you like to analyze today?' }]);
    setChatInput('');
    setCurrentView('chat');
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setMessages([...messages, { role: 'user', content: `📄 Uploaded file: ${file.name}` }]);
    }
  };

  const toggleVoiceRecording = () => {
    if (!recognitionRef.current) return alert("Voice typing requires Chrome or Edge.");
    if (isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    } else {
      recognitionRef.current.start();
      setIsRecording(true);
    }
  };

  return (
    <div className="flex h-screen bg-slate-900 font-sans text-slate-200 overflow-hidden">

      {/* --- LEFT SIDEBAR --- */}
      <div className="w-64 bg-slate-950 flex flex-col border-r border-slate-800 z-20">

        <div className="p-4 space-y-2">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center gap-3 px-4 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors border border-slate-700"
          >
            <span className="text-xl">+</span> New Chat
          </button>

          {/* NEW: RUN SCAN BUTTON */}
          <button
            onClick={handleRunScan}
            className="w-full flex items-center gap-3 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors shadow-lg shadow-blue-900/20"
          >
            <span className="text-xl">📊</span> Run Scan
          </button>
        </div>

        <div className="px-4 py-2 mt-2">
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
            <h3 className="text-red-400 text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
              Active Alerts
            </h3>
            <p className="text-sm text-slate-300 truncate">⚠️ Rohan Sharma (BP Spike)</p>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2 mt-4">
          <p className="text-xs font-bold text-slate-500 mb-3 uppercase tracking-wider px-2">Recent</p>
          {['Aarav Mehta Labs', 'Cardiac Protocol 2026', 'SafetyNet Integration'].map((chat, i) => (
            <button
              key={i}
              onClick={() => setCurrentView('chat')}
              className={`w-full text-left px-3 py-2 text-sm rounded-md truncate transition-colors ${currentView === 'chat' ? 'bg-slate-800 text-slate-200' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'}`}
            >
              💬 {chat}
            </button>
          ))}
        </div>

        {/* COMBINED ACCOUNT BUTTON */}
        <div className="p-4 border-t border-slate-800 bg-slate-950">
          <button
            onClick={() => setCurrentView('account')}
            className={`w-full flex items-center gap-3 px-2 py-2 rounded-lg transition-colors ${currentView === 'account' ? 'bg-slate-800' : 'hover:bg-slate-800'}`}
          >
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
              AS
            </div>
            <div className="text-left flex-1 overflow-hidden">
              <p className="text-sm font-medium text-slate-200 leading-tight truncate">Aditee S.</p>
              <p className="text-xs text-slate-500">Preferences ⚙️</p>
            </div>
          </button>
        </div>
      </div>

      {/* --- MAIN CONTENT AREA --- */}
      <div className="flex-1 flex flex-col bg-slate-900 relative">

        {/* VIEW 1: THE CHAT INTERFACE */}
        {currentView === 'chat' && (
          <>
            <div className="h-14 flex items-center justify-between px-6 border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm z-10">
              <h1 className="font-semibold text-slate-200">MedNexus 3.3-70b</h1>
              <div className="flex gap-2">
                <span className="px-2 py-1 bg-blue-500/10 text-blue-400 text-xs rounded-md font-medium border border-blue-500/20">RAG Active</span>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {messages.map((msg, index) => (
                <div key={index} className={`flex w-full ${msg.role === 'ai' ? 'justify-start' : 'justify-end'}`}>
                  <div className={`max-w-[75%] flex gap-4 ${msg.role === 'ai' ? 'flex-row' : 'flex-row-reverse'}`}>

                    {/* Avatar */}
                    <div className={`w-8 h-8 flex-shrink-0 rounded-lg flex items-center justify-center text-white font-bold shadow-sm ${msg.role === 'ai' ? 'bg-emerald-600' : 'bg-blue-600'}`}>
                      {msg.role === 'ai' ? 'AI' : 'AS'}
                    </div>

                    {/* Chat Bubble */}
                    <div className={`p-4 rounded-2xl text-base leading-relaxed whitespace-pre-wrap shadow-sm ${msg.role === 'ai'
                        ? 'bg-slate-800 text-slate-200 rounded-tl-sm'
                        : 'bg-blue-600 text-white rounded-tr-sm'
                      }`}>
                      {msg.content}
                    </div>

                  </div>
                </div>
              ))}
            </div>

            <div className="w-full pt-2 pb-6 px-4 bg-gradient-to-t from-slate-900 via-slate-900 to-transparent">
              <div className="max-w-3xl mx-auto relative flex items-end gap-2 bg-slate-800 border border-slate-700 rounded-2xl p-2 focus-within:ring-1 focus-within:ring-blue-500 focus-within:border-blue-500 shadow-xl transition-all">
                <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" accept=".pdf,.txt,.csv,.jpg,.png" />
                <button onClick={() => fileInputRef.current?.click()} className="p-4 text-slate-400 hover:text-slate-200 rounded-xl hover:bg-slate-700 transition-colors">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14M5 12h14" /></svg>
                </button>
                <textarea
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder={isRecording ? "Listening..." : "Message MedNexus..."}
                  className="flex-1 max-h-48 bg-transparent px-3 py-4 focus:outline-none text-slate-100 placeholder-slate-500 resize-none min-h-[80px] text-base"
                />
                <button onClick={toggleVoiceRecording} className={`p-4 rounded-xl transition-all ${isRecording ? 'text-red-400 bg-red-400/10 animate-pulse' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700'}`}>
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" /><path d="M19 10v2a7 7 0 0 1-14 0v-2" /><line x1="12" x2="12" y1="19" y2="22" /></svg>
                </button>
                <button onClick={() => handleSend()} disabled={!chatInput.trim() && !isRecording} className="p-4 bg-white text-slate-900 rounded-xl disabled:bg-slate-700 disabled:text-slate-500 hover:bg-slate-200 transition-colors">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" x2="11" y1="2" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" /></svg>
                </button>
              </div>
              <p className="text-center text-xs text-slate-500 mt-3">
                MedNexus can make mistakes. Check critical clinical information.
              </p>
            </div>
          </>
        )}

        {/* VIEW 2: MERGED ACCOUNT & SETTINGS PAGE */}
        {currentView === 'account' && (
          <div className="flex-1 overflow-y-auto p-10 pb-20">
            <div className="max-w-3xl mx-auto">

              {/* Profile Header */}
              <div className="flex items-center gap-6 mb-10 pb-8 border-b border-slate-800">
                <div className="w-24 h-24 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-3xl shadow-lg">
                  AS
                </div>
                <div>
                  <h2 className="text-3xl font-bold text-slate-100 mb-2">Dr. Aditee Srivastava</h2>
                  <div className="flex gap-3">
                    <span className="px-3 py-1 bg-blue-500/10 text-blue-400 text-xs rounded-md border border-blue-500/20">Verified Admin</span>
                    <span className="px-3 py-1 bg-slate-800 text-slate-300 text-xs rounded-md border border-slate-700">Hospital ID: MED-2026</span>
                  </div>
                </div>
              </div>

              {/* Grid Layout for Settings */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                {/* Appearance */}
                <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6">
                  <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">🎨 Appearance</h3>
                  <div className="space-y-3">
                    <button className="w-full text-left px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 transition-colors">Light Mode</button>
                    <button className="w-full text-left px-4 py-3 bg-blue-600 border border-blue-500 rounded-lg text-white font-medium shadow-md">Dark Mode (Active)</button>
                    <button className="w-full text-left px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 transition-colors">Sync with System</button>
                  </div>
                </div>

                {/* AI Preferences */}
                <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6">
                  <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">🧠 AI Preferences</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm text-slate-400 mb-2 block">Response Style</label>
                      <select className="w-full bg-slate-900 border border-slate-700 text-slate-200 rounded-lg px-4 py-3 outline-none focus:border-blue-500">
                        <option>Detailed & Clinical</option>
                        <option>Concise / Summary</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-sm text-slate-400 mb-2 block">Interface Language</label>
                      <select className="w-full bg-slate-900 border border-slate-700 text-slate-200 rounded-lg px-4 py-3 outline-none focus:border-blue-500">
                        <option>English (US)</option>
                        <option>Hindi</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Documents Management */}
                <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6">
                  <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">📂 Documents</h3>
                  <div className="space-y-3">
                    <button className="w-full text-left px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 transition-colors flex justify-between">
                      Manage Uploaded Files <span>→</span>
                    </button>
                    <button className="w-full text-left px-4 py-3 bg-slate-900 border border-red-900/30 rounded-lg text-red-400 hover:bg-red-900/50 transition-colors">
                      Delete Indexed Documents
                    </button>
                  </div>
                </div>

                {/* Chat Settings */}
                <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6">
                  <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">💬 Chat Settings</h3>
                  <div className="space-y-3">
                    <button className="w-full text-left px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 transition-colors flex justify-between">
                      Export Conversations <span>⬇️</span>
                    </button>
                    <button className="w-full text-left px-4 py-3 bg-slate-900 border border-red-900/30 rounded-lg text-red-400 hover:bg-red-900/50 transition-colors">
                      Clear Chat History
                    </button>
                  </div>
                </div>

                {/* Privacy & Security (Full Width) */}
                <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6 md:col-span-2">
                  <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">🔒 Privacy & Security</h3>
                  <div className="flex gap-4">
                    <button className="flex-1 px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 transition-colors">
                      Change Password
                    </button>
                    <button className="flex-1 px-4 py-3 bg-red-600 border border-red-500 rounded-lg text-white hover:bg-red-700 transition-colors shadow-md shadow-red-900/20">
                      Logout
                    </button>
                  </div>
                </div>

              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}