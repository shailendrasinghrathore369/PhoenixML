import React, { useState } from 'react';
import {
  LayoutDashboard,
  Cpu,
  CheckSquare,
  History,
  Activity,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { cn } from '../lib/utils.js';

export function AppSidebar({
  currentView = 'dashboard',
  onSelectView,
  pendingCount = 0,
  systemStatus = 'HEALTHY',
  totalModels = 0,
}) {
  const [collapsed, setCollapsed] = useState(false);

  const navItems = [
    {
      id: 'dashboard',
      label: 'Fleet Overview',
      icon: LayoutDashboard,
    },
    {
      id: 'models',
      label: 'Model Registry',
      icon: Cpu,
      badge: totalModels > 0 ? totalModels : null,
    },
    {
      id: 'approvals',
      label: 'Human Approvals',
      icon: CheckSquare,
      badge: pendingCount > 0 ? pendingCount : null,
      badgeVariant: 'warning',
    },
    {
      id: 'telemetry',
      label: 'Model Telemetry',
      icon: Activity,
    },
    {
      id: 'audit',
      label: 'Audit Trail',
      icon: History,
    },
  ];

  return (
    <aside
      className={cn('app-sidebar', collapsed && 'collapsed')}
      aria-label="Operations Navigation"
    >
      <div className="sidebar-header">
        {!collapsed && (
          <span className="sidebar-title">
            Operations Center
          </span>
        )}
        <button
          type="button"
          onClick={() => setCollapsed(!collapsed)}
          className="sidebar-toggle-btn"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <ChevronRight className="icon-sm" aria-hidden="true" />
          ) : (
            <ChevronLeft className="icon-sm" aria-hidden="true" />
          )}
        </button>
      </div>

      <nav className="sidebar-nav" aria-label="Sidebar Sections">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelectView?.(item.id)}
              className={cn('sidebar-nav-item', isActive && 'active')}
              title={collapsed ? item.label : undefined}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon className="icon-sm nav-icon" aria-hidden="true" />
              {!collapsed && <span className="nav-label">{item.label}</span>}
              {!collapsed && item.badge && (
                <span
                  className={cn(
                    'nav-badge',
                    item.badgeVariant === 'warning'
                      ? 'nav-badge-warning'
                      : 'nav-badge-neutral'
                  )}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* System Status Footer */}
      {!collapsed && (
        <div className="sidebar-footer">
          <div className="sidebar-footer-row">
            <span className="sidebar-footer-title">AIMD Engine</span>
            <span className="status-badge-inline">
              <span className="status-pulse-dot" aria-hidden="true" />
              <span>ONLINE</span>
            </span>
          </div>
          <p className="sidebar-footer-desc">
            Human approval enforced on all automated actions.
          </p>
        </div>
      )}
    </aside>
  );
}
