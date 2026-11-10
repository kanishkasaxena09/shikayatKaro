import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../../api/client';
import {
  FileText,
  Search,
  Shield,
  MapPin,
  TrendingUp,
  Sparkles,
  ArrowRight,
  Globe,
  Lock,
  Layers,
  LogIn,
} from 'lucide-react';
import HeatmapCanvas from '../../components/HeatmapCanvas';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorAlert from '../../components/ErrorAlert';

export const GuestDashboard = () => {
  const navigate = useNavigate();
  const [heatmap, setHeatmap] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [trackId, setTrackId] = useState('');
  const [accessCode, setAccessCode] = useState('');

  useEffect(() => {
    const fetchPublicData = async () => {
      try {
        setLoading(true);
        const [sumRes, heatRes] = await Promise.all([
          api.analytics.getDashboardSummary(),
          api.analytics.getHeatmap(),
        ]);
        setSummary(sumRes.data);
        setHeatmap(heatRes.data || []);
      } catch (err) {
        setError(err.userMessage || 'Failed to load public metrics');
      } finally {
        setLoading(false);
      }
    };
    fetchPublicData();
  }, []);

  const handleTrackSubmit = (e) => {
    e.preventDefault();
    if (!trackId.trim()) return;
    const url = `/track?tracking_id=${encodeURIComponent(trackId.trim())}${
      accessCode ? `&access_code=${encodeURIComponent(accessCode.trim())}` : ''
    }`;
    navigate(url);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
      {/* Hero Welcome Banner */}
      <div className="rounded-3xl bg-gradient-to-br from-slate-950 via-indigo-950 to-slate-900 text-white p-8 sm:p-12 shadow-2xl border border-slate-800 text-center space-y-6">
        <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-semibold">
          <Globe className="w-3.5 h-3.5 text-indigo-400" />
          University Grievance Redressal & Redressal Intelligence
        </div>

        <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-white max-w-3xl mx-auto leading-tight">
          Transforming Individual Grievances into Coordinated Solutions
        </h1>

        <p className="text-sm sm:text-base text-slate-300 max-w-2xl mx-auto leading-relaxed">
          Report facility breakdowns in <strong>Hindi</strong>, <strong>Hinglish</strong>, or <strong>English</strong>. Our transparent AI automatically aggregates related complaints into structured incidents with zero identity leakage for anonymous reporters.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          <Link
            to="/submit"
            className="px-6 py-3.5 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm shadow-lg shadow-indigo-500/30 transition flex items-center gap-2"
          >
            <FileText className="w-4 h-4" />
            File a Grievance Now
          </Link>
          <Link
            to="/login"
            className="px-6 py-3.5 rounded-2xl bg-white/10 hover:bg-white/20 border border-white/20 text-white font-semibold text-sm backdrop-blur-md transition flex items-center gap-2"
          >
            <LogIn className="w-4 h-4" />
            Student / Staff Sign In
          </Link>
        </div>
      </div>

      <ErrorAlert message={error} />

      {/* 2-Column: Quick Anonymous Tracker & Public Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Track by Code Card */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <Search className="w-5 h-5 text-indigo-600" />
            <h3 className="font-bold text-base text-slate-900">Track Any Grievance</h3>
          </div>
          <p className="text-xs text-slate-500">
            No login needed. Track anonymous or public complaints using your sequential Tracking ID:
          </p>

          <form onSubmit={handleTrackSubmit} className="space-y-3">
            <input
              type="text"
              value={trackId}
              onChange={(e) => setTrackId(e.target.value)}
              placeholder="Tracking ID (e.g. CMP-0001)"
              required
              className="w-full text-xs rounded-xl border border-slate-300 p-2.5 font-mono uppercase focus:border-indigo-500 outline-none"
            />
            <input
              type="text"
              value={accessCode}
              onChange={(e) => setAccessCode(e.target.value)}
              placeholder="Access Code (For Anonymous reports)"
              className="w-full text-xs rounded-xl border border-slate-300 p-2.5 font-mono uppercase focus:border-indigo-500 outline-none"
            />
            <button
              type="submit"
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs transition"
            >
              Inspect Live Status
            </button>
          </form>
        </div>

        {/* Pillar 1: Multilingual AI */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-2">
          <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center font-bold">
            <Globe className="w-5 h-5" />
          </div>
          <h4 className="font-bold text-sm text-slate-900">Multilingual Ingestion</h4>
          <p className="text-xs text-slate-500 leading-relaxed">
            Automatic Devanagari Hindi, Romanised Hinglish, and English parsing using semantic embeddings and prototype category classification.
          </p>
        </div>

        {/* Pillar 2: Zero Privacy Leakage */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-2">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold">
            <Shield className="w-5 h-5" />
          </div>
          <h4 className="font-bold text-sm text-slate-900">Strict Privacy Guarantees</h4>
          <p className="text-xs text-slate-500 leading-relaxed">
            Anonymous submissions never store user accounts. Tracking is secured via salted bcrypt access tokens with zero identity leakage.
          </p>
        </div>
      </div>

      {/* Public Heatmap Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-indigo-600" />
              Public Campus Grievance Density Heatmap
            </h2>
            <p className="text-xs text-slate-500">
              Live spatial coordinates across campus academic blocks, hostels, and libraries.
            </p>
          </div>
        </div>

        <HeatmapCanvas data={heatmap} loading={loading} />
      </div>
    </div>
  );
};

export default GuestDashboard;
