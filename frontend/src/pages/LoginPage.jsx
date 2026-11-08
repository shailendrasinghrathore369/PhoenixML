import React, { useState, useEffect } from 'react';
import { Shield, Lock, User, Eye, EyeOff, AlertCircle, CheckCircle } from 'lucide-react';
import { cn } from '../lib/utils.js';

export function LoginPage({
  onLogin,
  onSwitchToSignup,
  sessionExpired = false,
  initialMessage = null,
  initialMessageType = 'info',
  prefillUsername = '',
  loading = false,
}) {
  const [username, setUsername] = useState(prefillUsername);
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (prefillUsername) {
      setUsername(prefillUsername);
    }
  }, [prefillUsername]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    const trimmed = username.trim();
    if (!trimmed) {
      setError('Please enter your email or username.');
      return;
    }
    if (!password) {
      setError('Please enter your password.');
      return;
    }

    setSubmitting(true);
    try {
      await onLogin(trimmed, password);
    } catch (err) {
      setError(err.message || 'Login failed. Please verify your credentials and try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const isBusy = loading || submitting;

  return (
    <div className="login-container min-h-screen w-full flex items-center justify-center p-4 bg-slate-950 text-slate-100">
      <div className="login-card w-full max-w-md p-8 rounded-2xl border border-slate-800 bg-slate-900/90 shadow-2xl backdrop-blur-sm">
        {/* Brand Header */}
        <div className="login-header text-center mb-6">
          <div className="inline-flex p-3 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/20 mb-3 ring-1 ring-blue-500/30">
            <Shield className="w-8 h-8" />
          </div>
          <h1 className="brand-title text-xl font-bold tracking-tight text-slate-100">
            PhoenixML
          </h1>
          <p className="brand-subtitle text-xs text-slate-400 mt-1 uppercase tracking-wider font-semibold">
            MLOps Decision-Support Platform
          </p>
        </div>

        {/* Alerts & Feedback */}
        {error && (
          <div className="alert alert-error flex items-start gap-2.5 p-3.5 rounded-lg border border-rose-500/30 bg-rose-950/20 text-rose-300 text-xs mb-4">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {!error && sessionExpired && (
          <div className="alert alert-warning flex items-start gap-2.5 p-3.5 rounded-lg border border-amber-500/30 bg-amber-950/20 text-amber-300 text-xs mb-4">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>Your session has expired. Please sign in again.</span>
          </div>
        )}

        {!error && !sessionExpired && initialMessage && (
          <div
            className={cn(
              'alert flex items-start gap-2.5 p-3.5 rounded-lg border text-xs mb-4',
              initialMessageType === 'success'
                ? 'alert-success border-emerald-500/30 bg-emerald-950/20 text-emerald-300'
                : 'alert-info border-blue-500/30 bg-blue-950/20 text-blue-300'
            )}
          >
            {initialMessageType === 'success' ? (
              <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-emerald-400" />
            ) : (
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-blue-400" />
            )}
            <span>{initialMessage}</span>
          </div>
        )}

        {!error && !sessionExpired && !initialMessage && (
          <div className="auth-notice text-xs text-slate-400 text-center mb-5">
            Please sign in to access operator controls and model governance.
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="form-group">
            <label className="form-label block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5" htmlFor="login-username">
              Email or Username
            </label>
            <div className="relative">
              <input
                id="login-username"
                type="text"
                className="form-input w-full px-3.5 py-2.5 text-xs rounded-lg border border-slate-700 bg-slate-950 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                placeholder="Enter your email or username"
                autoComplete="username"
                autoFocus={!prefillUsername}
                disabled={isBusy}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5" htmlFor="login-password">
              Password
            </label>
            <div className="relative">
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                className="form-input w-full px-3.5 py-2.5 pr-10 text-xs rounded-lg border border-slate-700 bg-slate-950 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="Enter your password"
                autoComplete="current-password"
                disabled={isBusy}
              />
              <button
                type="button"
                className="password-toggle-btn absolute right-2.5 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-200"
                onClick={() => setShowPassword(!showPassword)}
                title={showPassword ? 'Hide password' : 'Show password'}
                tabIndex={-1}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary w-full py-2.5 px-4 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-50 flex items-center justify-center gap-2 mt-2"
            disabled={isBusy}
          >
            {isBusy && <span className="w-3.5 h-3.5 rounded-full border-2 border-white/30 border-t-white animate-spin" />}
            <span>{isBusy ? 'Signing in...' : 'Sign In'}</span>
          </button>
        </form>

        {/* Footer */}
        <div className="auth-footer mt-6 pt-4 border-t border-slate-800 text-center text-xs text-slate-400 flex items-center justify-center gap-1.5">
          <span>Need an operator account?</span>
          <button
            type="button"
            className="auth-link text-blue-400 hover:text-blue-300 font-semibold focus:outline-none underline-offset-4 hover:underline"
            onClick={onSwitchToSignup}
            disabled={isBusy}
          >
            Register Here
          </button>
        </div>
      </div>
    </div>
  );
}
