import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import {
  Shield,
  Layers,
  AlertTriangle,
  Clock,
  TrendingUp,
  FileText,
  Flame,
  Building,
  Sparkles,
  CheckCircle,
  ArrowRight,
  ShieldAlert,
  RotateCcw,
  Wrench,
  X,
} from 'lucide-react';
import HeatmapCanvas from '../../components/HeatmapCanvas';
import StatusBadge from '../../components/StatusBadge';
import PriorityBadge from '../../components/PriorityBadge';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorAlert from '../../components/ErrorAlert';

export const AdminDashboard = () => {
  const { user } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();

  const [summary, setSummary] = useState(null);
  const [heatmap, setHeatmap] = useState([]);
  const [pendingSuggestions, setPendingSuggestions] = useState([]);
  const [criticalIncidents, setCriticalIncidents] = useState([]);
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

  const loadAdminData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sumRes, heatRes, suggRes, incRes, recurRes, deptsRes] = await Promise.all([
        api.analytics.getDashboardSummary(),
        api.analytics.getHeatmap(selectedCategory ? { category: selectedCategory } : {}),
        api.suggestions.list('pending'),
        api.incidents.list({ priority: 'Critical' }),
        api.analytics.getRecurringIssues().catch(() => ({ data: [] })),
        api.departments.list().catch(() => ({ data: [] })),
      ]);
      setSummary(sumRes.data);
      setHeatmap(heatRes.data || []);
      setPendingSuggestions(suggRes.data || []);
      setCriticalIncidents(incRes.data || []);
      setRecurringIssues(recurRes.data || []);
      setDepartments(deptsRes.data || []);
    } catch (err) {
      setError(err.userMessage || 'Failed to load executive command metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAdminData();
    const interval = setInterval(loadAdminData, 25000);
    return () => clearInterval(interval);
  }, [selectedCategory]);

  const handleOpenFixModal = (issue) => {
    setSelectedRecurring(issue);
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
      notes: `Overhaul and engineering remediation for recurring incidents (${issue.incident_codes?.join(', ') || ''}).`,
    });
    setFixModalOpen(true);
  };

  const handleScheduleFix = async (e) => {
    e.preventDefault();
    if (!selectedRecurring) return;

    try {
      setSubmittingFix(true);
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
      addToast(`Permanent remediation task ${res.data.task_code} scheduled successfully!`, 'success');
      setFixModalOpen(false);
      const updatedRecur = await api.analytics.getRecurringIssues();
      setRecurringIssues(updatedRecur.data || []);
    } catch (err) {
      addToast(err.userMessage || 'Failed to schedule permanent fix task', 'error');
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
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  const handleQuickConfirmSuggestion = async (suggId) => {
    try {
      const res = await api.suggestions.confirm(suggId, {});
      addToast(
        `Suggestion confirmed! Parent Incident ${res.data.incident_code} created (Impact: ${res.data.impact_score}).`,
        'success'
      );
      loadAdminData();
      navigate(`/incidents/${res.data.incident_id}`);
    } catch (err) {
      addToast(err.userMessage || 'Failed to confirm suggestion', 'error');
    }
  };

  if (loading && !summary) {
    return <LoadingSpinner message="Loading Chief Executive Command Deck..." size="large" />;
  }

  // Department Load Matrix Data
  const departmentMatrix = [
    { name: 'Estate & Maintenance', code: 'EST-MAINT', active: 3, resolved: 8, compliance: '94%' },
    { name: 'Electrical & Power', code: 'ELEC-PWR', active: 1, resolved: 4, compliance: '91%' },
    { name: 'IT & Networking', code: 'IT-NET', active: 1, resolved: 3, compliance: '98%' },
    { name: 'Hostel & Food Services', code: 'HOSTEL-FOOD', active: 2, resolved: 5, compliance: '89%' },
    { name: 'Campus Security & Proctorial', code: 'SEC-PROC', active: 0, resolved: 2, compliance: '100%' },
    { name: 'Academic & Student Affairs', code: 'ACAD-STU', active: 0, resolved: 2, compliance: '96%' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Executive Header Banner */}
      <div className="rounded-3xl bg-gradient-to-r from-slate-950 via-slate-900 to-indigo-950 text-white p-6 sm:p-8 shadow-xl border border-slate-800">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="px-3 py-1 rounded-full bg-rose-500/20 text-rose-300 border border-rose-400/30 text-xs font-semibold flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-rose-400" />
                Chief Executive Oversight
              </span>
              <span className="bg-emerald-950/80 text-emerald-400 border border-emerald-800 px-2.5 py-0.5 rounded-full text-xs font-semibold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                SLA Scheduler Active (60s)
              </span>
            </div>
            <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
              Dr. Arvind Sharma (Chief Administrator)
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
              Campus-wide grievance aggregation, multi-factor incident confirmations, cross-departmental SLA compliance, and spatial infrastructure risk analytics.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/demo"
              className="px-4 py-2.5 rounded-xl border border-amber-400/50 bg-amber-500/20 text-amber-200 hover:bg-amber-500/30 text-xs font-semibold transition flex items-center gap-1.5 shadow-sm"
            >
              <Flame className="w-4 h-4 text-amber-400" />
              SLA Time Machine & Simulator
            </Link>
            <Link
              to="/suggestions"
              className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-md transition flex items-center gap-1.5"
            >
              <Layers className="w-4 h-4" />
              AI Suggestions ({pendingSuggestions.length})
            </Link>
          </div>
        </div>
      </div>

      <ErrorAlert message={error} onRetry={loadAdminData} />

      {/* Executive KPI Grid */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              Total Ingested
            </span>
            <div className="text-3xl font-extrabold text-slate-900">{summary.total_complaints}</div>
            <span className="text-[11px] text-slate-500 mt-1 block">Multilingual Grievances</span>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              Parent Incidents
            </span>
            <div className="text-3xl font-extrabold text-indigo-700">{summary.total_incidents}</div>
            <span className="text-[11px] text-slate-500 mt-1 block">
              {summary.active_incidents} Active • {summary.resolved_incidents} Resolved
            </span>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              Pending AI Clusters
            </span>
            <div className="text-3xl font-extrabold text-amber-600">
              {summary.pending_suggestions}
            </div>
            <span className="text-[11px] text-amber-700 font-semibold mt-1 block">
              Awaiting Admin Approval
            </span>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              SLA Escalations
            </span>
            <div className="text-3xl font-extrabold text-rose-600">{summary.escalated_count}</div>
            <span className="text-[11px] text-rose-700 font-medium mt-1 block">
              Tier 1, 2, 3 Overdue
            </span>
          </div>

          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              Avg Resolution Time
            </span>
            <div className="text-3xl font-extrabold text-slate-900">
              {summary.average_resolution_hours}h
            </div>
            <span className="text-[11px] text-emerald-600 font-semibold mt-1 block">
              Campus Target: &lt; 24h
            </span>
          </div>
        </div>
      )}

      {/* Actionable AI Cluster Confirmation Banner (If suggestions pending) */}
      {pendingSuggestions.length > 0 && (
        <div className="bg-amber-50/70 rounded-3xl border border-amber-300 p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <span className="w-3 h-3 rounded-full bg-amber-500 animate-ping"></span>
              <h2 className="text-base font-extrabold text-amber-950 tracking-tight">
                AI Multi-Factor Grievance Clusters Requiring Confirmation ({pendingSuggestions.length})
              </h2>
            </div>
            <Link
              to="/suggestions"
              className="text-xs font-bold text-amber-900 hover:text-amber-700 flex items-center gap-1"
            >
              Review all clusters <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-3">
            {pendingSuggestions.slice(0, 2).map((sugg) => (
              <div
                key={sugg.id}
                className="bg-white rounded-2xl p-4 border border-amber-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded">
                      Cluster #{sugg.id}
                    </span>
                    <span className="text-xs font-semibold text-slate-900">
                      {sugg.complaint_ids.length} Grievances Grouped
                    </span>
                    <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                      {(sugg.confidence * 100).toFixed(0)}% Match Confidence
                    </span>
                    {sugg.engine && (
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                        sugg.engine === 'neural'
                          ? 'bg-purple-50 text-purple-700 border-purple-200'
                          : 'bg-amber-50 text-amber-700 border-amber-200'
                      }`}>
                        {sugg.engine === 'neural' ? 'Engine: Neural' : 'Engine: Fallback'}
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-slate-600">
                    Reasons: {sugg.reasons?.join(' • ')}
                  </p>

                  <div className="text-[11px] text-slate-400">
                    Complaints: {sugg.complaints?.map((c) => c.tracking_id).join(', ')}
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end md:self-center">
                  <button
                    onClick={() => handleQuickConfirmSuggestion(sugg.id)}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs transition flex items-center gap-1.5"
                  >
                    <CheckCircle className="w-4 h-4" />
                    Approve & Escalate Incident
                  </button>
                  <Link
                    to="/suggestions"
                    className="px-3 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-xl text-xs font-medium"
                  >
                    Inspect
                  </Link>
                </div>
              </div>
            ))}
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
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Building className="w-4 h-4 text-slate-400 shrink-0" />
                        <div>
                          <div className="font-bold text-slate-900">{issue.block_name}</div>
                          <div className="text-[11px] text-slate-400">Block ID: #{issue.block_id}</div>
                        </div>
                      </div>
                    </td>

                    <td className="px-4 py-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold border ${getCategoryBadgeClass(
                          issue.category
                        )}`}
                      >
                        {issue.category}
                      </span>
                    </td>

                    <td className="px-4 py-4">
                      <div>
                        <span className="font-bold text-rose-600 text-sm">
                          {issue.incident_count}
                        </span>
                        <span className="text-slate-400 text-[11px] ml-1">incidents</span>
                      </div>
                      <div className="flex flex-wrap gap-1 mt-1.5 max-w-[200px]">
                        {issue.incident_codes?.map((code, idx) => (
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

                    <td className="px-4 py-4">
                      <div className="font-bold text-slate-900">
                        {issue.total_impact || issue.incident_count * 15}
                      </div>
                      <div className="text-[11px] text-slate-400">Cumulative score</div>
                    </td>

                    <td className="px-4 py-4">
                      <div className="font-semibold text-slate-800">
                        {issue.average_resolution_hours ? `${issue.average_resolution_hours}h` : 'N/A'}
                      </div>
                      <div className="text-[11px] text-slate-400">Mean time to resolve</div>
                    </td>

                    <td className="px-4 py-4">
                      <div className="text-slate-700 font-medium">
                        {issue.days_since_last_incident === 0
                          ? 'Today'
                          : `${issue.days_since_last_incident}d ago`}
                      </div>
                    </td>

                    <td className="px-6 py-4 text-right">
                      {issue.has_permanent_fix ? (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-semibold">
                          <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                          Remediation Scheduled ({issue.permanent_fix_task_code})
                        </span>
                      ) : (
                        <button
                          onClick={() => handleOpenFixModal(issue)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-semibold text-xs transition shadow-xs"
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

      {/* Spatial Campus Heatmap Section */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-indigo-600" />
              Campus Infrastructure Spatial Risk Heatmap
            </h2>
            <p className="text-xs text-slate-500">
              Interactive 2D spatial coordinate mapping across blocks, floors, and facilities.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="text-xs bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 font-medium text-slate-700 shadow-xs"
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

      {/* Department Workload & SLA Matrix */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="font-bold text-sm text-slate-900 flex items-center gap-2">
              <Building className="w-4 h-4 text-indigo-600" />
              Department Workload & SLA Performance Leaderboard
            </h3>
            <p className="text-xs text-slate-400">
              Cross-departmental dispatch, open incident load, and compliance rates.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase tracking-wider">
                <th className="pb-2">Department</th>
                <th className="pb-2">Code</th>
                <th className="pb-2">Active Incidents</th>
                <th className="pb-2">Resolved Incidents</th>
                <th className="pb-2">SLA Compliance Rate</th>
                <th className="pb-2 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {departmentMatrix.map((dept, i) => (
                <tr key={i} className="hover:bg-slate-50 transition">
                  <td className="py-3 font-bold text-slate-900">{dept.name}</td>
                  <td className="py-3 font-mono text-slate-500">{dept.code}</td>
                  <td className="py-3">
                    <span className="font-bold text-indigo-700">{dept.active}</span>
                  </td>
                  <td className="py-3">
                    <span className="font-bold text-emerald-700">{dept.resolved}</span>
                  </td>
                  <td className="py-3 font-semibold text-slate-800">{dept.compliance}</td>
                  <td className="py-3 text-right">
                    <Link
                      to={`/incidents?department_id=${i + 1}`}
                      className="text-xs font-semibold text-indigo-600 hover:text-indigo-800"
                    >
                      View Incidents →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
                  Engineering Notes & Scope
                </label>
                <textarea
                  rows="3"
                  value={fixForm.notes}
                  onChange={(e) => setFixForm({ ...fixForm, notes: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 focus:ring-1 focus:ring-indigo-500 text-slate-900 font-medium resize-none"
                  placeholder="Root cause diagnosis, required parts replacement, infrastructure vendor contact..."
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setFixModalOpen(false)}
                  className="px-4 py-2 border border-slate-300 rounded-xl text-slate-700 hover:bg-slate-50 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingFix}
                  className="px-4 py-2 bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white font-semibold rounded-xl transition flex items-center gap-1.5 shadow-xs"
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

export default AdminDashboard;
