import React, { useState } from 'react';
import { api } from '../api/client';
import { useToast } from '../context/ToastContext';
import { Link } from 'react-router-dom';
import {
  PlayCircle,
  FastForward,
  RotateCcw,
  Clock,
  Sparkles,
  Layers,
  ShieldAlert,
  ArrowRight,
  CheckCircle,
  Loader2,
} from 'lucide-react';
import ErrorAlert from '../components/ErrorAlert';

export const DemoControl = () => {
  const { addToast } = useToast();

  const [loadingStory, setLoadingStory] = useState(false);
  const [storyResult, setStoryResult] = useState(null);

  const [customHours, setCustomHours] = useState(6);
  const [advancingTime, setAdvancingTime] = useState(false);
  const [advanceResult, setAdvanceResult] = useState(null);

  const [resetting, setResetting] = useState(false);
  const [error, setError] = useState(null);

  const handleLoadStory = async () => {
    try {
      setLoadingStory(true);
      setError(null);
      const res = await api.demo.loadStory();
      setStoryResult(res.data);
      addToast('Demo story loaded: 5 multilingual complaints submitted & clustered!', 'success');
    } catch (err) {
      setError(err.userMessage || 'Failed to load demo story');
    } finally {
      setLoadingStory(false);
    }
  };

  const handleAdvanceTime = async (hours) => {
    try {
      setAdvancingTime(true);
      setError(null);
      const res = await api.demo.advanceTime(parseFloat(hours));
      setAdvanceResult(res.data);
      addToast(`Virtual clock advanced by ${hours} hours.`, 'info');
    } catch (err) {
      setError(err.userMessage || 'Failed to advance virtual time');
    } finally {
      setAdvancingTime(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm('Reset demo complaints and set virtual time offset back to 0?')) return;
    try {
      setResetting(true);
      setError(null);
      const res = await api.demo.reset();
      setStoryResult(null);
      setAdvanceResult(null);
      addToast('Demo state and virtual clock reset to benchmark.', 'success');
    } catch (err) {
      setError(err.userMessage || 'Failed to reset demo state');
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-amber-600 font-semibold text-xs uppercase tracking-wider mb-1">
          <Sparkles className="w-4 h-4" />
          Interactive Evaluation Suite
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Demo Simulator & SLA Time Machine
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Deterministically simulate multi-lingual grievance bursts, trigger AI clustering, and fast-forward time to test SLA escalation rules.
        </p>
      </div>

      <ErrorAlert message={error} />

      {/* Simulator Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Card 1: Canonical Demo Story */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center">
              <PlayCircle className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-base text-slate-900">1. Load Canonical Demo Story</h3>
              <p className="text-xs text-slate-500">Hostel Block B Water Leakage Cluster</p>
            </div>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed">
            Automatically simulates <strong>5 incoming complaints</strong> spaced over virtual hours:
          </p>
          <ul className="text-xs text-slate-600 space-y-1 list-disc list-inside bg-slate-50 p-3 rounded-xl border border-slate-100">
            <li>2 English complaints describing pipe rupture</li>
            <li>1 Hindi complaint (हिंदी Devanagari)</li>
            <li>1 Hinglish complaint ("nal ka paani waste ho raha hai")</li>
            <li>1 Anonymous report with generated access code</li>
          </ul>

          <button
            onClick={handleLoadStory}
            disabled={loadingStory}
            className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white rounded-xl text-xs font-semibold shadow-xs transition flex items-center justify-center gap-2"
          >
            {loadingStory ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Executing Ingestion & Clustering...
              </>
            ) : (
              <>
                <PlayCircle className="w-4 h-4" />
                Inject 5 Multilingual Complaints
              </>
            )}
          </button>
        </div>

        {/* Card 2: Virtual Clock Fast-Forward */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center">
              <FastForward className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-base text-slate-900">2. Virtual Clock Time Machine</h3>
              <p className="text-xs text-slate-500">Deterministic SLA Escalation Testing</p>
            </div>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed">
            Fast-forward internal time to trigger automatic background SLA evaluations (Critical: 4h, High: 24h, Medium: 72h):
          </p>

          {/* Quick Buttons */}
          <div className="grid grid-cols-4 gap-2">
            {[1, 4, 6, 24].map((h) => (
              <button
                key={h}
                onClick={() => handleAdvanceTime(h)}
                disabled={advancingTime}
                className="py-2 px-3 rounded-xl border border-slate-200 hover:border-amber-400 hover:bg-amber-50 text-xs font-bold text-slate-700 transition"
              >
                +{h} Hour{h > 1 ? 's' : ''}
              </button>
            ))}
          </div>

          {/* Custom Hours */}
          <div className="flex items-center gap-2 pt-1">
            <input
              type="number"
              min="1"
              max="200"
              value={customHours}
              onChange={(e) => setCustomHours(e.target.value)}
              className="w-24 text-sm rounded-xl border border-slate-300 p-2 font-mono"
            />
            <button
              onClick={() => handleAdvanceTime(customHours)}
              disabled={advancingTime}
              className="flex-1 py-2 px-4 bg-amber-600 hover:bg-amber-700 disabled:bg-amber-400 text-white rounded-xl text-xs font-semibold shadow-xs transition"
            >
              Advance by {customHours} Hours
            </button>
          </div>
        </div>
      </div>

      {/* Story Execution Results Banner */}
      {storyResult && (
        <div className="bg-white rounded-2xl border border-indigo-200 shadow-sm p-6 space-y-4 animate-in fade-in duration-200">
          <div className="flex items-center justify-between flex-wrap gap-2 border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2 text-emerald-600">
              <CheckCircle className="w-5 h-5" />
              <h4 className="font-bold text-base text-slate-900">Story Injected Successfully</h4>
            </div>
            {storyResult.pending_suggestion_id && (
              <Link
                to="/suggestions"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs"
              >
                <Layers className="w-4 h-4" />
                View Created Suggestion #{storyResult.pending_suggestion_id}
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            )}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="bg-slate-50 p-3 rounded-xl">
              <span className="text-slate-400 block mb-0.5">Location:</span>
              <span className="font-bold text-slate-900">{storyResult.location}</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl">
              <span className="text-slate-400 block mb-0.5">Complaints Ingested:</span>
              <span className="font-bold text-slate-900">{storyResult.complaints_created?.length}</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl">
              <span className="text-slate-400 block mb-0.5">Grouped in Suggestion:</span>
              <span className="font-bold text-indigo-700">{storyResult.grouped_complaint_count} Complaints</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl">
              <span className="text-slate-400 block mb-0.5">System Confidence:</span>
              <span className="font-bold text-emerald-600">
                {(storyResult.composite_confidence * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          <div>
            <h5 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
              Ingested Complaints Breakdown:
            </h5>
            <div className="space-y-1.5">
              {storyResult.complaints_created?.map((c, i) => (
                <div key={i} className="flex items-center justify-between text-xs p-2 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-slate-900">{c.tracking_id}</span>
                    <span className="uppercase text-[10px] bg-slate-200 px-1.5 py-0.5 rounded font-semibold">
                      {c.language}
                    </span>
                    <span className="text-slate-600">{c.category}</span>
                  </div>
                  {c.is_anonymous ? (
                    <span className="text-amber-700 font-mono text-[11px] font-bold">
                      Access Code: {c.access_code} (Anonymous)
                    </span>
                  ) : (
                    <span className="text-slate-400 text-[11px]">Logged-in Student</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Advance Time Escalation Results Banner */}
      {advanceResult && (
        <div className="bg-white rounded-2xl border border-amber-200 shadow-sm p-6 space-y-3 animate-in fade-in duration-200">
          <div className="flex items-center gap-2 text-amber-700">
            <Clock className="w-5 h-5" />
            <h4 className="font-bold text-base text-slate-900">Virtual Clock Updated</h4>
          </div>

          <div className="text-xs text-slate-600 space-y-1">
            <p>
              Current Virtual Time: <strong className="font-mono text-slate-900">{advanceResult.new_time}</strong>
            </p>
            <p>
              Total Offset: <strong>+{advanceResult.total_offset_hours} hours</strong>
            </p>
          </div>

          {advanceResult.escalations_triggered?.length > 0 ? (
            <div className="bg-rose-50 border border-rose-200 p-4 rounded-xl space-y-2">
              <h5 className="text-xs font-bold text-rose-900 flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-rose-600" />
                SLA Breaches Detected & Escalations Applied:
              </h5>
              <div className="space-y-1 text-xs text-rose-800">
                {advanceResult.escalations_triggered.map((esc, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <span>
                      {esc.target_type === 'incident' ? 'Incident' : 'Complaint'} <strong>{esc.code || `#${esc.id}`}</strong>
                    </span>
                    <span className="font-bold bg-rose-200 px-2 py-0.5 rounded text-[11px]">
                      Escalated to Tier {esc.new_level} ({esc.overdue_hours}h overdue)
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">No new SLA escalations triggered.</p>
          )}
        </div>
      )}

      {/* Pristine Reset Section */}
      <div className="pt-4 border-t border-slate-200 flex items-center justify-between">
        <div>
          <h4 className="font-bold text-sm text-slate-900">Reset Simulator State</h4>
          <p className="text-xs text-slate-500">
            Clears dynamic demo complaints and resets virtual time offset to 0.
          </p>
        </div>
        <button
          onClick={handleReset}
          disabled={resetting}
          className="inline-flex items-center gap-1.5 px-4 py-2 border border-rose-300 text-rose-700 hover:bg-rose-50 rounded-xl text-xs font-semibold transition"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          {resetting ? 'Resetting...' : 'Reset to Benchmark'}
        </button>
      </div>
    </div>
  );
};

export default DemoControl;
