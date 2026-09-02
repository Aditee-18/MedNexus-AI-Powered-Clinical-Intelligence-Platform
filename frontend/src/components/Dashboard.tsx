import React, { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message } from '../types';

interface DashboardProps {
  doctorName: string;
  messages: Message[];
  chatInput: string;
  setChatInput: React.Dispatch<React.SetStateAction<string>>;
  handleSend: (customText?: string) => void;
  isRecording: boolean;
  setIsRecording: React.Dispatch<React.SetStateAction<boolean>>;
  recognitionRef: React.MutableRefObject<any>;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  handleFileUpload: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  doctorName,
  messages,
  chatInput,
  setChatInput,
  handleSend,
  isRecording,
  setIsRecording,
  recognitionRef,
  fileInputRef,
  handleFileUpload,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Voice recording toggle handler
  const toggleRecording = () => {
    if (!recognitionRef.current) {
      alert("Speech recognition is not supported in this browser. Please use Chrome or Edge.");
      return;
    }

    if (isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsRecording(true);
      } catch (e) {
        console.log("Start recording notice:", e);
      }
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-900 overflow-hidden relative">
      
      {/* HEADER BAR */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60 backdrop-blur-md">
        <div>
          <h1 className="text-base font-bold text-slate-100 flex items-center gap-2">
            🏥 MedNexus AI Platform
          </h1>
          <p className="text-xs text-slate-400">Clinical Intelligence & Vector Diagnostics</p>
        </div>
      </div>

      {/* MESSAGES AREA / GREETING */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        
        {/* WELCOME HEADER GREETING */}
        <div className="text-center py-6 border-b border-slate-800/60 mb-4">
          <h2 className="text-2xl font-bold text-slate-100 mb-1">
            How can I help, Doctor {doctorName.split(' ')[0]}?
          </h2>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Ask patient questions, analyze clinical trends, or upload lab documents to ingest into ChromaDB.
          </p>
        </div>

        {/* CHAT MESSAGES STREAM */}
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-3xl px-5 py-4 rounded-2xl text-sm leading-relaxed shadow-md ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white rounded-br-none'
                  : 'bg-slate-850 text-slate-200 border border-slate-750/80 rounded-bl-none'
              }`}
            >
              {msg.role === 'user' ? (
                <p className="whitespace-pre-wrap">{msg.content}</p>
              ) : (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    table: ({ node, ...props }) => (
                      <div className="overflow-x-auto my-3 border border-slate-700/80 rounded-xl shadow-md">
                        <table className="min-w-full divide-y divide-slate-700/80 text-xs text-left" {...props} />
                      </div>
                    ),
                    thead: ({ node, ...props }) => (
                      <thead className="bg-slate-950 text-slate-200 font-bold uppercase tracking-wider text-[11px]" {...props} />
                    ),
                    th: ({ node, ...props }) => (
                      <th className="px-4 py-2.5 border-b border-slate-700/80 font-semibold" {...props} />
                    ),
                    td: ({ node, ...props }) => (
                      <td className="px-4 py-2.5 border-b border-slate-800/60 text-slate-300 bg-slate-900/40" {...props} />
                    ),
                    ul: ({ node, ...props }) => (
                      <ul className="list-disc list-inside space-y-1.5 my-2 text-slate-300" {...props} />
                    ),
                    ol: ({ node, ...props }) => (
                      <ol className="list-decimal list-inside space-y-1.5 my-2 text-slate-300" {...props} />
                    ),
                    li: ({ node, ...props }) => (
                      <li className="leading-relaxed" {...props} />
                    ),
                    p: ({ node, ...props }) => (
                      <p className="mb-2 last:mb-0" {...props} />
                    ),
                    strong: ({ node, ...props }) => (
                      <strong className="font-bold text-white" {...props} />
                    )
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              )}
            </div>
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* HIDDEN FILE INPUT */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileUpload}
        className="hidden"
        accept=".pdf,.csv,.txt,.png,.jpg,.jpeg"
      />

      {/* PROMPT INPUT BAR */}
      <div className="p-4 bg-slate-950/80 border-t border-slate-800 backdrop-blur-md">
        <div className="max-w-4xl mx-auto flex items-center gap-3 bg-slate-900 border border-slate-700/80 rounded-2xl p-2 shadow-xl focus-within:border-blue-500 transition-all">
          
          {/* FILE ATTACHMENT BUTTON */}
          <button
            onClick={() => fileInputRef.current?.click()}
            className="w-10 h-10 flex items-center justify-center text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-xl transition-colors text-lg"
            title="Attach Patient Document"
          >
            +
          </button>

          {/* CHAT INPUT AREA */}
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={isRecording ? "Listening to your dictation..." : "Type patient query or clinical prompt..."}
            className="flex-1 bg-transparent text-slate-100 text-sm outline-none px-2 placeholder-slate-500"
          />

          {/* VOICE DICTATION BUTTON */}
          <button
            onClick={toggleRecording}
            className={`w-10 h-10 flex items-center justify-center rounded-xl transition-colors text-lg ${
              isRecording
                ? 'bg-red-600 text-white animate-pulse shadow-lg shadow-red-900/50'
                : 'text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700'
            }`}
            title={isRecording ? "Stop Listening" : "Voice Input"}
          >
            🎙️
          </button>

          {/* SEND BUTTON */}
          <button
            onClick={() => handleSend()}
            disabled={!chatInput.trim()}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs rounded-xl transition-colors shadow-md shadow-blue-900/30 disabled:opacity-40"
          >
            Send
          </button>

        </div>

        <p className="text-[11px] text-center text-slate-500 mt-2">
          MedNexus AI provides decision support. Verify critical clinical findings.
        </p>
      </div>

    </div>
  );
};
