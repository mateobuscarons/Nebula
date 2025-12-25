import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { api } from './services/api';
import ProtectedRoute from './components/ProtectedRoute';
import LandingPage from './pages/LandingPage';
import SetupPage from './pages/SetupPage';
import PathApprovalPage from './pages/PathApprovalPage';
import Dashboard from './pages/Dashboard';
import LessonPage from './pages/LessonPage';
import AdminDashboard from './pages/AdminDashboard';
import './App.css';

function AppContent() {
  const { user, loading: authLoading } = useAuth();
  const [sessionState, setSessionState] = useState(null);
  const [loading, setLoading] = useState(true);

  // Cached dashboard data - persists across route changes
  const [dashboardData, setDashboardData] = useState(null);

  useEffect(() => {
    if (user) {
      loadSession();
    } else {
      setLoading(false);
    }
  }, [user]);

  const loadSession = async () => {
    try {
      const session = await api.getSession();
      console.log('📊 Session loaded:', session);
      setSessionState(session);
    } catch (error) {
      console.error('Failed to load session:', error);
    } finally {
      setLoading(false);
    }
  };

  const refreshSession = () => {
    setLoading(true);
    setDashboardData(null); // Clear cache on refresh
    loadSession();
  };

  if (authLoading || (user && loading)) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // Determine the correct route for logged-in users
  const getRedirectPath = () => {
    if (!sessionState) return '/setup'; // Default while loading
    switch (sessionState.state) {
      case 'new_user': return '/setup';
      case 'path_approval': return '/approve';
      case 'dashboard': return '/dashboard';
      default: return '/setup';
    }
  };

  return (
    <Routes>
      {/* Public Routes - redirect logged in users to appropriate page */}
      <Route path="/" element={
        user ? <Navigate to={getRedirectPath()} replace /> : <LandingPage />
      } />

      {/* Protected Routes */}
      <Route
        path="/setup"
        element={
          <ProtectedRoute>
            {sessionState?.state === 'path_approval' ? (
              <Navigate to="/approve" replace />
            ) : sessionState?.state === 'dashboard' ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <SetupPage onComplete={refreshSession} />
            )}
          </ProtectedRoute>
        }
      />

      <Route
        path="/approve"
        element={
          <ProtectedRoute>
            <PathApprovalPage sessionState={sessionState} onComplete={refreshSession} />
          </ProtectedRoute>
        }
      />

      <Route
        path="/path/view"
        element={
          <ProtectedRoute>
            <PathApprovalPage sessionState={sessionState} onComplete={refreshSession} viewOnly={true} />
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            {sessionState?.state === 'new_user' ? (
              <Navigate to="/setup" replace />
            ) : sessionState?.state === 'path_approval' ? (
              <Navigate to="/approve" replace />
            ) : (
              <Dashboard
                sessionState={sessionState}
                onRefresh={refreshSession}
                cachedData={dashboardData}
                setCachedData={setDashboardData}
              />
            )}
          </ProtectedRoute>
        }
      />

      <Route
        path="/lesson/:moduleNumber/:challengeNumber"
        element={
          <ProtectedRoute>
            <LessonPage onComplete={refreshSession} />
          </ProtectedRoute>
        }
      />

      <Route
        path="/admin"
        element={
          <ProtectedRoute>
            <AdminDashboard />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
