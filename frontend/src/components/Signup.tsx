import React, { useState } from 'react';
import type { UserSession } from '../types';

interface SignupProps {
  onSignupSuccess: (session: UserSession) => void;
  switchToLogin: () => void;
}

export const Signup: React.FC<SignupProps> = ({ onSignupSuccess, switchToLogin }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [hospitalId, setHospitalId] = useState('MED-2026');
  const [specialty, setSpecialty] = useState('Cardiology');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email || !password) return setErrorMsg("Please fill in Name, Email, and Password.");

    setIsLoading(true);
    setErrorMsg('');

    try {
      const res = await fetch('http://localhost:8000/api/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          email,
          password,
          hospital_id: hospitalId,
          specialty
        })
      });

      const data = await res.json();
      setIsLoading(false);

      if (!res.ok || data.status !== 'success') {
        throw new Error(data.detail || 'Signup failed.');
      }

      onSignupSuccess({
        user_id: data.user.user_id,
        name: data.user.name,
        email: data.user.email,
        hospital_id: data.user.hospital_id,
        specialty: data.user.specialty,
        token: data.token
      });

    } catch (err: any) {
      setIsLoading(false);
      setErrorMsg(err.message || 'Signup error.');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950 p-4 font-sans text-slate-200">
      <div className="bg-slate-900 border border-slate-800 w-full max-w-md rounded-2xl shadow-2xl p-8">
        
        {/* Header Branding */}
        <div className="text-center mb-6">
          <div className="w-12 h-12 bg-blue-600/20 border border-blue-500/30 rounded-2xl flex items-center justify-center mx-auto mb-2 text-xl text-blue-400">
            👨‍⚕️
          </div>
          <h1 className="text-xl font-bold text-slate-100">Clinician Registration</h1>
          <p className="text-xs text-slate-400 mt-1">Join the MedNexus AI Intelligence Platform</p>
        </div>

        {/* Error Alert */}
        {errorMsg && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-xs text-red-400 text-center">
            {errorMsg}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div>
            <label className="text-xs font-medium text-slate-300 mb-1 block">Full Doctor Name</label>
            <input
              type="text"
              placeholder="e.g. Aditee Srivastava"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-sm rounded-xl px-3.5 py-2.5 outline-none focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 mb-1 block">Email Address</label>
            <input
              type="email"
              placeholder="doctor@hospital.org"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-sm rounded-xl px-3.5 py-2.5 outline-none focus:border-blue-500"
              required
            />
          </div>

          <div className="flex gap-3">
            <div className="flex-1">
              <label className="text-xs font-medium text-slate-300 mb-1 block">Hospital ID</label>
              <input
                type="text"
                placeholder="MED-2026"
                value={hospitalId}
                onChange={(e) => setHospitalId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-sm rounded-xl px-3 py-2.5 outline-none focus:border-blue-500 font-mono"
              />
            </div>
            <div className="flex-1">
              <label className="text-xs font-medium text-slate-300 mb-1 block">Specialty</label>
              <input
                type="text"
                placeholder="Cardiology"
                value={specialty}
                onChange={(e) => setSpecialty(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-sm rounded-xl px-3 py-2.5 outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 mb-1 block">Password</label>
            <input
              type="password"
              placeholder="Create strong password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 text-slate-100 text-sm rounded-xl px-3.5 py-2.5 outline-none focus:border-blue-500"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm rounded-xl transition-all shadow-lg shadow-blue-900/30 disabled:opacity-50 flex items-center justify-center gap-2 mt-3"
          >
            {isLoading ? (
              <>
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                Creating Profile...
              </>
            ) : (
              "Complete Registration →"
            )}
          </button>
        </form>

        {/* Footer Link */}
        <div className="mt-5 text-center text-xs text-slate-400">
          Already registered?{' '}
          <button onClick={switchToLogin} className="text-blue-400 hover:underline font-semibold">
            Sign In
          </button>
        </div>

      </div>
    </div>
  );
};
