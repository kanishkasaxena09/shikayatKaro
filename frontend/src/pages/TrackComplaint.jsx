import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import {
  Search,
  CheckCircle,
  Clock,
  Shield,
  Layers,
  MapPin,
  Calendar,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import PriorityBadge from '../components/PriorityBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorAlert from '../components/ErrorAlert';

export const TrackComplaint = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [trackingId, setTrackingId] = useState(searchParams.get('tracking_id') || '');
  const [accessCode, setAccessCode] = useState(searchParams.get('access_code') || '');

  const [complaint, setComplaint] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchTrack = async (idToTrack, codeToUse) => {
    if (!idToTrack) return;
    try {
      setLoading(true);
      setError(null);
      const res = await api.complaints.track(idToTrack.trim(), codeToUse ? codeToUse.trim() : null);
      setComplaint(res.data);
    } catch (err) {
      setComplaint(null);
      setError(err.userMessage || 'Complaint not found or invalid access code.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const qTracking = searchParams.get('tracking_id');
    const qCode = searchParams.get('access_code');
    if (qTracking) {
      setTrackingId(qTracking);
      setAccessCode(qCode || '');
      fetchTrack(qTracking, qCode);
    }
  }, [searchParams]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!trackingId.trim()) return;
    setSearchParams({ tracking_id: trackingId.trim(), ...(accessCode ? { access_code: accessCode.trim() } : {}) });
    fetchTrack(trackingId, accessCode);
  };

  // Progression steps
  const steps = [
    { key: 'Submitted', label: 'Submitted' },
    { key: 'AI Analysed', label: 'AI Analysed' },
    { key: 'Assigned', label: 'Assigned' },
    { key: 'In Progress', label: 'In Progress' },
    { key: 'Resolved', label: 'Resolved' },
  ];

  const getStepIndex = (status) => {
    if (!status) return 0;
    if (status === 'Submitted') return 0;
    if (status === 'AI Analysed') return 1;
    if (status === 'Assigned') return 2;
    if (['Under Investigation', 'In Progress', 'Awaiting Info'].includes(status)) return 3;
    if (['Resolved', 'Closed'].includes(status)) return 4;
    return 1;
  };

  const currentStep = getStepIndex(complaint?.status);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Track Grievance Status
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Enter your sequential tracking identifier (e.g. <code className="text-indigo-600 font-bold">CMP-0001</code>). If filed anonymously, provide your 8-character access code.
        </p>
      </div>

      {/* Search Input Box */}
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
        <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
          <div className="sm:col-span-6">
            <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-1">
              Tracking ID (e.g. CMP-0001)
            </label>
            <input
              type="text"
              value={trackingId}
              onChange={(e) => setTrackingId(e.target.value)}
              placeholder="CMP-XXXX"
              required
              className="w-full text-sm rounded-xl border border-slate-300 p-2.5 font-mono uppercase focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none"
            />
          </div>

          <div className="sm:col-span-4">
            <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-1">
              Access Code (For Anonymous)
            </label>
            <input
              type="text"
              value={accessCode}
              onChange={(e) => setAccessCode(e.target.value)}
              placeholder="e.g. 8A4F19B2"
              className="w-full text-sm rounded-xl border border-slate-300 p-2.5 font-mono uppercase focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none"
            />
          </div>

          <div className="sm:col-span-2 flex items-end">
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white rounded-xl text-xs font-semibold shadow-xs transition flex items-center justify-center gap-1.5"
            >
              <Search className="w-3.5 h-3.5" />
              Track
            </button>
          </div>
        </div>
      </form>

      <ErrorAlert message={error} />
      {loading && <LoadingSpinner message="Retrieving grievance tracking records..." />}

      {/* Result Card */}
      {complaint && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden divide-y divide-slate-100">
          {/* Card Top Banner */}
          <div className="p-6 bg-slate-50 flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-lg font-bold text-slate-900">{complaint.tracking_id}</span>
                <StatusBadge status={complaint.status} />
                <PriorityBadge priority={complaint.priority} />
                {complaint.is_anonymous && (
                  <span className="text-xs bg-slate-200 text-slate-700 font-medium px-2 py-0.5 rounded-full flex items-center gap-1">
                    <Shield className="w-3 h-3 text-slate-500" />
                    Anonymous Report
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Submitted on {new Date(complaint.created_at).toLocaleString()}
              </p>
            </div>

            {/* Parent Incident Link */}
            {complaint.incident_id && (
              <Link
                to={`/incidents/${complaint.incident_id}`}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-semibold hover:bg-indigo-100 transition"
              >
                <Layers className="w-3.5 h-3.5 text-indigo-600" />
                Aggregated into Incident #{complaint.incident_id}
              </Link>
            )}
          </div>

          {/* Progress Timeline Stepper */}
          <div className="p-6">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4">
              Resolution Pipeline Progression
            </h3>
            <div className="grid grid-cols-5 gap-2 relative">
              {steps.map((step, idx) => {
                const isPassed = idx <= currentStep;
                const isCurrent = idx === currentStep;
                return (
                  <div key={step.key} className="flex flex-col items-center text-center">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs mb-1.5 transition ${
                        isCurrent
                          ? 'bg-indigo-600 text-white ring-4 ring-indigo-100'
                          : isPassed
                          ? 'bg-emerald-600 text-white'
                          : 'bg-slate-200 text-slate-500'
                      }`}
                    >
                      {isPassed && !isCurrent ? <CheckCircle className="w-4 h-4" /> : idx + 1}
                    </div>
                    <span
                      className={`text-xs ${
                        isCurrent ? 'font-bold text-indigo-900' : isPassed ? 'text-slate-800' : 'text-slate-400'
                      }`}
                    >
                      {step.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Grievance Details Body */}
          <div className="p-6 space-y-4">
            <div>
              <span className="text-xs font-bold uppercase text-slate-400 block mb-1">
                Grievance Description
              </span>
              <p className="text-sm text-slate-800 bg-slate-50 p-4 rounded-xl border border-slate-100 whitespace-pre-wrap">
                {complaint.text}
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                <span className="text-slate-400 block mb-1">Category & Confidence:</span>
                <span className="font-semibold text-slate-900">{complaint.category}</span>
                <span className="text-slate-500 block text-[11px]">
                  ({(complaint.category_confidence * 100).toFixed(0)}% AI Confidence)
                </span>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                <span className="text-slate-400 block mb-1">Campus Location:</span>
                <span className="font-semibold text-slate-900">{complaint.location_name || 'Campus Wide'}</span>
                <span className="text-slate-500 block text-[11px]">
                  {complaint.affected_count} people affected
                </span>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                <span className="text-slate-400 block mb-1">Handling Department:</span>
                <span className="font-semibold text-slate-900">
                  {complaint.department_name || 'Pending Assignment'}
                </span>
              </div>
            </div>

            {/* SLA Deadline */}
            {complaint.deadline_at && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-center gap-2 text-xs text-amber-900">
                <Clock className="w-4 h-4 text-amber-600 flex-shrink-0" />
                <span>
                  SLA Target Deadline: <strong>{new Date(complaint.deadline_at).toLocaleString()}</strong>
                  {complaint.escalation_level > 0 && (
                    <span className="ml-2 bg-rose-600 text-white px-1.5 py-0.5 rounded text-[10px] font-bold">
                      Escalated (Tier {complaint.escalation_level})
                    </span>
                  )}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TrackComplaint;
