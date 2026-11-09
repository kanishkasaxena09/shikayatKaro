import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ToastProvider } from './context/ToastContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import DemoBar from './components/DemoBar';

// Pages
import Dashboard from './pages/Dashboard';
import SubmitComplaint from './pages/SubmitComplaint';
import TrackComplaint from './pages/TrackComplaint';
import Suggestions from './pages/Suggestions';
import IncidentsList from './pages/IncidentsList';
import IncidentDetail from './pages/IncidentDetail';
import MyComplaints from './pages/MyComplaints';
import Notifications from './pages/Notifications';
import DemoControl from './pages/DemoControl';
import Login from './pages/Login';

// Protected Route Guard for Admin / Handler
const StaffRoute = ({ children }) => {
  const { role, isAuthenticated, loading } = useAuth();
  if (loading) return null;
  if (!isAuthenticated || (role !== 'admin' && role !== 'handler')) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

// Protected Route Guard for Authenticated Users
const UserRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return null;
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <BrowserRouter>
          <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
            {/* Top Interactive Demo Persona & Virtual Clock Bar */}
            <DemoBar />

            {/* Main Navigation Bar */}
            <Navbar />

            {/* Content Area */}
            <main className="flex-1">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/submit" element={<SubmitComplaint />} />
                <Route path="/track" element={<TrackComplaint />} />
                <Route
                  path="/suggestions"
                  element={
                    <StaffRoute>
                      <Suggestions />
                    </StaffRoute>
                  }
                />
                <Route
                  path="/incidents"
                  element={
                    <StaffRoute>
                      <IncidentsList />
                    </StaffRoute>
                  }
                />
                <Route
                  path="/incidents/:id"
                  element={
                    <StaffRoute>
                      <IncidentDetail />
                    </StaffRoute>
                  }
                />
                <Route
                  path="/my-complaints"
                  element={
                    <UserRoute>
                      <MyComplaints />
                    </UserRoute>
                  }
                />
                <Route
                  path="/notifications"
                  element={
                    <UserRoute>
                      <Notifications />
                    </UserRoute>
                  }
                />
                <Route path="/demo" element={<DemoControl />} />
                <Route path="/login" element={<Login />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>

            {/* Modern Footer */}
            <footer className="bg-white border-t border-slate-200 mt-12 py-6 text-xs text-slate-500">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-800">शिकायत Karo</span>
                  <span>•</span>
                  <span>Intelligent Grievance Redressal and Incident Aggregation Platform</span>
                </div>
                <div className="flex items-center gap-4 text-slate-400">
                  <span>Backend API: 127.0.0.1:8000</span>
                  <span>•</span>
                  <span>Version 1.0.0</span>
                </div>
              </div>
            </footer>
          </div>
        </BrowserRouter>
      </AuthProvider>
    </ToastProvider>
  );
}

export default App;
