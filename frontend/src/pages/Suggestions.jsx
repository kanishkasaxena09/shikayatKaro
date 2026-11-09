import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import {
  Layers,
  CheckCircle,
  XCircle,
  Trash2,
  Sparkles,
  ArrowRight,
  Shield,
  MapPin,
  Clock,
  Check,
} from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorAlert from '../components/ErrorAlert';
import StatusBadge from '../components/StatusBadge';
import PriorityBadge from '../components/PriorityBadge';
import { Link, useNavigate } from 'react-router-dom';

export const Suggestions = () => {
  const { role } = useAuth();
  const { addToast } = useToast();
  const navigate = useNavigate();

  const [suggestions, setSuggestions] = useState([]);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Confirm modal state
  const [confirmModalSugg, setConfirmModalSugg] = useState(null);
  const [confirmTitle, setConfirmTitle] = useState('');
  const [confirmPriority, setConfirmPriority] = useState('High');
  const [actionLoading, setActionLoading] = useState(false);

  const fetchSuggestions = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.suggestions.list(statusFilter);
      setSuggestions(res.data || []);
    } catch (err) {
      setError(err.userMessage || 'Failed to retrieve incident suggestions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSuggestions();
  }, [statusFilter]);

  const openConfirmModal = (sugg) => {
    setConfirmModalSugg(sugg);
    const firstCmp = sugg.complaints?.[0];
    const cat = firstCmp?.category || 'Campus Infrastructure';
    const loc = firstCmp?.location_name || 'Campus';
    setConfirmTitle(`${cat} issue near ${loc} (${sugg.complaint_ids.length} complaints grouped)`);
    setConfirmPriority(firstCmp?.priority || 'High');
  };

  const handleConfirm = async () => {
    if (!confirmModalSugg) return;
    try {
      setActionLoading(true);
      const res = await api.suggestions.confirm(confirmModalSugg.id, {
        title: confirmTitle,
        priority: confirmPriority,
      });
      addToast(
        `Suggestion confirmed! Parent Incident ${res.data.incident_code} created (Impact Score: ${res.data.impact_score}).`,
        'success'
      );
      setConfirmModalSugg(null);
      fetchSuggestions();
      navigate(`/incidents/${res.data.incident_id}`);
    } catch (err) {
      addToast(err.userMessage || 'Failed to confirm suggestion', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (id) => {
    if (!window.confirm('Are you sure you want to reject this clustering suggestion?')) return;
    try {
      await api.suggestions.reject(id);
      addToast('Suggestion marked as rejected.', 'info');
      fetchSuggestions();
    } catch (err) {
      addToast(err.userMessage || 'Failed to reject suggestion', 'error');
    }
  };

  const handleRemoveComplaint = async (suggId, complaintId) => {
    try {
      await api.suggestions.removeComplaint(suggId, complaintId);
      addToast(`Complaint #${complaintId} removed from cluster.`, 'info');
      fetchSuggestions();
    } catch (err) {
      addToast(err.userMessage || 'Failed to remove complaint from suggestion', 'error');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-indigo-600 font-semibold text-xs uppercase tracking-wider mb-1">
            <Sparkles className="w-4 h-4" />
            AI Multi-Factor Aggregation
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Incident Clustering Suggestions
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Grievances grouped by <strong>Text Embeddings (45%)</strong> + <strong>Spatial Hierarchy (25%)</strong> + <strong>Time Proximity (15%)</strong> + <strong>Category (15%)</strong>.
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl">
          {['pending', 'confirmed', 'rejected', 'all'].map((tab) => (
            <button
              key={tab}
              onClick={() => setStatusFilter(tab)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition ${
                statusFilter === tab
                  ? 'bg-white text-indigo-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <ErrorAlert message={error} onRetry={fetchSuggestions} />

      {/* Loading */}
      {loading && <LoadingSpinner message="Evaluating multi-factor relatedness clusters..." />}

      {/* Empty State */}
      {!loading && suggestions.length === 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-500 space-y-3">
          <Layers className="w-12 h-12 text-slate-300 mx-auto" />
          <h3 className="font-bold text-slate-700 text-lg">No {statusFilter} suggestions found</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Suggestions are created automatically when incoming grievances match existing open complaints across text, location, time, and category.
          </p>
          <Link
            to="/demo"
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs transition mt-2"
          >
            Run Demo Story to Auto-Generate Cluster
          </Link>
        </div>
      )}

      {/* Suggestions List */}
      <div className="space-y-6">
        {suggestions.map((sugg) => (
          <div
            key={sugg.id}
            className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
          >
            {/* Suggestion Top Banner */}
            <div className="p-6 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold text-sm shadow-md shadow-indigo-100">
                  #{sugg.id}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-base text-slate-900">
                      Cluster of {sugg.complaint_ids.length} Grievances
                    </h3>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                        sugg.status === 'pending'
                          ? 'bg-amber-100 text-amber-800'
                          : sugg.status === 'confirmed'
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-slate-200 text-slate-600'
                      }`}
                    >
                      {sugg.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500">
                    Created on {new Date(sugg.created_at).toLocaleString()}
                  </p>
                </div>
              </div>

              {/* Confidence Badge */}
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">
                    Composite Confidence
                  </span>
                  <span className="font-extrabold text-base text-indigo-700">
                    {(sugg.confidence * 100).toFixed(1)}%
                  </span>
                </div>

                {/* Actions for Pending */}
                {sugg.status === 'pending' && (role === 'admin' || role === 'handler') && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => openConfirmModal(sugg)}
                      className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs transition"
                    >
                      <CheckCircle className="w-4 h-4" />
                      Confirm & Create Incident
                    </button>
                    <button
                      onClick={() => handleReject(sugg.id)}
                      className="p-2 border border-slate-300 hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200 rounded-xl text-slate-500 transition"
                      title="Reject Suggestion"
                    >
                      <XCircle className="w-4 h-4" />
                    </button>
                  </div>
                )}

                {sugg.incident_id && (
                  <Link
                    to={`/incidents/${sugg.incident_id}`}
                    className="inline-flex items-center gap-1 px-3 py-1.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-xs font-semibold hover:bg-emerald-100"
                  >
                    View Incident #{sugg.incident_id} <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                )}
              </div>
            </div>

            {/* Decision Rationale */}
            {sugg.reasons?.length > 0 && (
              <div className="px-6 py-3 bg-indigo-50/50 border-b border-indigo-100 flex flex-wrap items-center gap-2 text-xs">
                <span className="font-bold text-indigo-900 flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                  Clustering Factors:
                </span>
                {sugg.reasons.map((r, i) => (
                  <span
                    key={i}
                    className="bg-white border border-indigo-200 text-indigo-800 px-2 py-0.5 rounded-md font-medium"
                  >
                    {r}
                  </span>
                ))}
              </div>
            )}

            {/* Complaints in this Cluster */}
            <div className="p-6 divide-y divide-slate-100">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                Grouped Citizen Complaints ({sugg.complaints?.length || 0})
              </h4>
              <div className="space-y-3">
                {sugg.complaints?.map((cmp) => (
                  <div
                    key={cmp.id}
                    className="pt-3 first:pt-0 flex flex-col sm:flex-row sm:items-start justify-between gap-3 text-xs"
                  >
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-slate-900">{cmp.tracking_id}</span>
                        <StatusBadge status={cmp.status} />
                        <PriorityBadge priority={cmp.priority} />
                        <span className="bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded text-[10px] font-semibold">
                          {cmp.original_language?.toUpperCase()}
                        </span>
                        {cmp.is_anonymous && (
                          <span className="text-slate-500 flex items-center gap-0.5 text-[10px]">
                            <Shield className="w-3 h-3 text-slate-400" /> Anonymous
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-slate-800 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                        {cmp.text}
                      </p>
                      <div className="flex items-center gap-3 text-slate-400 text-[11px]">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3 h-3" /> {cmp.location_name || 'Campus'}
                        </span>
                        <span>•</span>
                        <span>{cmp.affected_count} affected</span>
                        <span>•</span>
                        <span>{new Date(cmp.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                    </div>

                    {/* Remove Complaint Action */}
                    {sugg.status === 'pending' && sugg.complaint_ids.length > 2 && (
                      <button
                        onClick={() => handleRemoveComplaint(sugg.id, cmp.id)}
                        className="text-slate-400 hover:text-rose-600 hover:bg-rose-50 p-1.5 rounded-lg transition self-end sm:self-center"
                        title="Remove from group"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Confirmation Modal */}
      {confirmModalSugg && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 p-6 space-y-4">
            <h3 className="text-lg font-bold text-slate-900">
              Confirm Incident Grouping #{confirmModalSugg.id}
            </h3>
            <p className="text-xs text-slate-500">
              This will escalate {confirmModalSugg.complaint_ids.length} complaints into a formal Parent Incident with automated transparent Impact Scoring.
            </p>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Parent Incident Title
              </label>
              <input
                type="text"
                value={confirmTitle}
                onChange={(e) => setConfirmTitle(e.target.value)}
                className="w-full text-sm rounded-xl border border-slate-300 p-2.5 font-medium focus:border-indigo-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Priority Tier
              </label>
              <select
                value={confirmPriority}
                onChange={(e) => setConfirmPriority(e.target.value)}
                className="w-full text-sm rounded-xl border border-slate-300 p-2.5 bg-white focus:border-indigo-500 outline-none"
              >
                <option value="Critical">Critical (4h Target SLA)</option>
                <option value="High">High (24h Target SLA)</option>
                <option value="Medium">Medium (72h Target SLA)</option>
                <option value="Low">Low (168h Target SLA)</option>
              </select>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3">
              <button
                type="button"
                onClick={() => setConfirmModalSugg(null)}
                className="px-4 py-2 border border-slate-300 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirm}
                disabled={actionLoading}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs"
              >
                {actionLoading ? 'Creating Incident...' : 'Confirm & Create Incident'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Suggestions;
