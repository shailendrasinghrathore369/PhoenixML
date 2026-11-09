import React from 'react';
import { Shield, RefreshCw, LogOut, User as UserIcon } from 'lucide-react';
import { StatusBadge } from './StatusBadge.jsx';
import { ThemeToggle } from './ThemeToggle.jsx';
import { cn } from '../lib/utils.js';

export function AppHeader({ user, onLogout, onRefresh, loading }) {
  const role = user?.role || 'VIEWER';

  return (
    <header className="app-header navbar">
      <div className="header-brand-wrap">
        <div className="header-brand-icon" aria-hidden="true">
          <Shield className="icon-md" />
        </div>
        <div className="header-brand-info">
          <div className="header-brand-title-group">
            <span className="header-brand-title">PhoenixML</span>
            <span className="header-tag">AIMD v1.0</span>
          </div>
          <span className="header-subtitle">
            Enterprise MLOps Decision-Support Platform
          </span>
        </div>
      </div>

      <div className="header-controls">
        <StatusBadge variant={role} size="sm">
          {role}
        </StatusBadge>

        <div className="header-user-badge">
          <UserIcon className="icon-sm" aria-hidden="true" />
          <span className="header-user-name">
            {user?.email || user?.username}
          </span>
        </div>

        <ThemeToggle size="sm" />

        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          title="Refresh Dashboard Overview"
          className="btn btn-outline btn-sm"
          aria-label="Refresh dashboard data"
        >
          <RefreshCw className={cn('icon-sm', loading && 'spin-animation')} aria-hidden="true" />
          <span className="btn-label-desktop">{loading ? 'Refreshing...' : 'Refresh'}</span>
        </button>

        <button
          type="button"
          onClick={onLogout}
          title="Sign out of PhoenixML"
          className="btn btn-secondary btn-sm"
          aria-label="Sign out of account"
        >
          <LogOut className="icon-sm" aria-hidden="true" />
          <span className="btn-label-desktop">Sign Out</span>
        </button>
      </div>
    </header>
  );
}
