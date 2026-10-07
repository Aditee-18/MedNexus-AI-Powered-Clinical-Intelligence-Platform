import React from 'react';

interface IngestionModalProps {
  isUploadModalOpen: boolean;
  setIsUploadModalOpen: (open: boolean) => void;
  selectedFile: File | null;
  setSelectedFile: (file: File | null) => void;
  patientIdInput: string;
  setPatientIdInput: (id: string) => void;
  patientNameInput: string;
  setPatientNameInput: (name: string) => void;
  patientAgeInput?: number;
  setPatientAgeInput?: (age: number) => void;
  isUploading: boolean;
  uploadStatusMsg: string;
  handleStartUpload: () => void;
}

export const IngestionModal: React.FC<IngestionModalProps> = ({
  isUploadModalOpen,
  setIsUploadModalOpen,
  selectedFile,
  setSelectedFile,
  patientIdInput,
  setPatientIdInput,
  patientNameInput,
  setPatientNameInput,
  isUploading,
  uploadStatusMsg,
  handleStartUpload,
}) => {
  if (!isUploadModalOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-lg rounded-2xl shadow-2xl p-6 relative">
        <button
          onClick={() => { setIsUploadModalOpen(false); setSelectedFile(null); }}
          className="absolute top-4 right-4 text-slate-400 hover:text-white text-xl"
        >
          ✕
        </button>

        <h2 className="text-xl font-bold text-slate-100 mb-2 flex items-center gap-2">
          📁 Patient File Ingestion Pipeline
        </h2>
        <p className="text-xs text-slate-400 mb-6">
          Attach medical documents (PDF, CSV, TXT, OCR Images) to synchronize MongoDB metadata & ChromaDB vector search.
        </p>

        {/* Selected File Badge */}
        {selectedFile && (
          <div className="mb-4 p-3 bg-blue-950/50 border border-blue-800/50 rounded-xl flex items-center justify-between text-sm text-blue-200">
            <span className="truncate">📄 {selectedFile.name} {selectedFile.size ? `(${(selectedFile.size / 1024).toFixed(1)} KB)` : ''}</span>
            <span className="text-xs px-2 py-0.5 bg-blue-600 rounded text-white font-mono uppercase">{selectedFile.name ? selectedFile.name.split('.').pop() : 'FILE'}</span>
          </div>
        )}

        {/* Form Inputs */}
        <div className="space-y-4 mb-6">
          <div>
            <label className="text-xs font-medium text-slate-300 mb-1 block flex justify-between">
              <span>Hospital Patient ID (Full or Last Digits)</span>
              <span className="text-blue-400 font-normal">e.g. 18472 or AMH-2026-18472</span>
            </label>
            <input
              type="text"
              placeholder="Enter Patient ID (e.g. 18472 or AMH-2026-18472)"
              value={patientIdInput}
              onChange={(e) => setPatientIdInput(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-sm rounded-xl px-4 py-3 outline-none focus:border-blue-500 font-mono"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 mb-1 block">Patient Name (Optional for existing)</label>
            <input
              type="text"
              placeholder="Enter Patient Name (e.g. Ritik Jaiswal)"
              value={patientNameInput}
              onChange={(e) => setPatientNameInput(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 text-slate-200 text-sm rounded-xl px-4 py-3 outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Status Message */}
        {uploadStatusMsg && (
          <div className="mb-4 text-xs font-medium text-blue-400 bg-blue-950/30 p-2.5 rounded-lg border border-blue-900/30">
            {uploadStatusMsg}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => { setIsUploadModalOpen(false); setSelectedFile(null); }}
            className="flex-1 px-4 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm rounded-xl font-medium transition-colors border border-slate-700"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleStartUpload}
            disabled={isUploading}
            className="flex-1 px-4 py-3 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-xl font-semibold transition-colors shadow-lg shadow-blue-900/30 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isUploading ? (
              <>
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                Ingesting...
              </>
            ) : (
              "Start Ingestion →"
            )}
          </button>
        </div>

      </div>
    </div>
  );
};
