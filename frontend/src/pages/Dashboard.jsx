import React from 'react';
import { useAuth } from '../context/AuthContext';
import AdminDashboard from './dashboards/AdminDashboard';
import HandlerDashboard from './dashboards/HandlerDashboard';
import StudentDashboard from './dashboards/StudentDashboard';
import GuestDashboard from './dashboards/GuestDashboard';

export const Dashboard = () => {
  const { role, isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] text-slate-400 text-xs">
        Loading personalized role command center...
      </div>
    );
  }

  // Role-specific customized dashboard views
  if (isAuthenticated && role === 'admin') {
    return <AdminDashboard />;
  }

  if (isAuthenticated && role === 'handler') {
    return <HandlerDashboard />;
  }

  if (isAuthenticated && role === 'complainant') {
    return <StudentDashboard />;
  }

  // Public / Unauthenticated visitor view
  return <GuestDashboard />;
};

export default Dashboard;
