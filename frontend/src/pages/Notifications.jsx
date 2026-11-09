import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Bell, Check, ArrowRight, AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorAlert from '../components/ErrorAlert';

export const Notifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchNotifs = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.notifications.getMy();
      setNotifications(res.data || []);
    } catch (err) {
      setError(err.userMessage || 'Failed to retrieve notifications');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifs();
  }, []);

  const markAsRead = async (id) => {
    try {
      await api.notifications.markRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch {
      // silent
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Notification Center
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            System dispatch alerts, SLA deadline warnings, and status transitions.
          </p>
        </div>
      </div>

      <ErrorAlert message={error} onRetry={fetchNotifs} />
      {loading && <LoadingSpinner message="Checking notifications..." />}

      {!loading && notifications.length === 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-500 space-y-2">
          <Bell className="w-10 h-10 text-slate-300 mx-auto" />
          <h3 className="font-bold text-slate-700">No notifications</h3>
          <p className="text-xs text-slate-400">You are all caught up on alerts.</p>
        </div>
      )}

      <div className="space-y-3">
        {notifications.map((n) => (
          <div
            key={n.id}
            className={`p-4 rounded-2xl border transition flex items-start justify-between gap-4 ${
              n.is_read
                ? 'bg-white border-slate-200 text-slate-600'
                : 'bg-indigo-50/50 border-indigo-200 text-slate-900 shadow-xs'
            }`}
          >
            <div className="space-y-1 flex-1">
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-slate-900">{n.title}</span>
                {!n.is_read && (
                  <span className="w-2 h-2 rounded-full bg-indigo-600" title="Unread"></span>
                )}
              </div>
              <p className="text-xs text-slate-700">{n.message}</p>
              <span className="text-[11px] text-slate-400 block pt-1">
                {new Date(n.created_at).toLocaleString()}
              </span>
            </div>

            <div className="flex items-center gap-2">
              {n.target_type === 'incident' && n.target_id && (
                <Link
                  to={`/incidents/${n.target_id}`}
                  className="px-3 py-1 bg-white border border-slate-300 rounded-lg text-xs font-semibold text-indigo-700 hover:bg-indigo-50 flex items-center gap-1"
                >
                  View Incident <ArrowRight className="w-3 h-3" />
                </Link>
              )}

              {!n.is_read && (
                <button
                  onClick={() => markAsRead(n.id)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-slate-100 transition"
                  title="Mark as read"
                >
                  <Check className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Notifications;
