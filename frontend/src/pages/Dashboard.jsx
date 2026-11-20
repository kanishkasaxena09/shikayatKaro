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
  Wrench,
  RotateCcw,
  Users,
  Calendar,
  Building,
  Check,
  X,
} from 'lucide-react';
import HeatmapCanvas from '../components/HeatmapCanvas';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorAlert from '../components/ErrorAlert';

export const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [heatmap, setHeatmap] = useState([]);
  const [recurringIssues, setRecurringIssues] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('');

  // Permanent Fix Modal State
  const [fixModalOpen, setFixModalOpen] = useState(false);
  const [selectedRecurring, setSelectedRecurring] = useState(null);
  const [fixForm, setFixForm] = useState({
    department_id: '',
    due_date_days: 14,
    title: '',
    notes: '',
  });
  const [submittingFix, setSubmittingFix] = useState(false);
  const [fixSuccessMsg, setFixSuccessMsg] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sumRes, heatRes, recurRes, deptsRes] = await Promise.all([
        api.analytics.getDashboardSummary(),
        api.analytics.getHeatmap(selectedCategory ? { category: selectedCategory } : {}),
        api.analytics.getRecurringIssues(),
        api.departments.list().catch(() => ({ data: [] })),
      ]);
      setSummary(sumRes.data);
      setHeatmap(heatRes.data);
      setRecurringIssues(recurRes.data || []);
      setDepartments(deptsRes.data || []);
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

  const handleOpenFixModal = (issue) => {
    setSelectedRecurring(issue);

    // Auto-match department if possible
    const categoryDeptMap = {
      'Water & Plumbing': 'Estate & Maintenance',
      'Sanitation & Cleanliness': 'Estate & Maintenance',
      'Electrical': 'Electrical & Power',
      'IT & Network': 'IT & Networking',
      'Hostel & Mess': 'Hostel & Food Services',
      'Classroom & Infrastructure': 'Estate & Maintenance',
      'Safety & Security': 'Campus Security & Proctorial',
      'Administrative': 'Academic & Student Affairs',
    };
    const targetDeptName = categoryDeptMap[issue.category];
    const matchedDept = departments.find((d) => d.name === targetDeptName) || departments[0];

    setFixForm({
      department_id: matchedDept ? matchedDept.id : '',
      due_date_days: 14,
      title: `Root-cause remediation: Recurring ${issue.category} at ${issue.block_name}`,
      notes: `Overhaul and engineering remediation for recurring incidents (${issue.incident_codes.join(', ')}).`,
    });
    setFixSuccessMsg(null);
    setFixModalOpen(true);
  };

  const handleScheduleFix = async (e) => {
    e.preventDefault();
    if (!selectedRecurring) return;

    try {
      setSubmittingFix(true);
      setError(null);
      const payload = {
        category: selectedRecurring.category,
        location_id: selectedRecurring.block_id,
        department_id: fixForm.department_id ? Number(fixForm.department_id) : undefined,
        due_date_days: Number(fixForm.due_date_days) || 14,
        title: fixForm.title,
        notes: fixForm.notes,
        incident_ids: selectedRecurring.incident_ids,
      };

      const res = await api.analytics.markPermanentFix(payload);
      setFixSuccessMsg(`Permanent remediation task ${res.data.task_code} scheduled successfully!`);
      setFixModalOpen(false);
      // Reload recurring issues
      const updatedRecur = await api.analytics.getRecurringIssues();
      setRecurringIssues(updatedRecur.data || []);
    } catch (err) {
      setError(err.userMessage || 'Failed to schedule permanent fix task');
    } finally {
      setSubmittingFix(false);
    }
  };

  const getCategoryBadgeClass = (category) => {
    switch (category) {
      case 'Water & Plumbing':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'Electrical':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'Sanitation & Cleanliness':
        return 'bg-teal-50 text-teal-700 border-teal-200';
      case 'IT & Network':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      case 'Safety & Security':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

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

      {fixSuccessMsg && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{fixSuccessMsg}</span>
          </div>
          <button
            onClick={() => setFixSuccessMsg(null)}
            className="text-emerald-600 hover:text-emerald-800 text-xs font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* KPI Cards Grid */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
          {/* 1. Total Complaints */}
          <div
            title="Total individual citizen grievances ingested across English, Hindi, and Hinglish."
            className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs hover:border-slate-300 transition flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between text-slate-500 mb-1.5">
                <span className="text-[11px] font-bold uppercase tracking-wider">Total Grievances</span>
                <FileText className="w-4 h-4 text-slate-400" />
              </div>
              <div className="text-2xl font-extrabold text-slate-900">
                {summary.total_complaints}
              </div>
            </div>
            <div className="text-[11px] text-slate-500 mt-2 truncate">
              Individual citizen filings
            </div>
          </div>

          {/* 2. Parent Incidents */}
          <div
            title="Total parent incidents created by aggregating related grievances."
            className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs hover:border-indigo-300 transition flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between text-slate-500 mb-1.5">
                <span className="text-[11px] font-bold uppercase tracking-wider">Parent Incidents</span>
                <Layers className="w-4 h-4 text-indigo-500" />
              </div>
              <div className="text-2xl font-extrabold text-indigo-600">
                {summary.total_incidents}
              </div>
            </div>
            <div className="text-[11px] text-slate-500 mt-2 truncate">
              Aggregated parent dossiers
            </div>
          </div>

          {/* 3. Active vs Resolved */}
          <div
            title="Operational breakdown: active investigations vs closed cases."
            className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs hover:border-slate-300 transition flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between text-slate-500 mb-1.5">
                <span className="text-[11px] font-bold uppercase tracking-wider">Active vs Resolved</span>
                <CheckCircle className="w-4 h-4 text-emerald-500" />
              </div>
              <div className="text-2xl font-extrabold text-slate-900 flex items-baseline gap-1.5">
                <span className="text-amber-600">{summary.active_incidents}</span>
                <span className="text-slate-300 text-lg">/</span>
                <span className="text-emerald-600">{summary.resolved_incidents}</span>
              </div>
            </div>
            <div className="text-[11px] text-slate-500 mt-2 flex items-center justify-between">
              <span className="text-amber-700 font-semibold">{summary.active_incidents} Active</span>
              <span className="text-emerald-600 font-semibold">{summary.resolved_incidents} Done</span>
            </div>
          </div>

          {/* 4. Pending AI Clusters */}
          <div
            title="Candidate incident clusters surfaced by multi-factor AI awaiting human administrator confirmation."
            className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs hover:border-amber-300 transition flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between text-slate-500 mb-1.5">
                <span className="text-[11px] font-bold uppercase tracking-wider">Pending Clusters</span>
                <TrendingUp className="w-4 h-4 text-amber-500" />
              </div>
              <div className="text-2xl font-extrabold text-amber-600">
                {summary.pending_suggestions}
              </div>
            </div>
            <div className="text-[11px] text-amber-700 mt-2 truncate">
              {summary.pending_suggestions > 0 ? (
                <Link to="/suggestions" className="hover:underline font-semibold flex items-center gap-1">
                  Requires Admin Review <ArrowRight className="w-3 h-3" />
                </Link>
              ) : (
                'All suggestions confirmed'
              )}
            </div>
          </div>

          {/* 5. SLA Escalations */}
          <div
            title="Active incidents that breached SLA deadline thresholds and triggered automated escalation tiers."
            className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs hover:border-rose-300 transition flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between text-slate-500 mb-1.5">
                <span className="text-[11px] font-bold uppercase tracking-wider">SLA Escalations</span>
                <ShieldAlert className="w-4 h-4 text-rose-500" />
              </div>
              <div className="text-2xl font-extrabold text-rose-600">
                {summary.escalated_count}
              </div>
            </div>
            <div className="text-[11px] text-rose-700 font-medium mt-2 truncate">
              {summary.critical_incidents} Critical priority
            </div>
          </div>

          {/* 6. Avg Resolution Time */}
          <div
            title="Mean elapsed time from filing to confirmed resolution across all resolved incidents."
            className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs hover:border-slate-300 transition flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between text-slate-500 mb-1.5">
                <span className="text-[11px] font-bold uppercase tracking-wider">Avg Resolution</span>
                <Clock className="w-4 h-4 text-slate-400" />
              </div>
              <div className="text-2xl font-extrabold text-slate-900">
                {summary.average_resolution_hours}<span className="text-sm font-semibold text-slate-500 ml-0.5">h</span>
              </div>
            </div>
            <div className="text-[11px] text-slate-500 mt-2 truncate">
              Filing to resolution closure
            </div>
          </div>
        </div>
      )}

      {/* Recurring Campus Infrastructure Issues Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-6 py-4.5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-gradient-to-r from-slate-50 to-white">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-amber-100 text-amber-700">
              <RotateCcw className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-900 tracking-tight">
                  Recurring Campus Infrastructure Issues
                </h2>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                  {recurringIssues.length} Identified
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Operational heuristic: same category at same block producing &ge; 3 parent incidents within 30 days.
              </p>
            </div>
          </div>
        </div>

        {recurringIssues.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
            <p className="font-semibold text-slate-800">No recurring infrastructure issues detected</p>
            <p className="text-xs text-slate-400 mt-1">
              All campus facilities are currently operating below the 3-incident/30-day recurrence threshold.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/75 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-6 py-3">Location & Block</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Incidents (30d)</th>
                  <th className="px-4 py-3">Total Impact</th>
                  <th className="px-4 py-3">Avg Resolution</th>
                  <th className="px-4 py-3">Last Occurrence</th>
                  <th className="px-6 py-3 text-right">Root-Cause Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {recurringIssues.map((issue) => (
                  <tr key={issue.id} className="hover:bg-slate-50/60 transition">
                    {/* Location */}
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Building className="w-4 h-4 text-slate-400 shrink-0" />
                        <div>
                          <div className="font-bold text-slate-900">{issue.block_name}</div>
                          <div className="text-[11px] text-slate-400">Block ID: #{issue.block_id}</div>
                        </div>
                      </div>
                    </td>

                    {/* Category */}
                    <td className="px-4 py-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold border ${getCategoryBadgeClass(
                          issue.category
                        )}`}
                      >
                        {issue.category}
                      </span>
                    </td>

                    {/* Incident Count & Links */}
                    <td className="px-4 py-4">
                      <div>
                        <span className="font-bold text-rose-600 text-sm">
                          {issue.incident_count}
                        </span>
                        <span className="text-slate-400 text-[11px] ml-1">incidents</span>
                      </div>
                      <div className="flex flex-wrap gap-1 mt-1.5 max-w-[200px]">
                        {issue.incident_codes.map((code, idx) => (
                          <Link
                            key={code}
                            to={`/incidents/${issue.incident_ids[idx]}`}
                            className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-100 hover:bg-indigo-50 text-indigo-700 hover:text-indigo-900 border border-slate-200 transition"
                            title={`Inspect Incident dossier ${code}`}
                          >
                            {code}
                          </Link>
                        ))}
                      </div>
                    </td>

                    {/* Total Affected */}
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-1.5 text-slate-700">
                        <Users className="w-3.5 h-3.5 text-slate-400" />
                        <span className="font-bold text-slate-900">{issue.total_affected}</span>
                        <span className="text-[11px] text-slate-500">citizens</span>
                      </div>
                    </td>

                    {/* Avg Resolution */}
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-1 text-slate-700">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span className="font-semibold">{issue.average_resolution_hours}</span>
                        <span className="text-slate-400 text-[11px]">hours</span>
                      </div>
                    </td>

                    {/* Days Since Last */}
                    <td className="px-4 py-4">
                      <div className="text-slate-700">
                        <span className="font-semibold text-slate-900">
                          {issue.days_since_last_occurrence}
                        </span>
                        <span className="text-slate-500 text-[11px] ml-1">days ago</span>
                      </div>
                    </td>

                    {/* Remediation Action / Badge */}
                    <td className="px-6 py-4 text-right">
                      {issue.has_permanent_fix ? (
                        <div className="inline-flex flex-col items-end gap-1">
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <Check className="w-3.5 h-3.5 text-emerald-600" />
                            Remediation Scheduled
                          </span>
                          {issue.permanent_fix_task && (
                            <span className="text-[10px] text-slate-500 font-mono">
                              {issue.permanent_fix_task.task_code} &bull; Due{' '}
                              {new Date(issue.permanent_fix_task.due_date).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      ) : (
                        <button
                          onClick={() => handleOpenFixModal(issue)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-amber-600 hover:bg-amber-700 text-white shadow-xs transition"
                          title="Schedule a permanent root-cause remediation task assigned to a department"
                        >
                          <Wrench className="w-3.5 h-3.5" />
                          Needs Permanent Fix
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

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

      {/* Needs Permanent Fix Modal */}
      {fixModalOpen && selectedRecurring && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2 text-slate-900 font-bold text-lg">
                <Wrench className="w-5 h-5 text-amber-600" />
                Schedule Permanent Remediation
              </div>
              <button
                onClick={() => setFixModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleScheduleFix} className="space-y-4 mt-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Target Infrastructure Area
                </label>
                <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-800 font-medium flex justify-between items-center">
                  <span>{selectedRecurring.block_name}</span>
                  <span className="font-semibold text-amber-700">{selectedRecurring.category}</span>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Remediation Task Title</label>
                <input
                  type="text"
                  required
                  value={fixForm.title}
                  onChange={(e) => setFixForm({ ...fixForm, title: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:ring-1 focus:ring-indigo-500 text-slate-900 font-medium"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Assigned Department</label>
                  <select
                    value={fixForm.department_id}
                    onChange={(e) => setFixForm({ ...fixForm, department_id: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:ring-1 focus:ring-indigo-500 text-slate-900 font-medium bg-white"
                  >
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Due In (Days)</label>
                  <input
                    type="number"
                    min="1"
                    max="90"
                    required
                    value={fixForm.due_date_days}
                    onChange={(e) => setFixForm({ ...fixForm, due_date_days: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:ring-1 focus:ring-indigo-500 text-slate-900 font-medium"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Engineering Scope & Remediation Notes
                </label>
                <textarea
                  rows={3}
                  value={fixForm.notes}
                  onChange={(e) => setFixForm({ ...fixForm, notes: e.target.value })}
                  placeholder="Outline the permanent root cause fix (e.g. pipe replacement, electrical rewiring)..."
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:ring-1 focus:ring-indigo-500 text-slate-900 font-medium"
                />
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setFixModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-slate-300 text-slate-700 hover:bg-slate-50 font-semibold transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingFix}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white font-semibold shadow-xs transition"
                >
                  <Wrench className="w-3.5 h-3.5" />
                  {submittingFix ? 'Scheduling...' : 'Schedule Task'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
