import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import {
  Layers,
  Clock,
  MapPin,
  Building,
  TrendingUp,
  Sparkles,
  History,
  CheckCircle,
  AlertTriangle,
  ArrowLeft,
  ChevronDown,
  ChevronUp,
  Shield,
  Send,
  FileCheck,
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import PriorityBadge from '../components/PriorityBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorAlert from '../components/ErrorAlert';

export const IncidentDetail = () => {
  const { id } = useParams();
  const { role, user } = useAuth();
  const { addToast } = useToast();

  const [incident, setIncident] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Status Update Modal state
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [newStatus, setNewStatus] = useState('');
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [statusRemarks, setStatusRemarks] = useState('');
  const [updatingStatus, setUpdatingStatus] = useState(false);

  // Assign Modal state
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [selectedDeptId, setSelectedDeptId] = useState(1);
  const [assignRemarks, setAssignRemarks] = useState('');
  const [assigning, setAssigning] = useState(false);

  // Department choices
  const departments = [
    { id: 1, name: 'Estate & Maintenance' },
    { id: 2, name: 'Electrical & Power' },
    { id: 3, name: 'IT & Networking' },
    { id: 4, name: 'Hostel & Food Services' },
    { id: 5, name: 'Campus Security & Proctorial' },
    { id: 6, name: 'Academic & Student Affairs' },
  ];

  const fetchDetail = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.incidents.getById(id);
      setIncident(res.data);
      setNewStatus(res.data.status);
      if (res.data.department_id) setSelectedDeptId(res.data.department_id);
    } catch (err) {
      setError(err.userMessage || 'Failed to load incident details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [id]);

  const handleUpdateStatus = async (e) => {
    e.preventDefault();
    if (['Resolved', 'Closed'].includes(newStatus) && !resolutionNotes.trim()) {
      addToast('Resolution notes are strictly required when resolving or closing an incident.', 'error');
      return;
    }

    try {
      setUpdatingStatus(true);
      await api.incidents.updateStatus(id, newStatus, resolutionNotes, statusRemarks);
      addToast(`Incident status updated to ${newStatus}.`, 'success');
      setShowStatusModal(false);
      fetchDetail();
    } catch (err) {
      addToast(err.userMessage || 'Failed to update status', 'error');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handleAssignDepartment = async (e) => {
    e.preventDefault();
    try {
      setAssigning(true);
      await api.incidents.assign(id, selectedDeptId, assignRemarks);
      addToast('Department assigned successfully.', 'success');
      setShowAssignModal(false);
      fetchDetail();
    } catch (err) {
      addToast(err.userMessage || 'Failed to assign department', 'error');
    } finally {
      setAssigning(false);
    }
  };

  if (loading && !incident) {
    return <LoadingSpinner message="Retrieving incident dossier and resolution intel..." size="large" />;
  }

  if (error || !incident) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <ErrorAlert message={error || 'Incident not found'} onRetry={fetchDetail} />
        <Link to="/incidents" className="text-xs font-semibold text-indigo-600 flex items-center gap-1 mt-4">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Incidents Backlog
        </Link>
      </div>
    );
  }

  const breakdown = incident.impact_breakdown?.breakdown || {};

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Breadcrumb */}
      <div>
        <Link
          to="/incidents"
          className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Incidents Backlog
        </Link>
      </div>

      {/* Main Header Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-sm font-bold bg-slate-900 text-white px-2.5 py-1 rounded-lg">
                {incident.code}
              </span>
              <StatusBadge status={incident.status} />
              <PriorityBadge priority={incident.priority} />
              {incident.escalation_level > 0 && (
                <span className="bg-rose-100 text-rose-800 border border-rose-200 px-2.5 py-0.5 rounded-full text-xs font-bold">
                  SLA Escalated (Tier {incident.escalation_level})
                </span>
              )}
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {incident.title}
            </h1>

            <div className="flex items-center gap-4 text-xs text-slate-500 flex-wrap pt-1">
              <span className="flex items-center gap-1.5 font-medium text-slate-700">
                <Building className="w-4 h-4 text-indigo-600" />
                {incident.department_name || 'Unassigned'}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1.5 font-medium text-slate-700">
                <MapPin className="w-4 h-4 text-indigo-600" />
                {incident.location_name || 'Campus Wide'}
              </span>
              <span>•</span>
              <span>Category: <strong>{incident.category}</strong></span>
              <span>•</span>
              <span>Filed: {new Date(incident.created_at).toLocaleString()}</span>
            </div>
          </div>

          {/* Action Buttons for Handlers & Admins */}
          {(role === 'admin' || role === 'handler') && (
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowAssignModal(true)}
                className="px-4 py-2.5 rounded-xl border border-slate-300 hover:bg-slate-50 font-semibold text-xs text-slate-700 transition"
              >
                Assign Department
              </button>

              <button
                onClick={() => setShowStatusModal(true)}
                className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 font-semibold text-xs text-white shadow-xs transition"
              >
                Update Workflow Status
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Grid: Left Column (Linked complaints + Timeline), Right Column (Impact breakdown + Resolution Intel) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 Cols wide) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Linked Citizen Complaints */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <h3 className="font-bold text-sm text-slate-900 flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-600" />
                Aggregated Citizen Complaints ({incident.linked_complaints?.length || 0})
              </h3>
              <span className="text-xs text-slate-400">
                AI Relatedness Confidence: {(incident.relatedness_confidence * 100).toFixed(0)}%
              </span>
            </div>

            <div className="p-5 divide-y divide-slate-100 space-y-4">
              {incident.linked_complaints?.map((cmp) => (
                <div key={cmp.id} className="pt-4 first:pt-0 space-y-2">
                  <div className="flex items-center justify-between flex-wrap gap-2 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-slate-900">{cmp.tracking_id}</span>
                      <PriorityBadge priority={cmp.priority} />
                      <span className="bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase">
                        {cmp.original_language}
                      </span>
                      {cmp.is_anonymous && (
                        <span className="text-slate-500 flex items-center gap-1 text-[11px]">
                          <Shield className="w-3 h-3 text-slate-400" /> Anonymous
                        </span>
                      )}
                    </div>
                    <span className="text-slate-400 text-[11px]">
                      {new Date(cmp.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>

                  <p className="text-sm text-slate-800 bg-slate-50 p-3 rounded-xl border border-slate-100">
                    {cmp.text}
                  </p>

                  <div className="flex items-center gap-3 text-xs text-slate-500">
                    <span>Location: {cmp.location_name || 'Campus'}</span>
                    <span>•</span>
                    <span>{cmp.affected_count} affected users</span>
                    {cmp.complainant && (
                      <>
                        <span>•</span>
                        <span>Complainant: {cmp.complainant.full_name}</span>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Resolution Notes Banner (if resolved) */}
          {incident.resolution_notes && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-5 space-y-2">
              <h3 className="font-bold text-sm text-emerald-900 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-600" />
                Verified Resolution Notes
              </h3>
              <p className="text-sm text-emerald-800 whitespace-pre-wrap">
                {incident.resolution_notes}
              </p>
              {incident.resolved_at && (
                <span className="text-[11px] text-emerald-700 block">
                  Resolved on: {new Date(incident.resolved_at).toLocaleString()}
                </span>
              )}
            </div>
          )}

          {/* Audit Timeline */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4">
            <h3 className="font-bold text-sm text-slate-900 flex items-center gap-2">
              <History className="w-4 h-4 text-slate-500" />
              Incident Audit Timeline & Governance Log
            </h3>

            <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
              {incident.timeline?.map((event, idx) => (
                <div key={idx} className="relative text-xs space-y-1">
                  <div className="absolute -left-[22px] top-1 w-3 h-3 rounded-full bg-indigo-600 ring-4 ring-white" />
                  <div className="flex items-center justify-between text-slate-500">
                    <span className="font-bold text-slate-800 uppercase tracking-wider text-[10px]">
                      {event.event_type}
                    </span>
                    <span>{new Date(event.timestamp).toLocaleString()}</span>
                  </div>
                  <p className="text-sm text-slate-700">{event.remarks}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column (Impact breakdown + Resolution intelligence) */}
        <div className="space-y-6">
          {/* Transparent Impact Score Breakdown Card */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-sm text-slate-900 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-rose-500" />
                Transparent Impact Score
              </h3>
              <span className="text-lg font-extrabold text-slate-900">
                {incident.impact_score}<span className="text-xs font-medium text-slate-400">/100</span>
              </span>
            </div>

            <p className="text-[11px] text-slate-500">
              Calculated using the verified transparent weighted formula:
              <br />
              <code className="text-indigo-600 text-[10px]">
                0.35·Severity + 0.25·Urgency + 0.25·Affected + 0.15·Duration
              </code>
            </p>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Severity (35%):</span>
                <span className="font-bold text-slate-800">{breakdown.severity || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Urgency (25%):</span>
                <span className="font-bold text-slate-800">{breakdown.urgency || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Affected Occupants (25%):</span>
                <span className="font-bold text-slate-800">
                  {breakdown.affected || 0} ({breakdown.raw_affected_count || 1} people)
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Duration Open (15%):</span>
                <span className="font-bold text-slate-800">
                  {breakdown.duration || 0} ({breakdown.raw_hours_open || 0}h)
                </span>
              </div>
            </div>
          </div>

          {/* AI Resolution Intelligence Widget */}
          <div className="bg-gradient-to-br from-indigo-900 to-slate-900 rounded-2xl p-5 text-white shadow-lg space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-sm text-indigo-200 flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                AI Resolution Intelligence
              </h3>
              <span className="text-[11px] bg-indigo-800/80 px-2 py-0.5 rounded text-indigo-200">
                Top Matches
              </span>
            </div>

            <p className="text-xs text-slate-300">
              Historically resolved incidents with high semantic & equipment similarity:
            </p>

            {incident.similar_resolved?.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No past resolved matches found.</p>
            ) : (
              <div className="space-y-3">
                {incident.similar_resolved?.map((sim, i) => (
                  <div key={i} className="bg-slate-800/80 border border-slate-700/80 p-3 rounded-xl space-y-1.5 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-indigo-300">{sim.incident_code}</span>
                      <span className="text-emerald-400 font-bold">
                        {(sim.similarity * 100).toFixed(0)}% Match
                      </span>
                    </div>

                    <div className="font-semibold text-slate-200 text-xs">{sim.title}</div>

                    <div className="bg-slate-900/60 p-2 rounded-lg text-slate-300 text-[11px] border border-slate-800">
                      <strong>Past Resolution:</strong> "{sim.resolution_notes}"
                    </div>

                    <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
                      <span>Dept: {sim.department_name}</span>
                      <span>Resolved in {sim.hours_to_resolve}h</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Status Update Modal */}
      {showStatusModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <form onSubmit={handleUpdateStatus} className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <h3 className="text-lg font-bold text-slate-900">
              Update Incident Workflow Status
            </h3>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Target Status
              </label>
              <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                className="w-full text-sm rounded-xl border border-slate-300 p-2.5 bg-white focus:border-indigo-500 outline-none"
              >
                <option value="Submitted">Submitted</option>
                <option value="AI Analysed">AI Analysed</option>
                <option value="Assigned">Assigned</option>
                <option value="Under Investigation">Under Investigation</option>
                <option value="In Progress">In Progress</option>
                <option value="Awaiting Info">Awaiting Info</option>
                <option value="Resolved">Resolved (Requires Resolution Notes)</option>
                <option value="Closed">Closed (Requires Resolution Notes)</option>
              </select>
            </div>

            {/* Resolution notes required for Resolved / Closed */}
            {['Resolved', 'Closed'].includes(newStatus) && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Resolution Notes <span className="text-rose-500">* (Mandatory)</span>
                  </label>
                  {/* Quick autofill suggestion button */}
                  {incident.similar_resolved?.length > 0 && (
                    <button
                      type="button"
                      onClick={() => setResolutionNotes(incident.similar_resolved[0].resolution_notes)}
                      className="text-[10px] text-indigo-600 hover:underline"
                    >
                      Use AI Resolution Intel
                    </button>
                  )}
                </div>
                <textarea
                  rows={3}
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  placeholder="Describe technical corrective actions taken, replaced parts, or verification steps..."
                  className="w-full text-sm rounded-xl border border-slate-300 p-2.5 focus:border-indigo-500 outline-none"
                  required
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Optional Audit Remarks
              </label>
              <input
                type="text"
                value={statusRemarks}
                onChange={(e) => setStatusRemarks(e.target.value)}
                placeholder="Brief reason or action summary..."
                className="w-full text-sm rounded-xl border border-slate-300 p-2.5 focus:border-indigo-500 outline-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowStatusModal(false)}
                className="px-4 py-2 border border-slate-300 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={updatingStatus}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs"
              >
                {updatingStatus ? 'Updating...' : 'Save Status Update'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Assign Department Modal */}
      {showAssignModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <form onSubmit={handleAssignDepartment} className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <h3 className="text-lg font-bold text-slate-900">
              Assign Handling Department
            </h3>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Department
              </label>
              <select
                value={selectedDeptId}
                onChange={(e) => setSelectedDeptId(parseInt(e.target.value))}
                className="w-full text-sm rounded-xl border border-slate-300 p-2.5 bg-white focus:border-indigo-500 outline-none"
              >
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Assignment Instructions
              </label>
              <input
                type="text"
                value={assignRemarks}
                onChange={(e) => setAssignRemarks(e.target.value)}
                placeholder="e.g. Priority dispatch to Hostel Block B plumbing line..."
                className="w-full text-sm rounded-xl border border-slate-300 p-2.5 focus:border-indigo-500 outline-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowAssignModal(false)}
                className="px-4 py-2 border border-slate-300 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={assigning}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs"
              >
                {assigning ? 'Assigning...' : 'Confirm Assignment'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default IncidentDetail;
