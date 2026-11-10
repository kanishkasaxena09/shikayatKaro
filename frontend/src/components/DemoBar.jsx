import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import { Clock, UserCheck, Shield, Wrench, User as UserIcon, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';

export const DemoBar = () => {
  const { user, role, quickSwitchPersona, logout } = useAuth();
  const [clockTime, setClockTime] = useState(null);
  const [offsetHours, setOffsetHours] = useState(0);

  const fetchClock = async () => {
    try {
      const res = await api.analytics.getDashboardSummary();
      if (res.data?.virtual_clock_utc) {
        const d = new Date(res.data.virtual_clock_utc);
        setClockTime(d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
        setOffsetHours(res.data.virtual_offset_hours || 0);
      }
    } catch {
      // ignore in demo bar
    }
  };

  useEffect(() => {
    fetchClock();
    const interval = setInterval(fetchClock, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-slate-900 border-b border-slate-800 text-slate-300 px-4 py-1.5 text-xs">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
        {/* Personas Switcher */}
        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-semibold flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            Switch Demo Persona:
          </span>
          <div className="flex items-center gap-1.5 flex-wrap">
            <button
              onClick={() => quickSwitchPersona('admin@demo')}
              className={`px-2 py-0.5 rounded flex items-center gap-1 font-medium transition ${
                user?.email === 'admin@demo'
                  ? 'bg-rose-600 text-white font-bold'
                  : 'bg-slate-800 hover:bg-slate-700 text-slate-200'
              }`}
              title="Chief Admin (full system oversight & confirmations)"
            >
              <Shield className="w-3 h-3 text-rose-300" />
              Chief Admin
            </button>

            <button
              onClick={() => quickSwitchPersona('handler@demo')}
              className={`px-2 py-0.5 rounded flex items-center gap-1 font-medium transition ${
                user?.email === 'handler@demo'
                  ? 'bg-blue-600 text-white font-bold'
                  : 'bg-slate-800 hover:bg-slate-700 text-slate-200'
              }`}
              title="Estate & Maintenance Facility Incharge"
            >
              <Wrench className="w-3 h-3 text-blue-300" />
              Facility Handler
            </button>

            <button
              onClick={() => quickSwitchPersona('student@demo')}
              className={`px-2 py-0.5 rounded flex items-center gap-1 font-medium transition ${
                user?.email === 'student@demo'
                  ? 'bg-emerald-600 text-white font-bold'
                  : 'bg-slate-800 hover:bg-slate-700 text-slate-200'
              }`}
              title="Student Complainant"
            >
              <UserIcon className="w-3 h-3 text-emerald-300" />
              Student
            </button>

            {user && (
              <button
                onClick={logout}
                className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white"
              >
                Guest View
              </button>
            )}
          </div>
        </div>

        {/* Virtual Clock Display */}
        <div className="flex items-center gap-3">
          <Link
            to="/demo"
            className="flex items-center gap-1.5 text-slate-300 hover:text-indigo-300 transition"
            title="Open Virtual Clock & Story Simulator"
          >
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span>Virtual Clock: <span className="font-mono font-bold text-amber-300">{clockTime || 'Syncing...'}</span></span>
            {offsetHours > 0 && (
              <span className="bg-amber-900/50 text-amber-300 border border-amber-700 px-1 rounded text-[10px] font-bold">
                +{offsetHours}h
              </span>
            )}
          </Link>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400">
            Active: <strong className="text-white">{user ? user.full_name : 'Public Citizen'}</strong>
            {role !== 'guest' && (
              <span className="ml-1 uppercase text-[10px] px-1.5 py-0.2 rounded bg-indigo-900/60 text-indigo-300 border border-indigo-700">
                {role}
              </span>
            )}
          </span>
        </div>
      </div>
    </div>
  );
};

export default DemoBar;
