import React, { useState } from 'react';
import {
  LayoutDashboard,
  Cpu,
  CheckSquare,
  History,
  Activity,
  ChevronLeft,
  ChevronRight,
  X,
} from 'lucide-react';
import { cn } from '../lib/utils.js';

export function AppSidebar({
  currentView = 'dashboard',
  onSelectView,
  pendingCount = 0,
  systemStatus = 'HEALTHY',
  totalModels = 0,
  isMobileNavOpen = false,
  onCloseMobileNav,
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

  const showExpandedContent = !collapsed || isMobileNavOpen;

  return (
    <aside
      id="app-sidebar"
      className={cn('app-sidebar', collapsed && 'collapsed', isMobileNavOpen && 'mobile-open')}
      aria-label="Operations Navigation"
    >
      <div className="sidebar-header">
        {showExpandedContent && (
          <span className="sidebar-title">
            Operations Center
          </span>
        )}
        <button
          type="button"
          onClick={isMobileNavOpen ? onCloseMobileNav : () => setCollapsed(!collapsed)}
          className="sidebar-toggle-btn"
          title={isMobileNavOpen ? 'Close navigation' : (collapsed ? 'Expand sidebar' : 'Collapse sidebar')}
          aria-label={isMobileNavOpen ? 'Close navigation' : (collapsed ? 'Expand sidebar' : 'Collapse sidebar')}
        >
          {isMobileNavOpen ? (
            <X className="icon-sm" aria-hidden="true" />
          ) : collapsed ? (
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
              onClick={() => {
                onSelectView?.(item.id);
                onCloseMobileNav?.();
              }}
              className={cn('sidebar-nav-item', isActive && 'active')}
              title={!showExpandedContent ? item.label : undefined}
              aria-label={item.label}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon className="icon-sm nav-icon" aria-hidden="true" />
              {showExpandedContent && <span className="nav-label">{item.label}</span>}
              {showExpandedContent && item.badge && (
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
      {showExpandedContent && (
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
