import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LogIn,
  UserPlus,
  Shield,
  Wrench,
  User as UserIcon,
  Sparkles,
  Loader2,
  Lock,
  Mail,
  Compass,
} from 'lucide-react';
import ErrorAlert from '../components/ErrorAlert';

export const Login = () => {
  const { login, register, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/';

  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('complainant');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegister) {
        await register({ email, password, full_name: fullName, role });
      } else {
        await login(email, password);
      }
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.userMessage || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickPersona = async (demoEmail) => {
    setError(null);
    setLoading(true);
    try {
      await login(demoEmail, 'password123');
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.userMessage || 'Quick login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full space-y-6">
        {/* Brand Banner */}
        <div className="text-center space-y-2">
          <div className="inline-flex w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-600 to-indigo-900 items-center justify-center text-white shadow-lg shadow-indigo-200">
            <Compass className="w-7 h-7" />
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            {isRegister ? 'Create an Account' : 'Sign In to Shikayat Karo'}
          </h2>
          <p className="text-xs text-slate-500">
            Intelligent Grievance Redressal and Incident Aggregation Platform
          </p>
        </div>

        {/* 1-Click Fast Demo Persona Login */}
        <div className="bg-slate-900 text-white rounded-2xl p-5 shadow-lg border border-slate-800 space-y-3">
          <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-300 uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5" />
            1-Click Demo Evaluation Accounts:
          </div>

          <div className="space-y-2">
            <button
              type="button"
              onClick={() => handleQuickPersona('admin@demo')}
              className="w-full p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-left flex items-center justify-between text-xs transition"
            >
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-rose-400" />
                <div>
                  <div className="font-bold text-white">Chief Administrator</div>
                  <div className="text-[10px] text-slate-400">Dr. Arvind Sharma (admin@demo)</div>
                </div>
              </div>
              <span className="text-[10px] bg-rose-900/60 text-rose-300 border border-rose-700 px-2 py-0.5 rounded font-bold uppercase">
                Admin
              </span>
            </button>

            <button
              type="button"
              onClick={() => handleQuickPersona('handler@demo')}
              className="w-full p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-left flex items-center justify-between text-xs transition"
            >
              <div className="flex items-center gap-2">
                <Wrench className="w-4 h-4 text-blue-400" />
                <div>
                  <div className="font-bold text-white">Facility Incharge</div>
                  <div className="text-[10px] text-slate-400">Rajesh Kumar (handler@demo)</div>
                </div>
              </div>
              <span className="text-[10px] bg-blue-900/60 text-blue-300 border border-blue-700 px-2 py-0.5 rounded font-bold uppercase">
                Handler
              </span>
            </button>

            <button
              type="button"
              onClick={() => handleQuickPersona('student@demo')}
              className="w-full p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-left flex items-center justify-between text-xs transition"
            >
              <div className="flex items-center gap-2">
                <UserIcon className="w-4 h-4 text-emerald-400" />
                <div>
                  <div className="font-bold text-white">Student Citizen</div>
                  <div className="text-[10px] text-slate-400">Priya Verma (student@demo)</div>
                </div>
              </div>
              <span className="text-[10px] bg-emerald-900/60 text-emerald-300 border border-emerald-700 px-2 py-0.5 rounded font-bold uppercase">
                Student
              </span>
            </button>
          </div>
        </div>

        <ErrorAlert message={error} />

        {/* Form Container */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
          {/* Tab Switcher */}
          <div className="grid grid-cols-2 bg-slate-100 p-1 rounded-xl text-xs font-bold text-center">
            <button
              type="button"
              onClick={() => setIsRegister(false)}
              className={`py-1.5 rounded-lg transition ${
                !isRegister ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => setIsRegister(true)}
              className={`py-1.5 rounded-lg transition ${
                isRegister ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                  placeholder="e.g. Priya Verma"
                  className="w-full text-sm rounded-xl border border-slate-300 p-2.5 focus:border-indigo-500 outline-none"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Email Address
              </label>
              <div className="relative">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="name@domain.edu"
                  className="w-full text-sm rounded-xl border border-slate-300 pl-9 pr-3 p-2.5 focus:border-indigo-500 outline-none"
                />
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Password
              </label>
              <div className="relative">
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="w-full text-sm rounded-xl border border-slate-300 pl-9 pr-3 p-2.5 focus:border-indigo-500 outline-none"
                />
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              </div>
            </div>

            {isRegister && (
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  User Role
                </label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full text-sm rounded-xl border border-slate-300 p-2.5 bg-white focus:border-indigo-500 outline-none"
                >
                  <option value="complainant">Student / Citizen (Complainant)</option>
                  <option value="handler">Facility Handler (Estate/IT/Electric)</option>
                  <option value="admin">Administrator</option>
                </select>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white rounded-xl text-xs font-bold shadow-xs transition flex items-center justify-center gap-1.5"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Processing...
                </>
              ) : isRegister ? (
                <>
                  <UserPlus className="w-4 h-4" />
                  Create Account
                </>
              ) : (
                <>
                  <LogIn className="w-4 h-4" />
                  Sign In
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
