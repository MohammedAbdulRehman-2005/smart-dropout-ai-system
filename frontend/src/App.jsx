import { BrowserRouter, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import React from 'react';
import AdminDashboard from './pages/AdminDashboard';
import StudentProfile from './pages/StudentProfile';
import CounselorPanel from './pages/CounselorPanel';
import Login from './pages/Login';
import Unauthorized from './pages/Unauthorized';
import ErrorBoundary from './components/ErrorBoundary';
import { ToastProvider } from './components/ToastProvider';
import { useAuth } from './hooks/useAuth';
import {
  LayoutDashboard, UserSearch, UserCheck, Brain,
  LogOut, Shield
} from 'lucide-react';

// ── Protected Route ──────────────────────────────────────────
function ProtectedRoute({ children, requiredRole }) {
  const { isAuthenticated, role } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole) {
    const allowed =
      role === 'admin' ||              // admin can access everything
      role === requiredRole ||         // exact role match
      (requiredRole === 'any');        // any authenticated user
    if (!allowed) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  return children;
}

// ── Navbar ───────────────────────────────────────────────────
function Navbar() {
  const { isAuthenticated, role, name, logout } = useAuth();
  const location = useLocation();

  if (!isAuthenticated || location.pathname === '/login') return null;

  const navLinks = [
    { to: '/admin', label: 'Dashboard', icon: LayoutDashboard, roles: ['admin'] },
    { to: '/counselor', label: 'Counselor', icon: UserCheck, roles: ['admin', 'counselor'] },
    { to: '/student', label: 'Student Search', icon: UserSearch, roles: ['admin', 'teacher', 'counselor'] },
  ].filter(link => link.roles.includes(role));

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="bg-white border-b border-gray-100 sticky top-0 z-30 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-8">
            <Link to="/admin" className="flex items-center gap-2.5">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-sm">
                <Brain size={18} className="text-white" />
              </div>
              <span className="text-lg font-black text-gray-900 tracking-tight">SmartEWS</span>
            </Link>

            {/* Nav Links */}
            <div className="hidden md:flex items-center gap-1">
              {navLinks.map(({ to, label, icon: Icon }) => (
                <Link
                  key={to}
                  to={to}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-semibold transition-all
                    ${isActive(to)
                      ? 'bg-blue-50 text-blue-700 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                >
                  <Icon size={16} />
                  {label}
                </Link>
              ))}
            </div>
          </div>

          {/* Right side */}
          <div className="flex items-center gap-3">
            {/* Role Badge */}
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-gray-50 border border-gray-100 rounded-xl">
              <Shield size={13} className="text-blue-500" />
              <span className="text-xs font-bold text-gray-600 capitalize">{role}</span>
            </div>

            {/* User + Logout */}
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-400 to-indigo-500 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                {name?.charAt(0)?.toUpperCase() || 'U'}
              </div>
              <span className="hidden sm:block text-sm font-semibold text-gray-700 max-w-[120px] truncate">
                {name}
              </span>
            </div>

            <button
              onClick={logout}
              className="flex items-center gap-1.5 px-3 py-2 text-sm font-semibold text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all"
              title="Logout"
            >
              <LogOut size={15} />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

// ── App Root ─────────────────────────────────────────────────
const App = () => {
  return (
    <BrowserRouter>
      <ToastProvider>
        <ErrorBoundary>
          <div className="min-h-screen bg-gray-50 flex flex-col">
            <Navbar />
            <main className="flex-1">
              <Routes>
                {/* Public */}
                <Route path="/login" element={<Login />} />
                <Route path="/unauthorized" element={<Unauthorized />} />

                {/* Redirect root */}
                <Route path="/" element={<Navigate to="/admin" replace />} />

                {/* Protected: Admin only */}
                <Route path="/admin" element={
                  <ProtectedRoute requiredRole="admin">
                    <ErrorBoundary>
                      <AdminDashboard />
                    </ErrorBoundary>
                  </ProtectedRoute>
                } />

                {/* Protected: Counselor + Admin */}
                <Route path="/counselor" element={
                  <ProtectedRoute requiredRole="counselor">
                    <ErrorBoundary>
                      <CounselorPanel />
                    </ErrorBoundary>
                  </ProtectedRoute>
                } />

                {/* Protected: Any authenticated user */}
                <Route path="/student" element={
                  <ProtectedRoute requiredRole="any">
                    <ErrorBoundary>
                      <StudentProfile />
                    </ErrorBoundary>
                  </ProtectedRoute>
                } />

                {/* Fallback */}
                <Route path="*" element={<Navigate to="/admin" replace />} />
              </Routes>
            </main>

            <footer className="bg-white border-t border-gray-100 py-3 text-center text-gray-400 text-xs">
              Smart School Dropout Early Warning System · Powered by XGBoost + SHAP · © 2026
            </footer>
          </div>
        </ErrorBoundary>
      </ToastProvider>
    </BrowserRouter>
  );
};

export default App;
