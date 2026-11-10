import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import {
  FileText,
  Search,
  CheckCircle,
  Clock,
  MapPin,
  Shield,
  Layers,
  ArrowRight,
  Droplets,
  Zap,
  Wifi,
  Sparkles,
  Utensils,
  HelpCircle,
  AlertCircle,
  Building,
} from 'lucide-react';
import StatusBadge from '../../components/StatusBadge';
import PriorityBadge from '../../components/PriorityBadge';
import LoadingSpinner from '../../components/LoadingSpinner';
import ErrorAlert from '../../components/ErrorAlert';

export const StudentDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [myComplaints, setMyComplaints] = useState([]);
  const [activeCampusIncidents, setActiveCampusIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Quick anonymous track input state
  const [quickTrackId, setQuickTrackId] = useState('');
  const [quickAccessCode, setQuickAccessCode] = useState('');

  const loadStudentData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [compRes, incRes] = await Promise.all([
        api.complaints.getMy(),
        api.incidents.list({ status: 'In Progress' }),
      ]);
      setMyComplaints(compRes.data || []);
      setActiveCampusIncidents((incRes.data || []).slice(0, 3));
    } catch (err) {
      setError(err.userMessage || 'Failed to load your student dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStudentData();
  }, []);

  const handleQuickTrack = (e) => {
    e.preventDefault();
    if (!quickTrackId.trim()) return;
    const url = `/track?tracking_id=${encodeURIComponent(quickTrackId.trim())}${
      quickAccessCode ? `&access_code=${encodeURIComponent(quickAccessCode.trim())}` : ''
    }`;
    navigate(url);
  };

  const categoryPresets = [
    {
      title: 'Water & Plumbing',
      icon: Droplets,
      desc: 'Pipeline leaks, drinking water, taps, washrooms',
      color: 'from-blue-500 to-cyan-600',
      text: 'Water leakage in washroom/drinking cooler needing urgent plumbing repair',
    },
    {
      title: 'Electrical & Power',
      icon: Zap,
      desc: 'Sparking, power cut, ceiling fans, corridor lights',
      color: 'from-amber-500 to-yellow-600',
      text: 'Electrical malfunction and power issue requiring electrician inspection',
    },
    {
      title: 'Wi-Fi & Internet',
      icon: Wifi,
      desc: 'Hostel access points offline, slow speeds',
      color: 'from-indigo-500 to-purple-600',
      text: 'Campus hostel Wi-Fi network disconnected and access point not responding',
    },
    {
      title: 'Hostel & Food Mess',
      icon: Utensils,
      desc: 'Mess hygiene, dining water, room doors, keys',
      color: 'from-emerald-500 to-teal-600',
      text: 'Hostel room door lock jammed and dining mess maintenance required',
    },
    {
      title: 'Sanitation & Hygiene',
      icon: Sparkles,
      desc: 'Dustbin overflow, drainage blockage, washroom hygiene',
      color: 'from-rose-500 to-pink-600',
      text: 'Sewage drain blockage and foul odor overflow requiring sanitation crew',
    },
    {
      title: 'Campus Safety',
      icon: Shield,
      desc: 'Dark zones, boundary lights, gates, emergency concerns',
      color: 'from-slate-700 to-slate-900',
      text: 'Campus perimeter boundary lighting dark spot requiring proctorial security check',
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Student Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-emerald-600 via-teal-600 to-indigo-700 text-white p-6 sm:p-8 shadow-lg">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/20 backdrop-blur-md text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-300 animate-pulse"></span>
              Student & Citizen Grievance Portal
            </div>
            <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
              Namaste, {user?.full_name || 'Student'}! 👋
            </h1>
            <p className="text-sm text-emerald-100 leading-relaxed">
              Report campus facilities issues in <strong>Hindi</strong>, <strong>Hinglish</strong>, or <strong>English</strong>. Our AI clusters related issues together to ensure rapid maintenance response.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3">
            <Link
              to="/submit"
              className="w-full sm:w-auto px-5 py-3 rounded-2xl bg-white text-emerald-900 hover:bg-emerald-50 font-bold text-xs sm:text-sm shadow-md transition flex items-center justify-center gap-2"
            >
              <FileText className="w-4 h-4 text-emerald-700" />
              File a New Grievance
            </Link>
            <Link
              to="/track"
              className="w-full sm:w-auto px-5 py-3 rounded-2xl bg-white/10 hover:bg-white/20 border border-white/30 text-white font-semibold text-xs sm:text-sm backdrop-blur-md transition flex items-center justify-center gap-2"
            >
              <Search className="w-4 h-4" />
              Track Any Issue
            </Link>
          </div>
        </div>
      </div>

      <ErrorAlert message={error} onRetry={loadStudentData} />

      {/* Quick Category Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
            What type of issue are you facing?
          </h2>
          <span className="text-xs text-slate-400">Click to report with smart suggestions</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {categoryPresets.map((cat, idx) => {
            const Icon = cat.icon;
            return (
              <Link
                key={idx}
                to="/submit"
                state={{ prefillText: cat.text }}
                className="group bg-white rounded-2xl border border-slate-200 p-5 shadow-xs hover:border-emerald-400 hover:shadow-md transition flex items-start gap-4"
              >
                <div
                  className={`w-12 h-12 rounded-2xl bg-gradient-to-tr ${cat.color} flex items-center justify-center text-white flex-shrink-0 shadow-sm group-hover:scale-105 transition`}
                >
                  <Icon className="w-6 h-6" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-bold text-sm text-slate-900 group-hover:text-emerald-700 transition flex items-center justify-between">
                    {cat.title}
                    <ArrowRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition text-emerald-600" />
                  </h3>
                  <p className="text-xs text-slate-500 mt-1 leading-snug line-clamp-2">
                    {cat.desc}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* 2-Column Section: Left (My Recent Grievances) & Right (Quick Tracker & Campus Bulletins) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: My Active Grievances */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-emerald-600" />
              My Submitted Grievances
            </h2>
            {myComplaints.length > 0 && (
              <Link
                to="/my-complaints"
                className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 flex items-center gap-1"
              >
                View all ({myComplaints.length}) <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            )}
          </div>

          {loading ? (
            <LoadingSpinner message="Checking your grievance pipeline..." />
          ) : myComplaints.length === 0 ? (
            <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center text-slate-500 space-y-3">
              <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
                <FileText className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-slate-800 text-sm">No Active Grievances Filed</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                Whenever you report an issue, its real-time resolution timeline and department assignments will appear right here.
              </p>
              <Link
                to="/submit"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow-xs transition"
              >
                File an Issue Now
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {myComplaints.slice(0, 4).map((c) => (
                <div
                  key={c.id}
                  className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs hover:border-emerald-300 transition space-y-2.5"
                >
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">
                        {c.tracking_id}
                      </span>
                      <StatusBadge status={c.status} />
                      <PriorityBadge priority={c.priority} />
                      <span className="text-xs font-medium text-slate-600">{c.category}</span>
                    </div>
                    <span className="text-[11px] text-slate-400">
                      {new Date(c.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <p className="text-xs text-slate-700 line-clamp-2 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                    {c.text}
                  </p>

                  <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      {c.location_name || 'Campus Wide'}
                    </span>

                    <Link
                      to={`/track?tracking_id=${c.tracking_id}`}
                      className="font-semibold text-emerald-700 hover:text-emerald-900 flex items-center gap-1"
                    >
                      Track Step Progress <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Quick Anonymous Code Tracker & Campus Repair Notice Board */}
        <div className="space-y-6">
          {/* Quick Anonymous Track Card */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs space-y-3">
            <h3 className="font-bold text-sm text-slate-900 flex items-center gap-2">
              <Shield className="w-4 h-4 text-emerald-600" />
              Track Anonymous Complaint
            </h3>
            <p className="text-xs text-slate-500">
              Filed an issue anonymously? Check its status using your private access code:
            </p>

            <form onSubmit={handleQuickTrack} className="space-y-2.5">
              <input
                type="text"
                value={quickTrackId}
                onChange={(e) => setQuickTrackId(e.target.value)}
                placeholder="Tracking ID (e.g. CMP-0005)"
                required
                className="w-full text-xs rounded-xl border border-slate-300 p-2.5 font-mono uppercase focus:border-emerald-500 outline-none"
              />
              <input
                type="text"
                value={quickAccessCode}
                onChange={(e) => setQuickAccessCode(e.target.value)}
                placeholder="Access Code (e.g. DBE24BE1)"
                className="w-full text-xs rounded-xl border border-slate-300 p-2.5 font-mono uppercase focus:border-emerald-500 outline-none"
              />
              <button
                type="submit"
                className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow-xs transition"
              >
                Track Live Status
              </button>
            </form>
          </div>

          {/* Campus Live Repairs Bulletin */}
          <div className="bg-slate-900 rounded-2xl p-5 text-white shadow-md space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
              <h3 className="font-bold text-sm text-white flex items-center gap-2">
                <Building className="w-4 h-4 text-emerald-400" />
                Active Campus Repairs
              </h3>
              <span className="text-[10px] uppercase font-bold bg-emerald-900/60 text-emerald-300 border border-emerald-700 px-2 py-0.5 rounded">
                Live Redressal
              </span>
            </div>

            <p className="text-xs text-slate-300">
              Check if an ongoing repair already covers your area before filing duplicate reports:
            </p>

            {activeCampusIncidents.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No major repair works in progress.</p>
            ) : (
              <div className="space-y-2.5">
                {activeCampusIncidents.map((inc) => (
                  <div key={inc.id} className="bg-slate-800/80 p-3 rounded-xl border border-slate-700/80 space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-emerald-300">{inc.category}</span>
                      <span className="text-[10px] text-amber-400 font-semibold">{inc.status}</span>
                    </div>
                    <div className="text-white font-medium text-[11px]">{inc.title}</div>
                    <div className="text-slate-400 text-[10px] flex items-center gap-1">
                      <MapPin className="w-3 h-3" /> {inc.location_name || 'Campus Wide'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentDashboard;
