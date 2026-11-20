import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import {
  FileText,
  Search,
  Layers,
  AlertTriangle,
  Bell,
  PlayCircle,
  LogIn,
  LogOut,
  Menu,
  X,
  Compass,
  CheckCircle2,
  Wrench,
  Shield,
  GraduationCap,
  Building,
} from 'lucide-react';

export const Navbar = () => {
  const { user, role, isAuthenticated, logout } = useAuth();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [pendingSuggestionsCount, setPendingSuggestionsCount] = useState(0);
  const [unreadNotificationsCount, setUnreadNotificationsCount] = useState(0);

  useEffect(() => {
    const fetchCounters = async () => {
      try {
        const dash = await api.analytics.getDashboardSummary();
        setPendingSuggestionsCount(dash.data?.pending_suggestions || 0);

        if (isAuthenticated) {
          const notifs = await api.notifications.getMy();
          const unread = notifs.data?.filter((n) => !n.is_read).length || 0;
          setUnreadNotificationsCount(unread);
        }
      } catch {
        // silent fail
      }
    };

    fetchCounters();
    const interval = setInterval(fetchCounters, 20000);
    return () => clearInterval(interval);
  }, [isAuthenticated, location.pathname]);

  const isActive = (path) => location.pathname === path;

  // Role-specific badge and styling
  const getRoleHeaderBadge = () => {
    if (role === 'admin') {
      return (
        <span className="text-[11px] font-bold bg-rose-50 text-rose-700 border border-rose-200 px-2 py-0.5 rounded-full flex items-center gap-1">
          <Shield className="w-3 h-3 text-rose-600" />
          Chief Admin Deck
        </span>
      );
    }
    if (role === 'handler') {
      return (
        <span className="text-[11px] font-bold bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-full flex items-center gap-1">
          <Wrench className="w-3 h-3 text-blue-600" />
          Facility Operations
        </span>
      );
    }
    if (role === 'complainant') {
      return (
        <span className="text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full flex items-center gap-1">
          <GraduationCap className="w-3 h-3 text-emerald-600" />
          Student Portal
        </span>
      );
    }
    return (
      <span className="text-[11px] font-semibold bg-slate-100 text-slate-600 border border-slate-200 px-2 py-0.5 rounded-full">
        Public Civic Portal
      </span>
    );
  };

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo & Dynamic Role Tag */}
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-700 to-indigo-900 flex items-center justify-center text-white shadow-md shadow-indigo-200 flex-shrink-0">
              <Compass className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg text-slate-900 tracking-tight">शिकायत Karo</span>
                {getRoleHeaderBadge()}
              </div>
              <p className="text-[11px] text-slate-500 leading-tight">
                {role === 'admin'
                  ? 'University Governance & Incident Redressal'
                  : role === 'handler'
                  ? 'Estate & Facility Dispatch Command'
                  : role === 'complainant'
                  ? 'Campus Grievance Redressal System'
                  : 'Intelligent Grievance Redressal'}
              </p>
            </div>
          </Link>

          {/* Desktop Nav Links (Tailored to Role) */}
          <nav className="hidden md:flex items-center gap-1 font-medium text-xs sm:text-sm text-slate-600">
            {/* 1. CHIEF ADMIN NAV */}
            {role === 'admin' && (
              <>
                <Link
                  to="/"
                  className={`px-3 py-2 rounded-lg transition ${
                    isActive('/') ? 'bg-indigo-50 text-indigo-700 font-semibold' : 'hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  Executive Command
                </Link>
                <Link
                  to="/incidents"
                  className={`px-3 py-2 rounded-lg transition flex items-center gap-1.5 ${
                    isActive('/incidents') ? 'bg-indigo-50 text-indigo-700 font-semibold' : 'hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  <AlertTriangle className="w-4 h-4 text-slate-500" />
                  All Incidents
                </Link>
                <Link
                  to="/suggestions"
                  className={`px-3 py-2 rounded-lg transition flex items-center gap-1.5 ${
                    isActive('/suggestions') ? 'bg-indigo-50 text-indigo-700 font-semibold' : 'hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  <Layers className="w-4 h-4 text-amber-500" />
                  AI Clusters
                  {pendingSuggestionsCount > 0 && (
                    <span className="ml-1 bg-amber-500 text-white text-[10px] font-bold px-1.5 py-0.2 rounded-full">
                      {pendingSuggestionsCount}
                    </span>
                  )}
                </Link>
                <Link
                  to="/submit"
                  className={`px-3 py-2 rounded-lg transition flex items-center gap-1.5 ${
                    isActive('/submit') ? 'bg-indigo-50 text-indigo-700 font-semibold' : 'hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  <FileText className="w-4 h-4" />
                  File Grievance
                </Link>
              </>
            )}

            {/* 2. FACILITY HANDLER NAV */}
            {role === 'handler' && (
              <>
                <Link
                  to="/"
                  className={`px-3 py-2 rounded-lg transition ${
                    isActive('/') ? 'bg-blue-50 text-blue-700 font-semibold' : 'hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  Operations Deck
                </Link>
                <Link
                  to="/incidents"
                  className={`px-3 py-2 rounded-lg transition flex items-center gap-1.5 ${
                    isActive('/incidents') ? 'bg-blue-50 text-blue-700 font-semibold' : 'hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  <Building className="w-4 h-4 text-blue-600" />
                  Department Work Orders
                </Link>
                <Link
                  to="/suggestions"
                  className={`px-3 py-2 rounded-lg transition flex items-center gap-1.5 ${
                    isActive('/suggestions') ? 'bg-blue-50 text-blue-700 font-semibold' : 'hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  <Layers className="w-4 h-4 text-amber-500" />
                  Cluster Review
                  {pendingSuggestionsCount > 0 && (
                    <span className="ml-1 bg-amber-500 text-white text-[10px] font-bold px-1.5 py-0.2 rounded-full">
                      {pendingSuggestionsCount}
                    </span>
                  )}
                </Link>
              </>
            )}

            {/* 3. STUDENT COMPLAINANT NAV */}
            {role === 'complainant' && (
              <>
                <Link
                  to="/"
                  className={`px-3 py-2 rounded-lg transition ${
                    isActive('/') ? 'bg-emerald-50 text-emerald-700 font-semibold' : 'hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  Student Portal
                </Link>
                <Link
                  to="/submit"
                  className={`px-3 py-2 rounded-lg transition flex items-center gap-1.5 ${
                    isActive('/submit') ? 'bg-emerald-50 text-emerald-700 font-semibold' : 'hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  <FileText className="w-4 h-4 text-emerald-600" />
                  Report Issue
                </Link>
                <Link
                  to="/my-complaints"
                  className={`px-3 py-2 rounded-lg transition flex items-center gap-1.5 ${
                    isActive('/my-complaints') ? 'bg-emerald-50 text-emerald-700 font-semibold' : 'hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  My Grievances
                </Link>
                <Link
                  to="/track"
                  className={`px-3 py-2 rounded-lg transition flex items-center gap-1.5 ${
                    isActive('/track') ? 'bg-emerald-50 text-emerald-700 font-semibold' : 'hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  <Search className="w-4 h-4" />
                  Track Status
                </Link>
              </>
            )}

            {/* 4. GUEST NAV */}
            {!isAuthenticated && (
              <>
                <Link
                  to="/"
                  className={`px-3 py-2 rounded-lg transition ${
                    isActive('/') ? 'bg-indigo-50 text-indigo-700 font-semibold' : 'hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  Overview & Heatmap
                </Link>
                <Link
                  to="/submit"
                  className={`px-3 py-2 rounded-lg transition flex items-center gap-1.5 ${
                    isActive('/submit') ? 'bg-indigo-50 text-indigo-700 font-semibold' : 'hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  <FileText className="w-4 h-4" />
                  File Grievance
                </Link>
                <Link
                  to="/track"
                  className={`px-3 py-2 rounded-lg transition flex items-center gap-1.5 ${
                    isActive('/track') ? 'bg-indigo-50 text-indigo-700 font-semibold' : 'hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  <Search className="w-4 h-4" />
                  Track by Access Code
                </Link>
              </>
            )}

            {/* Notifications (For all logged in users) */}
            {isAuthenticated && (
              <Link
                to="/notifications"
                className={`p-2 rounded-lg transition relative flex items-center ${
                  isActive('/notifications') ? 'bg-indigo-50 text-indigo-700 font-semibold' : 'hover:bg-slate-100 text-slate-600'
                }`}
                title="Notifications"
              >
                <Bell className="w-4 h-4" />
                {unreadNotificationsCount > 0 && (
                  <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-rose-500"></span>
                )}
              </Link>
            )}

            {/* Demo Simulator Link (Available for evaluation) */}
            <Link
              to="/demo"
              className={`px-2.5 py-1.5 rounded-lg transition flex items-center gap-1 text-xs ${
                isActive('/demo') ? 'bg-amber-100 text-amber-900 font-semibold' : 'bg-slate-100 hover:bg-amber-50 text-slate-700'
              }`}
            >
              <PlayCircle className="w-3.5 h-3.5 text-amber-600" />
              Simulator
            </Link>
          </nav>

          {/* User Profile / Auth Action */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated ? (
              <div className="flex items-center gap-2.5">
                <div className="text-right">
                  <div className="text-xs font-bold text-slate-900">{user.full_name}</div>
                  <div className="text-[10px] text-slate-500 uppercase font-semibold">
                    {role === 'admin'
                      ? 'Chief Administrator'
                      : role === 'handler'
                      ? 'Facility Incharge'
                      : 'Student Citizen'}
                  </div>
                </div>
                <button
                  onClick={logout}
                  className="p-2 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition"
                  title="Logout"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition"
              >
                <LogIn className="w-4 h-4" />
                Sign In / Login
              </Link>
            )}
          </div>

          {/* Mobile hamburger */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="p-2 rounded-lg text-slate-600 hover:bg-slate-100"
            >
              {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white px-4 pt-2 pb-6 space-y-1">
          <Link
            to="/"
            onClick={() => setMobileOpen(false)}
            className="block px-3 py-2 rounded-lg text-base font-medium text-slate-800 hover:bg-slate-100"
          >
            {role === 'admin'
              ? 'Executive Command Deck'
              : role === 'handler'
              ? 'Operations Deck'
              : role === 'complainant'
              ? 'Student Portal'
              : 'Home & Heatmap'}
          </Link>
          <Link
            to="/submit"
            onClick={() => setMobileOpen(false)}
            className="block px-3 py-2 rounded-lg text-base font-medium text-slate-800 hover:bg-slate-100"
          >
            File Grievance
          </Link>
          <Link
            to="/track"
            onClick={() => setMobileOpen(false)}
            className="block px-3 py-2 rounded-lg text-base font-medium text-slate-800 hover:bg-slate-100"
          >
            Track Grievance
          </Link>
          {(role === 'admin' || role === 'handler') && (
            <>
              <Link
                to="/suggestions"
                onClick={() => setMobileOpen(false)}
                className="block px-3 py-2 rounded-lg text-base font-medium text-slate-800 hover:bg-slate-100"
              >
                AI Suggestions ({pendingSuggestionsCount})
              </Link>
              <Link
                to="/incidents"
                onClick={() => setMobileOpen(false)}
                className="block px-3 py-2 rounded-lg text-base font-medium text-slate-800 hover:bg-slate-100"
              >
                {role === 'handler' ? 'Department Work Orders' : 'Incident Management'}
              </Link>
            </>
          )}
          {isAuthenticated && (
            <Link
              to="/my-complaints"
              onClick={() => setMobileOpen(false)}
              className="block px-3 py-2 rounded-lg text-base font-medium text-slate-800 hover:bg-slate-100"
            >
              My Submitted Grievances
            </Link>
          )}
          <Link
            to="/demo"
            onClick={() => setMobileOpen(false)}
            className="block px-3 py-2 rounded-lg text-base font-medium text-amber-700 hover:bg-amber-50"
          >
            SLA Time Machine & Simulator
          </Link>
          <div className="pt-4 border-t border-slate-100">
            {isAuthenticated ? (
              <button
                onClick={() => {
                  logout();
                  setMobileOpen(false);
                }}
                className="w-full text-left px-3 py-2 rounded-lg text-base font-medium text-rose-600 hover:bg-rose-50"
              >
                Sign Out ({user.full_name})
              </button>
            ) : (
              <Link
                to="/login"
                onClick={() => setMobileOpen(false)}
                className="block w-full text-center px-4 py-2 bg-indigo-600 text-white rounded-lg font-semibold"
              >
                Sign In
              </Link>
            )}
          </div>
        </div>
      )}
    </header>
  );
};

export default Navbar;
