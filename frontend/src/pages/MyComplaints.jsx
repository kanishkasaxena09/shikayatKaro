import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { FileText, ArrowRight, Layers, Clock, AlertCircle } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import PriorityBadge from '../components/PriorityBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorAlert from '../components/ErrorAlert';

export const MyComplaints = () => {
  const { user } = useAuth();
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMyComplaints = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.complaints.getMy();
      setComplaints(res.data || []);
    } catch (err) {
      setError(err.userMessage || 'Failed to retrieve your grievances');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMyComplaints();
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            My Submitted Grievances
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Grievances filed under account <strong>{user?.email}</strong>.
          </p>
        </div>

        <Link
          to="/submit"
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-xs"
        >
          <FileText className="w-4 h-4" />
          File New Grievance
        </Link>
      </div>

      <ErrorAlert message={error} onRetry={fetchMyComplaints} />

      {loading && <LoadingSpinner message="Retrieving your filed grievances..." />}

      {!loading && complaints.length === 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-500 space-y-3">
          <FileText className="w-10 h-10 text-slate-300 mx-auto" />
          <h3 className="font-bold text-slate-700">No grievances filed yet</h3>
          <p className="text-xs text-slate-400">
            Any grievances you submit while logged in (non-anonymously) will appear here for easy tracking.
          </p>
          <Link
            to="/submit"
            className="inline-flex items-center gap-1 px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold"
          >
            Submit your first grievance
          </Link>
        </div>
      )}

      <div className="space-y-4">
        {complaints.map((c) => (
          <div
            key={c.id}
            className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-3 hover:border-slate-300 transition"
          >
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm font-bold text-slate-900">{c.tracking_id}</span>
                <StatusBadge status={c.status} />
                <PriorityBadge priority={c.priority} />
                <span className="text-xs text-slate-500 font-medium">Category: {c.category}</span>
              </div>
              <span className="text-xs text-slate-400">
                {new Date(c.created_at).toLocaleDateString()} at{' '}
                {new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>

            <p className="text-sm text-slate-800 bg-slate-50 p-3 rounded-xl border border-slate-100">
              {c.text}
            </p>

            <div className="flex items-center justify-between flex-wrap gap-2 text-xs text-slate-500 pt-1">
              <span>Location: <strong>{c.location_name || 'Campus'}</strong></span>

              <div className="flex items-center gap-3">
                {c.incident_id && (
                  <span className="text-indigo-600 font-semibold flex items-center gap-1">
                    <Layers className="w-3.5 h-3.5" /> Clustered in Incident #{c.incident_id}
                  </span>
                )}
                <Link
                  to={`/track?tracking_id=${c.tracking_id}`}
                  className="font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                >
                  Track Pipeline <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MyComplaints;
