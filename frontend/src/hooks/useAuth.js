import { useState, useEffect, useCallback } from 'react';
import { api, authStorage } from '../lib/api.js';

export function useAuth(onNotify) {
  const [user, setUser] = useState(() => {
    const token = authStorage.getToken();
    const storedUser = authStorage.getUser();
    return token && storedUser ? storedUser : null;
  });
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'signup'
  const [authMessage, setAuthMessage] = useState(null);
  const [prefillUsername, setPrefillUsername] = useState('');
  const [sessionExpired, setSessionExpired] = useState(false);
  const [loading, setLoading] = useState(false);

  // Handle unauthorized session expiration event
  useEffect(() => {
    const handleUnauthorized = (e) => {
      setUser(null);
      const isExpired = e?.detail?.reason === 'session_expired';
      setSessionExpired(isExpired);
      setAuthMode('login');
      if (isExpired) {
        setAuthMessage({ type: 'warning', text: 'Your session has expired. Please sign in again.' });
        if (onNotify) {
          onNotify.warning?.('Your session has expired. Please sign in again.');
        }
      }
    };

    window.addEventListener('phoenixml-unauthorized', handleUnauthorized);
    return () => window.removeEventListener('phoenixml-unauthorized', handleUnauthorized);
  }, [onNotify]);

  const login = useCallback(async (username, password) => {
    setLoading(true);
    try {
      const res = await api.login(username, password);
      setUser(res.user);
      setSessionExpired(false);
      setAuthMessage(null);
      if (onNotify) {
        onNotify.success?.(`Welcome back, ${res.user.email}!`);
      }
      return res.user;
    } finally {
      setLoading(false);
    }
  }, [onNotify]);

  const register = useCallback(async ({ username, email, password }) => {
    setLoading(true);
    try {
      const res = await api.register({ username, email, password });
      setAuthMode('login');
      setPrefillUsername(username);
      setSessionExpired(false);
      const msg = res?.message || 'Account created successfully! Please sign in with your credentials.';
      setAuthMessage({ type: 'success', text: msg });
      if (onNotify) {
        onNotify.success?.(msg);
      }
      return res;
    } finally {
      setLoading(false);
    }
  }, [onNotify]);

  const logout = useCallback(async () => {
    setLoading(true);
    try {
      await api.logout();
    } finally {
      setUser(null);
      setSessionExpired(false);
      setAuthMessage(null);
      setAuthMode('login');
      setLoading(false);
      if (onNotify) {
        onNotify.info?.('Signed out successfully.');
      }
    }
  }, [onNotify]);

  const switchToSignup = useCallback(() => {
    setAuthMode('signup');
    setAuthMessage(null);
  }, []);

  const switchToLogin = useCallback(() => {
    setAuthMode('login');
    setAuthMessage(null);
  }, []);

  return {
    user,
    setUser,
    authMode,
    setAuthMode,
    authMessage,
    setAuthMessage,
    prefillUsername,
    setPrefillUsername,
    sessionExpired,
    loading,
    login,
    register,
    logout,
    switchToSignup,
    switchToLogin,
  };
}
