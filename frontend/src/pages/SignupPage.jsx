import React, { useState } from 'react';
import { Shield, Lock, User, Mail, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { cn } from '../lib/utils.js';

export function SignupPage({
  onSignup,
  onSwitchToLogin,
  loading = false,
}) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    const trimmedUsername = username.trim();
    const trimmedEmail = email.trim();

    if (!trimmedUsername) {
      setError('Username is required.');
      return;
    }
    if (trimmedUsername.length < 3) {
      setError('Username must be at least 3 characters long.');
      return;
    }
    if (trimmedUsername.length > 50) {
      setError('Username must be 50 characters or less.');
      return;
    }
    if (!trimmedEmail) {
      setError('Email address is required.');
      return;
    }
    if (!password) {
      setError('Password is required.');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match. Please verify your password confirmation.');
      return;
    }

    setSubmitting(true);
    try {
      await onSignup({
        username: trimmedUsername,
        email: trimmedEmail,
        password,
      });
    } catch (err) {
      setError(err.message || 'Registration failed. Please check your information and try again.');
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
            Create Account
          </h1>
          <p className="brand-subtitle text-xs text-slate-400 mt-1 uppercase tracking-wider font-semibold">
            Register for PhoenixML Decision Support
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="alert alert-error flex items-start gap-2.5 p-3.5 rounded-lg border border-rose-500/30 bg-rose-950/20 text-rose-300 text-xs mb-4">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="form-group">
            <label className="form-label block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5" htmlFor="signup-username">
              Username
            </label>
            <input
              id="signup-username"
              type="text"
              className="form-input w-full px-3.5 py-2.5 text-xs rounded-lg border border-slate-700 bg-slate-950 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              minLength={3}
              maxLength={50}
              placeholder="Choose a username (min 3 chars)"
              autoComplete="username"
              autoFocus
              disabled={isBusy}
            />
            <div className="form-hint text-[11px] text-slate-500 mt-1">
              Must be between 3 and 50 characters.
            </div>
          </div>

          <div className="form-group">
            <label className="form-label block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5" htmlFor="signup-email">
              Email Address
            </label>
            <input
              id="signup-email"
              type="email"
              className="form-input w-full px-3.5 py-2.5 text-xs rounded-lg border border-slate-700 bg-slate-950 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="operator@example.com"
              autoComplete="email"
              disabled={isBusy}
            />
          </div>

          <div className="form-group">
            <label className="form-label block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5" htmlFor="signup-password">
              Password
            </label>
            <div className="relative">
              <input
                id="signup-password"
                type={showPassword ? 'text' : 'password'}
                className="form-input w-full px-3.5 py-2.5 pr-10 text-xs rounded-lg border border-slate-700 bg-slate-950 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                placeholder="Minimum 8 characters"
                autoComplete="new-password"
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
            <div className="form-hint text-[11px] text-slate-500 mt-1">
              At least 8 characters required.
            </div>
          </div>

          <div className="form-group">
            <label className="form-label block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5" htmlFor="signup-confirm-password">
              Confirm Password
            </label>
            <div className="relative">
              <input
                id="signup-confirm-password"
                type={showConfirmPassword ? 'text' : 'password'}
                className="form-input w-full px-3.5 py-2.5 pr-10 text-xs rounded-lg border border-slate-700 bg-slate-950 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                placeholder="Re-enter your password"
                autoComplete="new-password"
                disabled={isBusy}
              />
              <button
                type="button"
                className="password-toggle-btn absolute right-2.5 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-200"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                title={showConfirmPassword ? 'Hide password' : 'Show password'}
                tabIndex={-1}
              >
                {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary w-full py-2.5 px-4 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-50 flex items-center justify-center gap-2 mt-2"
            disabled={isBusy}
          >
            {isBusy && <span className="w-3.5 h-3.5 rounded-full border-2 border-white/30 border-t-white animate-spin" />}
            <span>{isBusy ? 'Creating Account...' : 'Create Account'}</span>
          </button>
        </form>

        {/* Footer */}
        <div className="auth-footer mt-6 pt-4 border-t border-slate-800 text-center text-xs text-slate-400 flex items-center justify-center gap-1.5">
          <span>Already have an account?</span>
          <button
            type="button"
            className="auth-link text-blue-400 hover:text-blue-300 font-semibold focus:outline-none underline-offset-4 hover:underline"
            onClick={onSwitchToLogin}
            disabled={isBusy}
          >
            Sign In
          </button>
        </div>
      </div>
    </div>
  );
}
