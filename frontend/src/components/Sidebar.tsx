import React from 'react';
import type { ViewState, AlertItem, ChatSession } from '../types';

interface SidebarProps {
  currentView: ViewState;
  setCurrentView: (view: ViewState) => void;
  handleNewChat: () => void;
  alerts: AlertItem[];
  fetchAlerts: () => void;
  doctorName: string;
  chatSessions: ChatSession[];
  activeSessionId: string;
  onSelectSession: (sessionId: string) => void;
  onLogout: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  setCurrentView,
  handleNewChat,
  alerts,
  fetchAlerts,
  doctorName,
  chatSessions,
  activeSessionId,
  onSelectSession,
  onLogout,
}) => {
  const activeCount = alerts.filter(a => a.status === 'active').length;
  const activeAlertTitle = alerts.find(a => a.status === 'active')?.title;

  return (
    <div className="w-64 bg-slate-950 flex flex-col border-r border-slate-800 z-20 h-full justify-between">
      
      {/* TOP SECTION */}
      <div className="flex-1 flex flex-col overflow-hidden">
        
        {/* NEW CHAT BUTTON */}
        <div className="p-4">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl font-medium transition-colors border border-slate-700 shadow-md"
          >
            <span className="text-xl">+</span> New Chat
          </button>
        </div>

        {/* ACTIVE ALERTS BUTTON */}
        <div className="px-4 py-2">
          <button
            onClick={() => {
              setCurrentView('alerts');
              fetchAlerts();
            }}
            className={`w-full text-left p-3 rounded-xl border transition-all ${
              currentView === 'alerts'
                ? 'bg-red-500/20 border-red-500/50 text-white shadow-lg shadow-red-950/40'
                : 'bg-red-500/10 border-red-500/20 text-slate-300 hover:bg-red-500/20'
            }`}
          >
            <h3 className="text-red-400 text-xs font-bold uppercase tracking-wider mb-1 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full bg-red-500 ${activeCount > 0 ? 'animate-pulse' : ''}`}></span>
                Active Alerts
              </span>
              <span className="px-2 py-0.5 bg-red-500/20 border border-red-500/30 text-red-300 text-xs rounded-full font-mono font-bold">
                {activeCount}
              </span>
            </h3>
            <p className="text-xs text-slate-300 truncate font-medium">
              {activeAlertTitle || 'View Triage Dashboard →'}
            </p>
          </button>
        </div>

        {/* DIVIDER LINE */}
        <div className="px-4 my-2">
          <div className="border-t border-slate-800" />
        </div>

        {/* RECENT CHAT SESSIONS FROM MONGODB */}
        <div className="flex-1 overflow-y-auto px-4 space-y-1.5">
          <p className="text-xs font-bold text-slate-500 mb-2 uppercase tracking-wider px-2">Recent Chats</p>
          
          {chatSessions.length === 0 ? (
            <p className="text-xs text-slate-500 px-2 italic">No past sessions yet.</p>
          ) : (
            chatSessions.map((session) => (
              <button
                key={session.session_id}
                onClick={() => onSelectSession(session.session_id)}
                className={`w-full text-left px-3 py-2.5 rounded-xl text-sm transition-all truncate flex items-center gap-2 ${
                  currentView === 'chat' && activeSessionId === session.session_id
                    ? 'bg-slate-800 text-white font-medium border border-slate-700/60 shadow-sm'
                    : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
                }`}
              >
                <span>💬</span>
                <span className="truncate">{session.title || 'Clinical Session'}</span>
              </button>
            ))
          )}
        </div>
      </div>

      {/* BOTTOM ANCHORED DOCTOR PROFILE CARD & LOGOUT */}
      <div className="p-4 border-t border-slate-800 bg-slate-950 space-y-2">
        <button
          onClick={() => setCurrentView('account')}
          className={`w-full flex items-center gap-3 p-2.5 rounded-xl border transition-all text-left ${
            currentView === 'account'
              ? 'bg-blue-600/20 border-blue-500/50 text-white'
              : 'bg-slate-900 border-slate-800 hover:bg-slate-850 text-slate-300'
          }`}
        >
          <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm shadow-md">
            {doctorName.split(' ').map(n => n[0]).join('').slice(0, 2)}
          </div>
          <div className="flex-1 overflow-hidden">
            <h4 className="text-xs font-bold text-slate-200 truncate">{doctorName}</h4>
            <p className="text-[10px] text-slate-400 truncate">Verified Admin • MED-2026</p>
          </div>
        </button>

        <button
          onClick={onLogout}
          className="w-full text-center py-2 text-xs font-medium text-slate-400 hover:text-red-400 transition-colors"
        >
          🔒 Sign Out
        </button>
      </div>

    </div>
  );
};
