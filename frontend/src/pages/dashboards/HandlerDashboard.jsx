import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import {
  Wrench,
  AlertTriangle,
  Clock,
  CheckCircle,
  Building,
  Layers,
  MapPin,
  TrendingUp,
  Sparkles,
  ArrowRight,
  Filter,
  Check,
  Send,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import StatusBadge from '../../components/StatusBadge';
import PriorityBadge from '../../components/PriorityBadge';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorAlert from '../../components/ErrorAlert';

export const HandlerDashboard = () => {
  const { user } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();

  const [incidents, setIncidents] = useState([]);
  const [departmentSuggestions, setDepartmentSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Active status filter in handler queue
  const [activeQueueTab, setActiveQueueTab] = useState('all'); // all | assigned | in_progress | escalated | resolved

  // Quick Resolution Modal state
  const [activeIncidentForResolution, setActiveIncidentForResolution] = useState(null);
  const [targetStatus, setTargetStatus] = useState('Resolved');
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [statusRemarks, setStatusRemarks] = useState('');
  const [updatingStatus, setUpdatingStatus] = useState(false);

  const fetchHandlerData = async () => {
    try {
      setLoading(true);
      setError(null);
      // Fetch incidents
      const [incRes, suggRes] = await Promise.all([
        api.incidents.list({}),
        api.suggestions.list('pending'),
      ]);
      setIncidents(incRes.data || []);
      setDepartmentSuggestions(suggRes.data || []);
    } catch (err) {
      setError(err.userMessage || 'Failed to load department work orders');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHandlerData();
  }, []);

  // Filter incidents for this handler
  const myDeptName = 'Estate & Maintenance'; // Demo handler Rajesh Kumar's department
  const myDeptIncidents = incidents.filter(
    (inc) => !inc.department_name || inc.department_name === myDeptName
  );

  const assignedCount = myDeptIncidents.filter((i) =>
    ['Assigned', 'Submitted', 'AI Analysed'].includes(i.status)
  ).length;

  const inProgressCount = myDeptIncidents.filter((i) =>
    ['Under Investigation', 'In Progress', 'Awaiting Info'].includes(i.status)
  ).length;

  const escalatedCount = myDeptIncidents.filter((i) => i.escalation_level > 0).length;

  const resolvedCount = myDeptIncidents.filter((i) =>
    ['Resolved', 'Closed'].includes(i.status)
  ).length;

  // Filtered queue based on active tab
  const displayedIncidents = myDeptIncidents.filter((inc) => {
    if (activeQueueTab === 'assigned')
      return ['Assigned', 'Submitted', 'AI Analysed'].includes(inc.status);
    if (activeQueueTab === 'in_progress')
      return ['Under Investigation', 'In Progress', 'Awaiting Info'].includes(inc.status);
    if (activeQueueTab === 'escalated') return inc.escalation_level > 0;
    if (activeQueueTab === 'resolved') return ['Resolved', 'Closed'].includes(inc.status);
    return true;
  });

  const openResolutionModal = (inc) => {
    setActiveIncidentForResolution(inc);
    setTargetStatus('Resolved');
    // Pre-fill suggested resolution notes if available
    setResolutionNotes(
      'Inspected site, deployed technician team, repaired damaged infrastructure fixture and validated continuous line pressure/stability with zero leakage.'
    );
    setStatusRemarks('Corrective repair completed and verified by facility handler.');
  };

  const handleQuickStatusSubmit = async (e) => {
    e.preventDefault();
    if (!activeIncidentForResolution) return;

    if (['Resolved', 'Closed'].includes(targetStatus) && !resolutionNotes.trim()) {
      addToast('Resolution notes are mandatory when marking an incident resolved.', 'error');
      return;
    }

    try {
      setUpdatingStatus(true);
      await api.incidents.updateStatus(
        activeIncidentForResolution.id,
        targetStatus,
        resolutionNotes,
        statusRemarks
      );
      addToast(
        `Incident ${activeIncidentForResolution.code} updated to ${targetStatus}!`,
        'success'
      );
      setActiveIncidentForResolution(null);
      fetchHandlerData();
    } catch (err) {
      addToast(err.userMessage || 'Failed to update work order status', 'error');
    } finally {
      setUpdatingStatus(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Handler Operations Deck Banner */}
      <div className="rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-900 text-white p-6 sm:p-8 shadow-xl border border-slate-800">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 border border-blue-400/30 text-xs font-semibold flex items-center gap-1.5">
                <Wrench className="w-3.5 h-3.5 text-blue-400" />
                Department Operations Deck
              </span>
              <span className="bg-slate-800 text-slate-300 px-2.5 py-1 rounded-full text-xs font-mono font-bold">
                {myDeptName}
              </span>
            </div>
            <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
              Facility Incharge: {user?.full_name || 'Rajesh Kumar'}
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
              Prioritize field work orders, inspect automated AI cluster suggestions, and resolve grievances with AI Resolution Intelligence.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              to="/incidents"
              className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-md transition flex items-center gap-1.5"
            >
              <Building className="w-4 h-4" />
              Full Campus Backlog
            </Link>
            <Link
              to="/suggestions"
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold transition flex items-center gap-1.5"
            >
              <Layers className="w-4 h-4 text-amber-400" />
              Pending Clusters ({departmentSuggestions.length})
            </Link>
          </div>
        </div>
      </div>

      <ErrorAlert message={error} onRetry={fetchHandlerData} />

      {/* Handler KPI Counters */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          onClick={() => setActiveQueueTab('assigned')}
          className={`cursor-pointer bg-white rounded-2xl p-5 border shadow-xs transition ${
            activeQueueTab === 'assigned'
              ? 'border-blue-500 ring-2 ring-blue-100'
              : 'border-slate-200 hover:border-blue-300'
          }`}
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">New Assigned</span>
            <AlertCircle className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-3xl font-extrabold text-blue-700">{assignedCount}</div>
          <div className="text-[11px] text-slate-500 mt-1">Ready for field investigation</div>
        </div>

        <div
          onClick={() => setActiveQueueTab('in_progress')}
          className={`cursor-pointer bg-white rounded-2xl p-5 border shadow-xs transition ${
            activeQueueTab === 'in_progress'
              ? 'border-amber-500 ring-2 ring-amber-100'
              : 'border-slate-200 hover:border-amber-300'
          }`}
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">In Progress</span>
            <Clock className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-3xl font-extrabold text-amber-600">{inProgressCount}</div>
          <div className="text-[11px] text-slate-500 mt-1">Technicians deployed on site</div>
        </div>

        <div
          onClick={() => setActiveQueueTab('escalated')}
          className={`cursor-pointer bg-white rounded-2xl p-5 border shadow-xs transition ${
            activeQueueTab === 'escalated'
              ? 'border-rose-500 ring-2 ring-rose-100'
              : 'border-slate-200 hover:border-rose-300'
          }`}
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">SLA Overdue / Escalated</span>
            <AlertTriangle className="w-4 h-4 text-rose-500" />
          </div>
          <div className="text-3xl font-extrabold text-rose-600">{escalatedCount}</div>
          <div className="text-[11px] text-rose-600 font-semibold mt-1">Exceeded target SLA timeline</div>
        </div>

        <div
          onClick={() => setActiveQueueTab('resolved')}
          className={`cursor-pointer bg-white rounded-2xl p-5 border shadow-xs transition ${
            activeQueueTab === 'resolved'
              ? 'border-emerald-500 ring-2 ring-emerald-100'
              : 'border-slate-200 hover:border-emerald-300'
          }`}
        >
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-bold uppercase tracking-wider">Completed / Resolved</span>
            <CheckCircle className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-600">{resolvedCount}</div>
          <div className="text-[11px] text-emerald-700 font-semibold mt-1">Verified with resolution notes</div>
        </div>
      </div>

      {/* Main Work Orders Queue Section */}
      <div className="space-y-4">
        {/* Queue Filter Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-3">
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <Building className="w-5 h-5 text-indigo-600" />
              Department Work Orders Queue
            </h2>
            <p className="text-xs text-slate-500">
              Showing incidents routed to <strong>{myDeptName}</strong>
            </p>
          </div>

          {/* Queue Tab Buttons */}
          <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
            {[
              { id: 'all', label: `All (${myDeptIncidents.length})` },
              { id: 'assigned', label: `Assigned (${assignedCount})` },
              { id: 'in_progress', label: `In Progress (${inProgressCount})` },
              { id: 'escalated', label: `Overdue (${escalatedCount})` },
              { id: 'resolved', label: `Resolved (${resolvedCount})` },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveQueueTab(tab.id)}
                className={`px-3 py-1.5 rounded-lg transition ${
                  activeQueueTab === tab.id
                    ? 'bg-white text-indigo-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <LoadingSpinner message="Loading work orders queue..." />
        ) : displayedIncidents.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-500">
            <CheckCircle className="w-10 h-10 text-emerald-400 mx-auto mb-2" />
            <h3 className="font-bold text-slate-700 text-sm">No Work Orders In This Queue</h3>
            <p className="text-xs text-slate-400 mt-1">
              Select "All" or check other statuses to view active incidents.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {displayedIncidents.map((inc) => (
              <div
                key={inc.id}
                className={`bg-white rounded-2xl border p-5 shadow-xs transition hover:shadow-md flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                  inc.escalation_level > 0 ? 'border-rose-300 bg-rose-50/20' : 'border-slate-200'
                }`}
              >
                {/* Left Detail */}
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-xs font-bold bg-slate-900 text-white px-2 py-0.5 rounded">
                      {inc.code}
                    </span>
                    <StatusBadge status={inc.status} />
                    <PriorityBadge priority={inc.priority} />
                    {inc.escalation_level > 0 && (
                      <span className="bg-rose-600 text-white px-2 py-0.5 rounded-full text-[10px] font-bold">
                        SLA Escalation Tier {inc.escalation_level}
                      </span>
                    )}
                    <span className="text-xs text-slate-400">•</span>
                    <span className="text-xs font-semibold text-slate-600">{inc.category}</span>
                  </div>

                  <h3 className="text-base font-bold text-slate-900">
                    <Link to={`/incidents/${inc.id}`} className="hover:text-indigo-600">
                      {inc.title}
                    </Link>
                  </h3>

                  <div className="flex items-center gap-4 text-xs text-slate-500 flex-wrap">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      {inc.location_name || 'Campus Wide'}
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Layers className="w-3.5 h-3.5 text-indigo-500" />
                      <strong>{inc.linked_complaints_count}</strong> grievances grouped
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      Pending: {inc.pending_hours}h
                    </span>
                  </div>
                </div>

                {/* Right Action: Quick Status / Resolve Button */}
                <div className="flex items-center gap-3 self-end md:self-center">
                  <div className="text-right mr-2 hidden sm:block">
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">
                      Impact
                    </span>
                    <span className="font-extrabold text-sm text-slate-900">
                      {inc.impact_score}/100
                    </span>
                  </div>

                  {['Resolved', 'Closed'].includes(inc.status) ? (
                    <Link
                      to={`/incidents/${inc.id}`}
                      className="px-4 py-2 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-xl text-xs font-semibold hover:bg-emerald-100 transition flex items-center gap-1.5"
                    >
                      <Check className="w-4 h-4" />
                      View Resolution
                    </Link>
                  ) : (
                    <button
                      onClick={() => openResolutionModal(inc)}
                      className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs transition flex items-center gap-1.5"
                    >
                      <Wrench className="w-4 h-4" />
                      Update / Resolve Work Order
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Work Order Status & Resolution Modal */}
      {activeIncidentForResolution && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <form
            onSubmit={handleQuickStatusSubmit}
            className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4"
          >
            <div className="flex items-start justify-between border-b border-slate-100 pb-3">
              <div>
                <span className="text-[10px] font-mono font-bold text-slate-500">
                  {activeIncidentForResolution.code}
                </span>
                <h3 className="text-base font-bold text-slate-900">
                  Field Redressal: {activeIncidentForResolution.title}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setActiveIncidentForResolution(null)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Update Status To:
              </label>
              <select
                value={targetStatus}
                onChange={(e) => setTargetStatus(e.target.value)}
                className="w-full text-sm rounded-xl border border-slate-300 p-2.5 bg-white font-medium focus:border-indigo-500 outline-none"
              >
                <option value="Under Investigation">Under Investigation</option>
                <option value="In Progress">In Progress</option>
                <option value="Awaiting Info">Awaiting Info (Pauses Clock)</option>
                <option value="Resolved">Resolved (Closes Ticket with Notes)</option>
                <option value="Closed">Closed</option>
              </select>
            </div>

            {/* Resolution Notes with AI suggestion helper */}
            {['Resolved', 'Closed'].includes(targetStatus) && (
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Corrective Resolution Notes <span className="text-rose-500">*</span>
                  </label>
                  <span className="text-[11px] text-indigo-600 font-medium flex items-center gap-1">
                    <Sparkles className="w-3 h-3" /> AI Assisted
                  </span>
                </div>
                <textarea
                  rows={3}
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  placeholder="Detail parts replaced, repairs completed, or technician verification steps..."
                  className="w-full text-xs rounded-xl border border-slate-300 p-2.5 focus:border-indigo-500 outline-none"
                  required
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Internal Remarks / Dispatch Notes
              </label>
              <input
                type="text"
                value={statusRemarks}
                onChange={(e) => setStatusRemarks(e.target.value)}
                placeholder="e.g. Dispatched plumbing unit #2..."
                className="w-full text-xs rounded-xl border border-slate-300 p-2.5 focus:border-indigo-500 outline-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setActiveIncidentForResolution(null)}
                className="px-4 py-2 border border-slate-300 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={updatingStatus}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs"
              >
                {updatingStatus ? 'Updating...' : 'Save & Propagate Status'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default HandlerDashboard;
