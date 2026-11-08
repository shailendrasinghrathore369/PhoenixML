import React from 'react';
import { ThemeProvider } from './hooks/useTheme.js';
import { useToast } from './hooks/useToast.js';
import { useAuth } from './hooks/useAuth.js';
import { useDashboard } from './hooks/useDashboard.js';
import { DashboardLayout } from './layouts/DashboardLayout.jsx';
import { LoginPage } from './pages/LoginPage.jsx';
import { SignupPage } from './pages/SignupPage.jsx';
import { DashboardPage } from './pages/DashboardPage.jsx';
import { ToastContainer } from './components/Toast.jsx';

function AppContent() {
  const toast = useToast();
  const auth = useAuth(toast);
  const dashboard = useDashboard(auth.user, toast);

  // If user is unauthenticated, show Login or Signup
  if (!auth.user) {
    return (
      <>
        {auth.authMode === 'signup' ? (
          <SignupPage
            onSignup={auth.register}
            onSwitchToLogin={auth.switchToLogin}
            loading={auth.loading}
          />
        ) : (
          <LoginPage
            onLogin={auth.login}
            onSwitchToSignup={auth.switchToSignup}
            sessionExpired={auth.sessionExpired}
            initialMessage={auth.authMessage?.text}
            initialMessageType={auth.authMessage?.type || 'info'}
            prefillUsername={auth.prefillUsername}
            loading={auth.loading}
          />
        )}
        <ToastContainer toasts={toast.toasts} onDismiss={toast.dismissToast} />
      </>
    );
  }

  const pendingCount = dashboard.dashboardData?.decision_summary?.pending_approvals_count || 0;
  const systemStatus = dashboard.dashboardData?.health_summary?.system_health_status || 'NO_DATA';
  const totalModels = dashboard.dashboardData?.models_summary?.total_models || 0;

  return (
    <DashboardLayout
      user={auth.user}
      onLogout={auth.logout}
      onRefresh={() => dashboard.loadDashboard(dashboard.selectedModelId)}
      loading={dashboard.loading}
      pendingCount={pendingCount}
      systemStatus={systemStatus}
      totalModels={totalModels}
      toasts={toast.toasts}
      onDismissToast={toast.dismissToast}
    >
      <DashboardPage
        user={auth.user}
        dashboardData={dashboard.dashboardData}
        selectedModelId={dashboard.selectedModelId}
        setSelectedModelId={dashboard.setSelectedModelId}
        loading={dashboard.loading}
        actionLoading={dashboard.actionLoading}
        evalResults={dashboard.evalResults}
        modelMap={dashboard.modelMap}
        pendingDecision={dashboard.pendingDecision}
        handleEvaluate={dashboard.handleEvaluate}
        handleRealEvaluate={dashboard.handleRealEvaluate}
        handleApprove={dashboard.handleApprove}
        handleReject={dashboard.handleReject}
      />
    </DashboardLayout>
  );
}

export function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;
