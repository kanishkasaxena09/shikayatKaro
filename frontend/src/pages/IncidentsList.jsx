import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import {
  AlertTriangle,
  Filter,
  Layers,
  Clock,
  ArrowRight,
  TrendingUp,
  MapPin,
  Building,
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import PriorityBadge from '../components/PriorityBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorAlert from '../components/ErrorAlert';

export const IncidentsList = () => {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  const fetchIncidents = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {};
      if (statusFilter) params.status = statusFilter;
      if (priorityFilter) params.priority = priorityFilter;
      if (categoryFilter) params.category = categoryFilter;

      const res = await api.incidents.list(params);
      setIncidents(res.data || []);
    } catch (err) {
      setError(err.userMessage || 'Failed to retrieve incidents backlog');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
  }, [statusFilter, priorityFilter, categoryFilter]);

  const getImpactBarColor = (score) => {
    if (score >= 70) return 'bg-rose-500';
    if (score >= 50) return 'bg-amber-500';
    if (score >= 30) return 'bg-blue-500';
    return 'bg-slate-400';
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Incident Management & Redressal
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Track and resolve aggregated parent incidents ranked by multi-factor impact score.
          </p>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-500 uppercase tracking-wider mr-2">
          <Filter className="w-3.5 h-3.5" />
          Filters:
        </div>

        {/* Status */}
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="text-xs bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1.5 text-slate-700 font-medium"
        >
          <option value="">All Statuses</option>
          <option value="Submitted">Submitted</option>
          <option value="AI Analysed">AI Analysed</option>
          <option value="Assigned">Assigned</option>
          <option value="Under Investigation">Under Investigation</option>
          <option value="In Progress">In Progress</option>
          <option value="Resolved">Resolved</option>
          <option value="Closed">Closed</option>
        </select>

        {/* Priority */}
        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value)}
          className="text-xs bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1.5 text-slate-700 font-medium"
        >
          <option value="">All Priorities</option>
          <option value="Critical">Critical</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>

        {/* Category */}
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="text-xs bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1.5 text-slate-700 font-medium"
        >
          <option value="">All Categories</option>
          <option value="Water & Plumbing">Water & Plumbing</option>
          <option value="Electrical">Electrical</option>
          <option value="Sanitation & Cleanliness">Sanitation & Cleanliness</option>
          <option value="IT & Network">IT & Network</option>
          <option value="Hostel & Mess">Hostel & Mess</option>
          <option value="Safety & Security">Safety & Security</option>
          <option value="Classroom & Infrastructure">Classroom & Infrastructure</option>
        </select>

        {(statusFilter || priorityFilter || categoryFilter) && (
          <button
            onClick={() => {
              setStatusFilter('');
              setPriorityFilter('');
              setCategoryFilter('');
            }}
            className="text-xs text-rose-600 hover:text-rose-800 font-semibold ml-auto"
          >
            Clear Filters
          </button>
        )}
      </div>

      <ErrorAlert message={error} onRetry={fetchIncidents} />

      {loading && <LoadingSpinner message="Loading incidents backlog..." />}

      {!loading && incidents.length === 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-500">
          <AlertTriangle className="w-10 h-10 text-slate-300 mx-auto mb-2" />
          <h3 className="font-bold text-slate-700">No matching incidents found</h3>
          <p className="text-xs text-slate-400 mt-1">
            Try adjusting your filter parameters or run the demo story simulator.
          </p>
        </div>
      )}

      {/* Incidents Cards / Table */}
      <div className="space-y-3">
        {incidents.map((inc) => (
          <Link
            key={inc.id}
            to={`/incidents/${inc.id}`}
            className="block bg-white rounded-2xl border border-slate-200 p-5 shadow-xs hover:border-indigo-300 hover:shadow-md transition group"
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              {/* Left Column: Code, Title, Badges */}
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-mono text-xs font-bold bg-slate-900 text-white px-2 py-0.5 rounded">
                    {inc.code}
                  </span>
                  <StatusBadge status={inc.status} />
                  <PriorityBadge priority={inc.priority} />
                  {inc.escalation_level > 0 && (
                    <span className="bg-rose-100 text-rose-800 border border-rose-200 px-2 py-0.5 rounded text-[10px] font-bold">
                      SLA Escalated (L{inc.escalation_level})
                    </span>
                  )}
                  <span className="text-xs font-medium text-slate-400">•</span>
                  <span className="text-xs text-slate-500 font-medium">{inc.category}</span>
                </div>

                <h3 className="text-base font-bold text-slate-900 group-hover:text-indigo-600 transition">
                  {inc.title}
                </h3>

                <div className="flex items-center gap-4 text-xs text-slate-500 flex-wrap">
                  <span className="flex items-center gap-1">
                    <Building className="w-3.5 h-3.5 text-slate-400" />
                    {inc.department_name || 'Unassigned'}
                  </span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    {inc.location_name || 'Campus Wide'}
                  </span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Layers className="w-3.5 h-3.5 text-indigo-500" />
                    <strong>{inc.linked_complaints_count}</strong> grievances grouped
                  </span>
                </div>
              </div>

              {/* Right Column: Impact Score & Pending Hours */}
              <div className="flex items-center gap-6 self-end md:self-center">
                {/* Impact Score Widget */}
                <div className="text-right min-w-[100px]">
                  <div className="flex items-center justify-end gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5 text-slate-400" />
                    <span className="text-[10px] uppercase font-bold text-slate-400">Impact Score</span>
                  </div>
                  <div className="text-xl font-extrabold text-slate-900">
                    {inc.impact_score}<span className="text-xs font-medium text-slate-400">/100</span>
                  </div>
                  <div className="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden mt-1 ml-auto">
                    <div
                      className={`h-full ${getImpactBarColor(inc.impact_score)}`}
                      style={{ width: `${Math.min(100, inc.impact_score)}%` }}
                    />
                  </div>
                </div>

                {/* Arrow */}
                <div className="w-8 h-8 rounded-full bg-slate-50 group-hover:bg-indigo-50 flex items-center justify-center text-slate-400 group-hover:text-indigo-600 transition">
                  <ArrowRight className="w-4 h-4" />
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default IncidentsList;
