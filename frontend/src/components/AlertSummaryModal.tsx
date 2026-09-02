import React from 'react';
import type { AlertItem } from '../types';

interface AlertSummaryModalProps {
  selectedAlertModal: AlertItem | null;
  setSelectedAlertModal: (alert: AlertItem | null) => void;
  handleAcknowledgeAlert: (alertId: string) => void;
}

export const AlertSummaryModal: React.FC<AlertSummaryModalProps> = ({
  selectedAlertModal,
  setSelectedAlertModal,
  handleAcknowledgeAlert,
}) => {
  if (!selectedAlertModal) return null;

  const isAcknowledged = selectedAlertModal.status === 'acknowledged';

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-2xl rounded-2xl shadow-2xl p-6 relative max-h-[90vh] overflow-y-auto">
        
        {/* CLOSE BUTTON */}
        <button
          onClick={() => setSelectedAlertModal(null)}
          className="absolute top-4 right-4 text-slate-400 hover:text-white text-xl"
        >
          ✕
        </button>

        {/* HEADER SEVERITY BADGE */}
        <div className="flex items-center gap-3 mb-4">
          <span className={`px-3 py-1 text-xs font-bold rounded-full border uppercase ${
            isAcknowledged
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              : selectedAlertModal.severity_level === 'high'
              ? 'bg-red-500/10 text-red-400 border-red-500/30'
              : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
          }`}>
            {isAcknowledged ? 'Acknowledged' : `${selectedAlertModal.severity_level} Risk (${selectedAlertModal.risk_score}/100)`}
          </span>
          <span className="text-xs text-slate-400">
            Automated Clinical Scan
          </span>
        </div>

        {/* TITLE & PATIENT METADATA */}
        <h2 className="text-xl font-bold text-slate-100 mb-1">{selectedAlertModal.title}</h2>
        <p className="text-xs text-slate-400 mb-6">
          Patient: <strong className="text-slate-200">{selectedAlertModal.patient_name}</strong> (ID: {selectedAlertModal.patient_id}) • Age: {selectedAlertModal.age}
        </p>

        {/* AI SUMMARY BOX */}
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 mb-5 space-y-4">
          <div>
            <h4 className="text-xs font-bold text-blue-400 uppercase tracking-wider mb-2 flex items-center gap-2">
              🧠 AI Clinical Finding & Delta Summary
            </h4>
            <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
              {selectedAlertModal.ai_summary}
            </p>
          </div>

          <div className="pt-3 border-t border-slate-800/80">
            <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2 flex items-center gap-2">
              🩺 Clinical Decision Support Recommendation
            </h4>
            <p className="text-sm text-slate-300 leading-relaxed">
              {selectedAlertModal.suggested_action}
            </p>
          </div>
        </div>

        {/* ACTIONS */}
        <div className="flex justify-between items-center pt-2">
          <span className="text-xs text-slate-500">
            {isAcknowledged
              ? 'Auto-deletes 10 days after acknowledgment via MongoDB TTL.'
              : 'Clicking acknowledge moves alert to 10-day history.'}
          </span>

          <div className="flex gap-3">
            <button
              onClick={() => setSelectedAlertModal(null)}
              className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded-xl font-medium transition-colors border border-slate-700"
            >
              Close
            </button>

            {!isAcknowledged && (
              <button
                onClick={() => handleAcknowledgeAlert(selectedAlertModal.alert_id)}
                className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl shadow-lg transition-all border border-emerald-500"
              >
                ✓ Acknowledge Alert
              </button>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
