import React, { useState } from 'react';
import type { UserSession } from '../types';

interface LoginProps {
  onLoginSuccess: (session: UserSession) => void;
  switchToSignup: () => void;
}

export const Login: React.FC<LoginProps> = ({ onLoginSuccess, switchToSignup }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return setErrorMsg("Please fill in both Email and Password.");

    setIsLoading(true);
    setErrorMsg('');

    try {
      const res = await fetch('http://localhost:8000/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      const data = await res.json();
      setIsLoading(false);

      if (!res.ok || data.status !== 'success') {
        throw new Error(data.detail || 'Login failed. Please check credentials.');
      }

      onLoginSuccess({
        user_id: data.user.user_id,
        name: data.user.name,
        email: data.user.email,
        hospital_id: data.user.hospital_id,
        specialty: data.user.specialty,
        token: data.token
      });

    } catch (err: any) {
      setIsLoading(false);
      setErrorMsg(err.message || 'Login error.');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950 p-4 font-sans text-slate-200">
      <div className="bg-slate-900 border border-slate-800 w-full max-w-md rounded-2xl shadow-2xl p-8">
        
        {/* Header Branding */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-blue-600/20 border border-blue-500/30 rounded-2xl flex items-center justify-center mx-auto mb-3 text-2xl text-blue-400">
            🏥
          </div>
          <h1 className="text-2xl font-bold text-slate-100">MedNexus AI</h1>
          <p className="text-xs text-slate-400 mt-1">Clinical Intelligence Platform</p>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="mb-6 p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-xs text-red-400 text-center">
            {errorMsg}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs font-medium text-slate-300 mb-1 block">Clinician Email</label>
            <input
              type="email"
              placeholder="e.g. doctor@hospital.org"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-sm rounded-xl px-4 py-3 outline-none focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 mb-1 block">Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-sm rounded-xl px-4 py-3 outline-none focus:border-blue-500"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm rounded-xl transition-all shadow-lg shadow-blue-900/30 disabled:opacity-50 flex items-center justify-center gap-2 mt-2"
          >
            {isLoading ? (
              <>
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                Authenticating...
              </>
            ) : (
              "Sign In to Dashboard →"
            )}
          </button>
        </form>

        {/* Footer Link */}
        <div className="mt-6 text-center text-xs text-slate-400">
          New clinician?{' '}
          <button onClick={switchToSignup} className="text-blue-400 hover:underline font-semibold">
            Create an Account
          </button>
        </div>

      </div>
    </div>
  );
};
