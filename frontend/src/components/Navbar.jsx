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

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo */}
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-700 to-indigo-900 flex items-center justify-center text-white shadow-md shadow-indigo-200">
              <Compass className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg text-slate-900 tracking-tight">शिकायत Karo</span>
                <span className="text-[11px] font-semibold bg-indigo-50 text-indigo-700 px-1.5 py-0.5 rounded border border-indigo-200">
                  AI Aggregator
                </span>
              </div>
              <p className="text-[11px] text-slate-500 leading-tight">Intelligent Grievance Redressal</p>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-1 font-medium text-sm text-slate-600">
            <Link
              to="/"
              className={`px-3 py-2 rounded-lg transition ${
                isActive('/') ? 'bg-indigo-50 text-indigo-700 font-semibold' : 'hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              Dashboard & Heatmap
            </Link>

            <Link
              to="/submit"
              className={`px-3 py-2 rounded-lg transition flex items-center gap-1.5 ${
                isActive('/submit') ? 'bg-indigo-50 text-indigo-700 font-semibold' : 'hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              <FileText className="w-4 h-4" />
              File Grievance
            </Link>

            <Link
              to="/track"
              className={`px-3 py-2 rounded-lg transition flex items-center gap-1.5 ${
                isActive('/track') ? 'bg-indigo-50 text-indigo-700 font-semibold' : 'hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              <Search className="w-4 h-4" />
              Track
            </Link>

            {/* Admin and Handler: Suggestions */}
            {(role === 'admin' || role === 'handler') && (
              <Link
                to="/suggestions"
                className={`px-3 py-2 rounded-lg transition flex items-center gap-1.5 ${
                  isActive('/suggestions')
                    ? 'bg-indigo-50 text-indigo-700 font-semibold'
                    : 'hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                <Layers className="w-4 h-4" />
                Suggestions
                {pendingSuggestionsCount > 0 && (
                  <span className="ml-1 bg-amber-500 text-white text-[11px] font-bold px-1.5 py-0.2 rounded-full">
                    {pendingSuggestionsCount}
                  </span>
                )}
              </Link>
            )}

            {/* Admin and Handler: Incidents */}
            {(role === 'admin' || role === 'handler') && (
              <Link
                to="/incidents"
                className={`px-3 py-2 rounded-lg transition flex items-center gap-1.5 ${
                  isActive('/incidents')
                    ? 'bg-indigo-50 text-indigo-700 font-semibold'
                    : 'hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                <AlertTriangle className="w-4 h-4" />
                Incidents
              </Link>
            )}

            {/* Authenticated Complainant: My Complaints */}
            {isAuthenticated && (
              <Link
                to="/my-complaints"
                className={`px-3 py-2 rounded-lg transition flex items-center gap-1.5 ${
                  isActive('/my-complaints')
                    ? 'bg-indigo-50 text-indigo-700 font-semibold'
                    : 'hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                <CheckCircle2 className="w-4 h-4" />
                My Grievances
              </Link>
            )}

            {/* Notifications */}
            {isAuthenticated && (
              <Link
                to="/notifications"
                className={`px-3 py-2 rounded-lg transition relative flex items-center ${
                  isActive('/notifications')
                    ? 'bg-indigo-50 text-indigo-700 font-semibold'
                    : 'hover:bg-slate-100 hover:text-slate-900'
                }`}
                title="Notifications"
              >
                <Bell className="w-4 h-4" />
                {unreadNotificationsCount > 0 && (
                  <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-rose-500"></span>
                )}
              </Link>
            )}

            {/* Simulator Link */}
            <Link
              to="/demo"
              className={`px-3 py-2 rounded-lg transition flex items-center gap-1 text-slate-700 ${
                isActive('/demo') ? 'bg-amber-100 text-amber-900 font-semibold' : 'hover:bg-slate-100'
              }`}
            >
              <PlayCircle className="w-4 h-4 text-amber-600" />
              Demo Simulator
            </Link>
          </nav>

          {/* User Profile / Auth Action */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-xs font-bold text-slate-900">{user.full_name}</div>
                  <div className="text-[11px] text-slate-500 uppercase font-semibold">{user.role}</div>
                </div>
                <button
                  onClick={logout}
                  className="p-2 rounded-lg text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition"
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
                Staff / Student Login
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
            Dashboard & Heatmap
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
                System Suggestions ({pendingSuggestionsCount})
              </Link>
              <Link
                to="/incidents"
                onClick={() => setMobileOpen(false)}
                className="block px-3 py-2 rounded-lg text-base font-medium text-slate-800 hover:bg-slate-100"
              >
                Incident Management
              </Link>
            </>
          )}
          {isAuthenticated && (
            <Link
              to="/my-complaints"
              onClick={() => setMobileOpen(false)}
              className="block px-3 py-2 rounded-lg text-base font-medium text-slate-800 hover:bg-slate-100"
            >
              My Filed Grievances
            </Link>
          )}
          <Link
            to="/demo"
            onClick={() => setMobileOpen(false)}
            className="block px-3 py-2 rounded-lg text-base font-medium text-amber-700 hover:bg-amber-50"
          >
            Demo Story Simulator
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
                Logout ({user.full_name})
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
