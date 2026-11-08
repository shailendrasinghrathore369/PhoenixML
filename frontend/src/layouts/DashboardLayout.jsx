import React, { useState } from 'react';
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
  children,
}) {
  const [currentView, setCurrentView] = useState('dashboard');

  return (
    <div className="app-shell">
      {/* Top Application Bar */}
      <AppHeader
        user={user}
        onLogout={onLogout}
        onRefresh={onRefresh}
        loading={loading}
      />

      {/* Main Content Area with Sidebar */}
      <div className="app-body">
        <AppSidebar
          currentView={currentView}
          onSelectView={setCurrentView}
          pendingCount={pendingCount}
          systemStatus={systemStatus}
          totalModels={totalModels}
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
