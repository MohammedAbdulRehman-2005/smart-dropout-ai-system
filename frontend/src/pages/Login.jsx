import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../hooks/useToast';
import { LogIn, Brain, ShieldCheck, Eye, EyeOff } from 'lucide-react';
import axios from 'axios';

const Login = () => {
  const [email, setEmail] = useState('admin@school.edu');
  const [password, setPassword] = useState('admin123');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const { addToast } = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      addToast('Please enter email and password', 'warning');
      return;
    }
    setLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const res = await axios.post('http://localhost:8000/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });

      localStorage.setItem('token', res.data.access_token);

      // Decode role from JWT payload for RBAC
      try {
        const payload = JSON.parse(atob(res.data.access_token.split('.')[1]));
        if (payload.role) localStorage.setItem('user_role', payload.role);
        if (payload.full_name) localStorage.setItem('user_name', payload.full_name);
      } catch (_) {}

      addToast('Login successful! Welcome back 👋', 'success');
      setTimeout(() => navigate('/admin', { replace: true }), 500);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Invalid credentials. Please try again.';
      addToast(msg, 'error');
    } finally {
      setLoading(false);
    }
  };

  const quickFill = (role) => {
    const creds = {
      admin: { email: 'admin@school.edu', password: 'admin123' },
      teacher: { email: 'teacher@school.edu', password: 'teacher123' },
      counselor: { email: 'counselor@school.edu', password: 'counsel123' },
    };
    setEmail(creds[role].email);
    setPassword(creds[role].password);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-950 to-indigo-950 flex items-center justify-center p-4">
      {/* Background decorative blobs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-indigo-500/20 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo / Hero */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-2xl shadow-blue-500/40 mb-5">
            <Brain size={40} className="text-white" />
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight">SmartEWS</h1>
          <p className="text-blue-300 text-sm mt-1 font-medium">School Dropout Early Warning System</p>
        </div>

        {/* Card */}
        <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl p-8 shadow-2xl">
          <div className="flex items-center gap-2 mb-6">
            <ShieldCheck size={20} className="text-blue-300" />
            <p className="text-white/90 font-semibold text-sm">Secure Staff Login</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-white/70 text-xs font-semibold uppercase tracking-wide mb-1.5">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all text-sm"
                placeholder="your@school.edu"
                autoComplete="email"
              />
            </div>

            <div>
              <label className="block text-white/70 text-xs font-semibold uppercase tracking-wide mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 pr-11 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-all text-sm"
                  placeholder="••••••••"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPass((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/50 hover:text-white transition-colors"
                >
                  {showPass ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white font-bold py-3.5 rounded-xl transition-all shadow-lg shadow-blue-500/30 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Authenticating...
                </>
              ) : (
                <>
                  <LogIn size={18} />
                  Sign In
                </>
              )}
            </button>
          </form>

          {/* Quick Fill Buttons */}
          <div className="mt-6 pt-5 border-t border-white/10">
            <p className="text-white/40 text-xs font-semibold uppercase tracking-wide mb-3 text-center">
              Quick demo access
            </p>
            <div className="grid grid-cols-3 gap-2">
              {[
                { role: 'admin', label: 'Admin', color: 'text-blue-300 hover:bg-blue-500/20' },
                { role: 'teacher', label: 'Teacher', color: 'text-green-300 hover:bg-green-500/20' },
                { role: 'counselor', label: 'Counselor', color: 'text-purple-300 hover:bg-purple-500/20' },
              ].map(({ role, label, color }) => (
                <button
                  key={role}
                  type="button"
                  onClick={() => quickFill(role)}
                  className={`text-xs font-semibold px-3 py-2 rounded-lg border border-white/10 transition-colors ${color}`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="text-center text-white/30 text-xs mt-6">
          Smart School Dropout Early Warning System © 2026
        </p>
      </div>
    </div>
  );
};

export default Login;
