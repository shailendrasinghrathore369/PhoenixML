import React, { useState } from 'react';
import { Shield, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { ThemeToggle } from '../components/ThemeToggle.jsx';

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
            Create Account
          </h1>
          <p className="brand-subtitle">
            Register for PhoenixML Decision Support
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="alert alert-error" role="alert">
            <AlertCircle className="icon-sm" aria-hidden="true" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label className="form-label" htmlFor="signup-username">
              Username
            </label>
            <input
              id="signup-username"
              type="text"
              className="form-input"
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
            <div className="form-hint">
              Must be between 3 and 50 characters.
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-email">
              Email Address
            </label>
            <input
              id="signup-email"
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="operator@example.com"
              autoComplete="email"
              disabled={isBusy}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-password">
              Password
            </label>
            <div className="password-input-wrapper">
              <input
                id="signup-password"
                type={showPassword ? 'text' : 'password'}
                className="form-input"
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
                className="password-toggle-btn"
                onClick={() => setShowPassword(!showPassword)}
                title={showPassword ? 'Hide password' : 'Show password'}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="icon-sm" /> : <Eye className="icon-sm" />}
              </button>
            </div>
            <div className="form-hint">
              At least 8 characters required.
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-confirm-password">
              Confirm Password
            </label>
            <div className="password-input-wrapper">
              <input
                id="signup-confirm-password"
                type={showConfirmPassword ? 'text' : 'password'}
                className="form-input"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                placeholder="Re-enter your password"
                autoComplete="new-password"
                disabled={isBusy}
              />
              <button
                type="button"
                className="password-toggle-btn"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                title={showConfirmPassword ? 'Hide password' : 'Show password'}
                aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
              >
                {showConfirmPassword ? <EyeOff className="icon-sm" /> : <Eye className="icon-sm" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={isBusy}
          >
            {isBusy && <span className="btn-spinner" aria-hidden="true" />}
            <span>{isBusy ? 'Creating Account...' : 'Create Account'}</span>
          </button>
        </form>

        {/* Footer */}
        <div className="auth-footer">
          <span>Already have an account?</span>
          <button
            type="button"
            className="auth-link"
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
