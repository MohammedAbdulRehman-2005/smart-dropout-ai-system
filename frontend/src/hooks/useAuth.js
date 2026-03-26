import { useMemo } from 'react';

/**
 * Decode a JWT payload without verification (client-side display only).
 * Never use for security decisions — the backend enforces actual auth.
 */
function decodeJWT(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

export function useAuth() {
  const token = localStorage.getItem('token');

  const payload = useMemo(() => {
    if (!token) return null;
    return decodeJWT(token);
  }, [token]);

  const isAuthenticated = !!token;

  // JWT payload shape: { sub: email, role: "admin"|"teacher"|"counselor", ... }
  const role = payload?.role || localStorage.getItem('user_role') || null;
  const name = payload?.full_name || localStorage.getItem('user_name') || payload?.sub || 'User';
  const email = payload?.sub || '';

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_name');
    window.location.href = '/login';
  };

  const hasRole = (requiredRole) => {
    if (!role) return false;
    if (role === 'admin') return true; // admin can access everything
    return role === requiredRole;
  };

  const canAccessAdmin = () => role === 'admin';
  const canAccessCounselor = () => role === 'admin' || role === 'counselor';
  const canAccessTeacher = () => ['admin', 'teacher', 'counselor'].includes(role);

  return {
    isAuthenticated,
    token,
    role,
    name,
    email,
    logout,
    hasRole,
    canAccessAdmin,
    canAccessCounselor,
    canAccessTeacher,
  };
}
