import React, { useState, useEffect } from 'react';
import { Shield, Eye, EyeOff, AlertCircle, CheckCircle } from 'lucide-react';
import { ThemeToggle } from '../components/ThemeToggle.jsx';
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
    <div className="login-container">
      <div className="auth-theme-toggle">
        <ThemeToggle size="sm" />
      </div>
      <div className="login-card">
        {/* Brand Header */}
        <div className="login-header">
          <div className="auth-logo-badge">
            <Shield aria-hidden="true" />
          </div>
          <h1 className="brand-title">
            PhoenixML
          </h1>
          <p className="brand-subtitle">
            MLOps Decision-Support Platform
          </p>
        </div>

        {/* Alerts & Feedback */}
        {error && (
          <div className="alert alert-error" role="alert">
            <AlertCircle className="icon-sm" aria-hidden="true" />
            <span>{error}</span>
          </div>
        )}

        {!error && sessionExpired && (
          <div className="alert alert-warning" role="alert">
            <AlertCircle className="icon-sm" aria-hidden="true" />
            <span>Your session has expired. Please sign in again.</span>
          </div>
        )}

        {!error && !sessionExpired && initialMessage && (
          <div
            className={cn('alert', initialMessageType === 'success' ? 'alert-success' : 'alert-info')}
            role="status"
          >
            {initialMessageType === 'success' ? (
              <CheckCircle className="icon-sm" aria-hidden="true" />
            ) : (
              <AlertCircle className="icon-sm" aria-hidden="true" />
            )}
            <span>{initialMessage}</span>
          </div>
        )}

        {!error && !sessionExpired && !initialMessage && (
          <div className="auth-notice">
            Please sign in to access operator controls and model governance.
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label className="form-label" htmlFor="login-username">
              Email or Username
            </label>
            <input
              id="login-username"
              type="text"
              className="form-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              placeholder="Enter your email or username"
              autoComplete="username"
              autoFocus={!prefillUsername}
              disabled={isBusy}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="login-password">
              Password
            </label>
            <div className="password-input-wrapper">
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                className="form-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="Enter your password"
                autoComplete="current-password"
                disabled={isBusy}
              />
              <button
                type="button"
                className="password-toggle-btn"
                onClick={() => setShowPassword(!showPassword)}
                title={showPassword ? 'Hide password' : 'Show password'}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                tabIndex={-1}
              >
                {showPassword ? <EyeOff className="icon-sm" /> : <Eye className="icon-sm" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={isBusy}
          >
            {isBusy && <span className="btn-spinner" aria-hidden="true" />}
            <span>{isBusy ? 'Signing in...' : 'Sign In'}</span>
          </button>
        </form>

        {/* Footer */}
        <div className="auth-footer">
          <span>Need an operator account?</span>
          <button
            type="button"
            className="auth-link"
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
