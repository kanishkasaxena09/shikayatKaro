import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  Layers,
  CheckCircle,
  Clock,
  TrendingUp,
  FileText,
  ShieldAlert,
  ArrowRight,
  Flame,
} from 'lucide-react';
import HeatmapCanvas from '../components/HeatmapCanvas';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorAlert from '../components/ErrorAlert';

export const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [heatmap, setHeatmap] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sumRes, heatRes] = await Promise.all([
        api.analytics.getDashboardSummary(),
        api.analytics.getHeatmap(selectedCategory ? { category: selectedCategory } : {}),
      ]);
      setSummary(sumRes.data);
      setHeatmap(heatRes.data);
    } catch (err) {
      setError(err.userMessage || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [selectedCategory]);

  if (loading && !summary) {
    return <LoadingSpinner message="Synchronizing campus grievance metrics..." size="large" />;
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Page Title & Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Campus Grievance & Incident Command
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time multi-factor incident aggregation, spatial risk heatmap, and SLA resolution tracking.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Link
            to="/submit"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs shadow-md shadow-indigo-100 transition"
          >
            <FileText className="w-4 h-4" />
            File New Grievance
          </Link>
          <Link
            to="/demo"
            className="inline-flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl border border-amber-300 bg-amber-50 hover:bg-amber-100 text-amber-900 font-semibold text-xs transition"
          >
            <Flame className="w-4 h-4 text-amber-600" />
            Story Simulator
          </Link>
        </div>
      </div>

      <ErrorAlert message={error} onRetry={loadData} />

      {/* KPI Cards Grid */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Total Complaints */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs hover:border-slate-300 transition">
            <div className="flex items-center justify-between text-slate-500 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider">Total Complaints</span>
              <FileText className="w-4 h-4 text-slate-400" />
            </div>
            <div className="text-2xl sm:text-3xl font-extrabold text-slate-900">
              {summary.total_complaints}
            </div>
            <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
              <span>Multilingual student grievances</span>
            </div>
          </div>

          {/* Aggregated Incidents */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs hover:border-slate-300 transition">
            <div className="flex items-center justify-between text-slate-500 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider">Grouped Incidents</span>
              <Layers className="w-4 h-4 text-indigo-500" />
            </div>
            <div className="text-2xl sm:text-3xl font-extrabold text-indigo-600">
              {summary.total_incidents}
            </div>
            <div className="text-[11px] text-slate-500 mt-1 flex items-center justify-between">
              <span>Active: {summary.active_incidents}</span>
              <span className="text-emerald-600 font-semibold">Resolved: {summary.resolved_incidents}</span>
            </div>
          </div>

          {/* Pending Suggestions */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs hover:border-slate-300 transition">
            <div className="flex items-center justify-between text-slate-500 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider">Pending Clusters</span>
              <TrendingUp className="w-4 h-4 text-amber-500" />
            </div>
            <div className="text-2xl sm:text-3xl font-extrabold text-amber-600">
              {summary.pending_suggestions}
            </div>
            <div className="text-[11px] text-amber-700 mt-1">
              {summary.pending_suggestions > 0 ? (
                <Link to="/suggestions" className="hover:underline font-semibold flex items-center gap-1">
                  Requires Admin Confirmation <ArrowRight className="w-3 h-3" />
                </Link>
              ) : (
                'All suggestions confirmed'
              )}
            </div>
          </div>

          {/* Escalations & Critical */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs hover:border-slate-300 transition">
            <div className="flex items-center justify-between text-slate-500 mb-2">
              <span className="text-xs font-bold uppercase tracking-wider">SLA Escalations</span>
              <ShieldAlert className="w-4 h-4 text-rose-500" />
            </div>
            <div className="text-2xl sm:text-3xl font-extrabold text-rose-600">
              {summary.escalated_count}
            </div>
            <div className="text-[11px] text-slate-500 mt-1 flex items-center justify-between">
              <span className="text-rose-700 font-medium">Critical: {summary.critical_incidents}</span>
              <span>Avg: {summary.average_resolution_hours}h</span>
            </div>
          </div>
        </div>
      )}

      {/* Heatmap Section */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            Campus Infrastructure Spatial Risk
          </h2>

          {/* Filter dropdown */}
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-500 font-medium">Filter Category:</label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="text-xs bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 font-medium text-slate-700 shadow-xs focus:ring-1 focus:ring-indigo-500"
            >
              <option value="">All Categories</option>
              <option value="Water & Plumbing">Water & Plumbing</option>
              <option value="Electrical">Electrical</option>
              <option value="Sanitation & Cleanliness">Sanitation & Cleanliness</option>
              <option value="IT & Network">IT & Network</option>
              <option value="Hostel & Mess">Hostel & Mess</option>
              <option value="Safety & Security">Safety & Security</option>
            </select>
          </div>
        </div>

        <HeatmapCanvas data={heatmap} loading={loading} selectedCategory={selectedCategory} />
      </div>

      {/* Workflow Navigation Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        <div className="bg-gradient-to-br from-indigo-900 to-slate-900 rounded-2xl p-5 text-white shadow-md">
          <h3 className="font-bold text-sm text-indigo-200 uppercase tracking-wider mb-1">Step 1: Ingestion</h3>
          <h4 className="text-base font-bold text-white mb-2">Multilingual Grievance Filing</h4>
          <p className="text-xs text-slate-300 leading-relaxed mb-4">
            Citizens file complaints in Hindi, Hinglish, or English with optional zero-knowledge anonymity.
          </p>
          <Link
            to="/submit"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-300 hover:text-white transition"
          >
            Open Submission Portal <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="bg-gradient-to-br from-purple-900 to-slate-900 rounded-2xl p-5 text-white shadow-md">
          <h3 className="font-bold text-sm text-purple-200 uppercase tracking-wider mb-1">Step 2: AI Clustering</h3>
          <h4 className="text-base font-bold text-white mb-2">Multi-Factor Aggregation</h4>
          <p className="text-xs text-slate-300 leading-relaxed mb-4">
            Combines text cosine similarity, spatial hierarchy match, and time proximity into unified suggestions.
          </p>
          <Link
            to="/suggestions"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-purple-300 hover:text-white transition"
          >
            Inspect Pending Suggestions <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="bg-gradient-to-br from-teal-900 to-slate-900 rounded-2xl p-5 text-white shadow-md">
          <h3 className="font-bold text-sm text-teal-200 uppercase tracking-wider mb-1">Step 3: Redressal</h3>
          <h4 className="text-base font-bold text-white mb-2">Resolution Intelligence</h4>
          <p className="text-xs text-slate-300 leading-relaxed mb-4">
            Department handlers resolve incidents guided by past historical cases and automated SLA timers.
          </p>
          <Link
            to="/incidents"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-teal-300 hover:text-white transition"
          >
            Manage Active Incidents <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
