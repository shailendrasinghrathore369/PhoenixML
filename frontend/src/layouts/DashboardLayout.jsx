import React, { useState, useEffect } from 'react';
import { AppSidebar } from '../components/AppSidebar.jsx';
import { AppHeader } from '../components/AppHeader.jsx';
import { ToastContainer } from '../components/Toast.jsx';

export function DashboardLayout({
  user,
  onLogout,
  onRefresh,
  loading,
  pendingCount = 0,
  systemStatus = 'HEALTHY',
  totalModels = 0,
  toasts = [],
  onDismissToast,
  currentView = 'dashboard',
  onSelectView,
  children,
}) {
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);

  // Close mobile navigation drawer on Escape key press
  useEffect(() => {
    if (!isMobileNavOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setIsMobileNavOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMobileNavOpen]);

  return (
    <div className="app-shell">
      {/* Top Application Bar */}
      <AppHeader
        user={user}
        onLogout={onLogout}
        onRefresh={onRefresh}
        loading={loading}
        isMobileNavOpen={isMobileNavOpen}
        onToggleMobileNav={() => setIsMobileNavOpen((prev) => !prev)}
      />

      {/* Backdrop for mobile drawer */}
      {isMobileNavOpen && (
        <div
          className="sidebar-backdrop"
          onClick={() => setIsMobileNavOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Main Content Area with Sidebar */}
      <div className="app-body">
        <AppSidebar
          currentView={currentView}
          onSelectView={onSelectView}
          pendingCount={pendingCount}
          systemStatus={systemStatus}
          totalModels={totalModels}
          isMobileNavOpen={isMobileNavOpen}
          onCloseMobileNav={() => setIsMobileNavOpen(false)}
        />

        <main className="app-main" id="main-content" tabIndex="-1">
          <div className="app-container">
            {children}
          </div>
        </main>
      </div>

      {/* Global Toast System */}
      <ToastContainer toasts={toasts} onDismiss={onDismissToast} />
    </div>
  );
}
