import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle,
  Copy,
  Check,
  ShieldCheck,
  Sparkles,
  Layers,
  ArrowRight,
  AlertTriangle,
} from 'lucide-react';

export const AiAnalysisModal = ({ data, onClose }) => {
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);

  if (!data) return null;

  const { complaint, access_code, suggestion_created, suggestion_id, ai_analysis } = data;

  const handleCopyCode = () => {
    if (access_code) {
      navigator.clipboard.writeText(access_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-xl w-full shadow-2xl border border-slate-100 overflow-hidden transform transition-all animate-in fade-in duration-200">
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-900 to-slate-900 text-white p-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/20 border border-emerald-400/40 flex items-center justify-center text-emerald-400">
              <CheckCircle className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-xl font-bold tracking-tight">Grievance Registered Successfully</h3>
              <p className="text-xs text-indigo-200">
                Tracking Reference: <strong className="text-white font-mono">{complaint.tracking_id}</strong>
              </p>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-5">
          {/* Anonymous Access Code Callout */}
          {complaint.is_anonymous && access_code && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
              <div className="flex items-start gap-3">
                <ShieldCheck className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="text-sm font-bold text-amber-900">
                    Anonymous Grievance — Save Your Access Code
                  </h4>
                  <p className="text-xs text-amber-700 mt-1">
                    Your personal identity was NOT recorded. To track this complaint in the future, you must use this secret access code:
                  </p>
                  <div className="mt-2 flex items-center gap-2">
                    <span className="font-mono text-base font-bold bg-white px-3 py-1.5 rounded-lg border border-amber-300 text-amber-900 select-all">
                      {access_code}
                    </span>
                    <button
                      onClick={handleCopyCode}
                      className="inline-flex items-center gap-1 px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-semibold transition"
                    >
                      {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                      {copied ? 'Copied' : 'Copy Code'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* AI Pipeline Results */}
          <div className="border border-slate-200 rounded-xl p-4 bg-slate-50 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-200 pb-2">
              <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                AI Pipeline Diagnostic
              </span>
              <span className="text-xs bg-indigo-100 text-indigo-800 font-semibold px-2 py-0.5 rounded">
                Language: {complaint.original_language?.toUpperCase()}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-xs text-slate-500 block">Predicted Category:</span>
                <span className="font-semibold text-slate-900">{complaint.category}</span>
                {ai_analysis?.classification?.confidence && (
                  <span className="text-[11px] text-slate-500 block">
                    Confidence: {(ai_analysis.classification.confidence * 100).toFixed(1)}%
                  </span>
                )}
              </div>
              <div>
                <span className="text-xs text-slate-500 block">Rule-Based Priority:</span>
                <span className="font-semibold text-indigo-700">{complaint.priority}</span>
              </div>
            </div>

            {complaint.priority_reasons?.length > 0 && (
              <div>
                <span className="text-xs text-slate-500 block mb-1">Priority Rationale:</span>
                <ul className="text-xs text-slate-600 space-y-0.5 list-disc list-inside">
                  {complaint.priority_reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Incident Aggregation Notice */}
          {suggestion_created && (
            <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-3 flex items-start gap-3 text-xs text-indigo-900">
              <Layers className="w-4 h-4 text-indigo-600 flex-shrink-0 mt-0.5" />
              <div>
                <strong>Multi-Factor Clustering Match:</strong> Our AI detected related complaints with high semantic, spatial, and temporal proximity. This grievance was automatically grouped into Incident Suggestion #{suggestion_id} for aggregated resolution.
              </div>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              onClick={() => {
                onClose();
                navigate(`/track?tracking_id=${complaint.tracking_id}${access_code ? `&access_code=${access_code}` : ''}`);
              }}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold inline-flex items-center gap-1.5 transition"
            >
              Track Progress
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 border border-slate-300 hover:bg-slate-100 rounded-xl text-xs font-semibold text-slate-700 transition"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AiAnalysisModal;
