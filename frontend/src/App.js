/**
 * PhoenixML Operator-Facing Dashboard Single Page Application
 * Built with React 18 for operator decision support and human approval workflows.
 */

import { api, authStorage } from './api.js';

const { useState, useEffect, useCallback, useMemo } = React;
const h = React.createElement;

// Helper to format date strings cleanly
function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  try {
    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? 'N/A' : d.toLocaleString();
  } catch {
    return 'N/A';
  }
}

// Helper to format float values
function formatMetric(val, decimals = 4) {
  if (val === null || val === undefined || isNaN(val)) return 'N/A';
  return Number(val).toFixed(decimals);
}

// Health status CSS class helper
function getHealthClass(status) {
  if (!status) return 'insufficient';
  const s = status.toUpperCase();
  if (s === 'HEALTHY') return 'healthy';
  if (s === 'WARNING') return 'warning';
  if (s === 'CRITICAL') return 'critical';
  return 'insufficient';
}

// Approval status CSS class helper
function getApprovalClass(status) {
  if (!status) return 'pending';
  const s = status.toUpperCase();
  if (s === 'APPROVED') return 'approved';
  if (s === 'REJECTED') return 'rejected';
  return 'pending';
}

// Priority badge CSS class helper
function getPriorityClass(priority) {
  if (!priority) return 'neutral';
  const p = priority.toUpperCase();
  if (p === 'CRITICAL') return 'critical';
  if (p === 'HIGH') return 'warning';
  if (p === 'MEDIUM') return 'info';
  return 'neutral';
}

/**
 * Login Screen Component
 */
function LoginScreen({ onLoginSuccess }) {
  const [username, setUsername] = useState('admin@phoenixml.io');
  const [password, setPassword] = useState('AdminSecurePass123!');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.login(username, password);
      onLoginSuccess(res.user);
    } catch (err) {
      setError(err.message || 'Login failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  return h('div', { className: 'login-container' },
    h('div', { className: 'login-card' },
      h('div', { className: 'login-header' },
        h('div', { style: { display: 'flex', justifyContent: 'center', marginBottom: '1rem' } },
          h('div', { className: 'brand-icon', style: { width: '48px', height: '48px', fontSize: '1.5rem' } }, 'P')
        ),
        h('h1', { className: 'brand-title', style: { fontSize: '1.5rem', marginBottom: '0.25rem' } }, 'PhoenixML'),
        h('p', { className: 'brand-subtitle' }, 'MLOps Decision-Support Platform')
      ),
      error && h('div', { className: 'alert alert-error', style: { marginBottom: '1.5rem' } }, error),
      h('form', { onSubmit: handleSubmit },
        h('div', { className: 'form-group' },
          h('label', { className: 'form-label' }, 'Username / Email'),
          h('input', {
            type: 'text',
            className: 'form-input',
            value: username,
            onChange: (e) => setUsername(e.target.value),
            required: true,
            placeholder: 'admin@phoenixml.io',
          })
        ),
        h('div', { className: 'form-group' },
          h('label', { className: 'form-label' }, 'Password'),
          h('input', {
            type: 'password',
            className: 'form-input',
            value: password,
            onChange: (e) => setPassword(e.target.value),
            required: true,
            placeholder: '••••••••',
          })
        ),
        h('button', {
          type: 'submit',
          className: 'btn btn-primary',
          style: { width: '100%', justifyContent: 'center', padding: '0.75rem', marginTop: '0.5rem' },
          disabled: loading,
        }, loading ? 'Authenticating...' : 'Sign In to Dashboard')
      ),
      h('div', { className: 'login-footer-hint' },
        h('p', { style: { fontWeight: '600', marginBottom: '0.25rem' } }, 'Pre-configured Test Roles:'),
        h('p', null, 'Admin: admin@phoenixml.io'),
        h('p', null, 'ML Engineer: engineer@phoenixml.io'),
        h('p', null, 'Viewer: viewer@phoenixml.io')
      )
    )
  );
}

/**
 * Top Navigation Bar
 */
function Navbar({ user, onLogout, onRefresh, loading }) {
  const roleClass = user?.role ? user.role.toLowerCase() : 'viewer';

  return h('header', { className: 'navbar' },
    h('div', { className: 'brand' },
      h('div', { className: 'brand-icon' }, 'P'),
      h('div', null,
        h('div', { className: 'brand-title' }, 'PhoenixML'),
        h('div', { className: 'brand-subtitle' }, 'MLOps Decision Support')
      )
    ),
    h('div', { className: 'user-controls' },
      h('span', { className: `role-badge ${roleClass}` }, user?.role || 'VIEWER'),
      h('span', { style: { fontSize: '0.875rem', color: '#cbd5e1', fontWeight: 500 } }, user?.email || user?.username),
      h('button', {
        className: 'btn btn-outline',
        onClick: onRefresh,
        disabled: loading,
        title: 'Refresh Dashboard Data',
      }, loading ? '⟳ Refreshing...' : '⟳ Refresh'),
      h('button', {
        className: 'btn btn-secondary',
        onClick: onLogout,
        title: 'Sign out of dashboard',
      }, 'Sign Out')
    )
  );
}

/**
 * Guardrails / HITL Banner
 */
function HITLBanner() {
  return h('div', { className: 'hitl-banner' },
    h('div', { className: 'hitl-banner-text' },
      h('span', { className: 'hitl-pill' }, 'Human-In-The-Loop Advisory'),
      h('span', null,
        'PhoenixML AIMD generates deterministic maintenance recommendations only. Autonomous retraining, rollback, deployment, or maintenance execution is strictly prohibited. Human operator review and authorization is mandatory.'
      )
    )
  );
}

/**
 * Overview KPI Cards Grid
 */
function KPIGrid({ data }) {
  const models = data?.models_summary || {};
  const monitoring = data?.monitoring_summary || {};
  const health = data?.health_summary || {};
  const decisions = data?.decision_summary || {};

  const healthClass = getHealthClass(health.system_health_status);
  const pendingCount = decisions.pending_approvals_count || 0;

  return h('div', { className: 'kpi-grid' },
    // KPI 1: Models
    h('div', { className: 'kpi-card' },
      h('div', { className: 'kpi-header' },
        h('span', { className: 'kpi-title' }, 'Registered Models'),
        h('span', { className: 'status-badge' }, `${models.active_models || 0} Active`)
      ),
      h('div', { className: 'kpi-value' }, models.total_models || 0),
      h('div', { className: 'kpi-sub' },
        `Active: ${models.active_models || 0} · Dev: ${models.development_models || 0} · Archived: ${models.archived_models || 0}`
      )
    ),

    // KPI 2: Monitoring Observations
    h('div', { className: 'kpi-card' },
      h('div', { className: 'kpi-header' },
        h('span', { className: 'kpi-title' }, 'Telemetry & Observations'),
        monitoring.latest_f1 !== null && monitoring.latest_f1 !== undefined
          ? h('span', { className: 'status-badge healthy' }, `F1: ${formatMetric(monitoring.latest_f1, 2)}`)
          : null
      ),
      h('div', { className: 'kpi-value' }, monitoring.total_observations || 0),
      h('div', { className: 'kpi-sub' },
        monitoring.latest_observation_at
          ? `Latest: ${formatDate(monitoring.latest_observation_at)}`
          : 'No observations recorded'
      )
    ),

    // KPI 3: System Health
    h('div', { className: 'kpi-card' },
      h('div', { className: 'kpi-header' },
        h('span', { className: 'kpi-title' }, 'Fleet Health Status'),
        h('span', { className: `status-badge ${healthClass}` }, health.system_health_status || 'NO_DATA')
      ),
      h('div', { className: 'kpi-value' },
        health.average_health_score !== null && health.average_health_score !== undefined
          ? `${formatMetric(health.average_health_score, 1)}%`
          : 'N/A'
      ),
      h('div', { className: 'kpi-sub' },
        `Healthy: ${health.healthy_count || 0} · Warning: ${health.warning_count || 0} · Critical: ${health.critical_count || 0}`
      )
    ),

    // KPI 4: Pending Human Approvals
    h('div', { className: `kpi-card ${pendingCount > 0 ? 'highlight-pending' : ''}` },
      h('div', { className: 'kpi-header' },
        h('span', { className: 'kpi-title' }, 'Pending Human Approvals'),
        h('span', { className: `status-badge ${pendingCount > 0 ? 'pending' : 'approved'}` },
          pendingCount > 0 ? 'Action Required' : 'All Clear'
        )
      ),
      h('div', { className: 'kpi-value', style: { color: pendingCount > 0 ? '#fbbf24' : '#f8fafc' } }, pendingCount),
      h('div', { className: 'kpi-sub' },
        `Total Decisions: ${decisions.total_decisions || 0} · Approved: ${decisions.approved_count || 0} · Rejected: ${decisions.rejected_count || 0}`
      )
    )
  );
}

/**
 * Health Score Progress Meter
 */
function HealthMeter({ score, status }) {
  const numScore = score !== null && score !== undefined ? Math.max(0, Math.min(100, score)) : 0;
  const barClass = getHealthClass(status);

  return h('div', { className: 'health-meter' },
    h('div', { className: 'health-meter-labels' },
      h('span', { style: { color: '#94a3b8' } }, 'Health Score'),
      h('span', { style: { color: '#f8fafc' } }, score !== null && score !== undefined ? `${formatMetric(score, 1)} / 100` : 'N/A')
    ),
    h('div', { className: 'meter-track' },
      h('div', {
        className: `meter-bar ${barClass}`,
        style: { width: `${numScore}%` },
      })
    )
  );
}

/**
 * Interactive Decision Review Box (Approve / Reject Action Card)
 */
function DecisionReviewBox({ decision, modelName, userRole, onApprove, onReject, actionLoading }) {
  if (!decision) return null;

  const isPending = decision.approval_status === 'PENDING';
  const isViewer = userRole === 'VIEWER';
  const isLoading = actionLoading === `approval-${decision.id}`;

  return h('div', { className: `decision-box ${isPending ? 'highlight' : ''}` },
    h('div', { className: 'decision-header' },
      h('div', null,
        h('div', { style: { display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem', flexWrap: 'wrap' } },
          h('span', { className: 'decision-action-title' }, decision.recommended_action),
          h('span', { className: `status-badge ${getPriorityClass(decision.priority)}` }, `Priority: ${decision.priority}`),
          h('span', { className: `status-badge ${getApprovalClass(decision.approval_status)}` }, decision.approval_status)
        ),
        h('div', { style: { fontSize: '0.8rem', color: '#94a3b8' } },
          `Model: ${modelName || decision.model_id} · Decision ID: ${decision.id} · Evaluated: ${formatDate(decision.created_at)}`
        )
      )
    ),

    h('div', { className: 'decision-rationale' },
      h('strong', null, 'Rationale: '),
      decision.rationale || 'No rationale recorded.'
    ),

    decision.explanation && h('div', { className: 'decision-rationale', style: { color: '#94a3b8', fontStyle: 'italic' } },
      h('strong', null, 'Explanation: '),
      decision.explanation
    ),

    h('div', { className: 'decision-details-grid' },
      h('div', null,
        h('div', { className: 'decision-detail-label' }, 'Health Score at Decision'),
        h('div', { className: 'decision-detail-val' },
          decision.health_score !== null && decision.health_score !== undefined
            ? `${formatMetric(decision.health_score, 1)} (${decision.health_status})`
            : 'N/A'
        )
      ),
      h('div', null,
        h('div', { className: 'decision-detail-label' }, 'Confidence Score'),
        h('div', { className: 'decision-detail-val' },
          decision.confidence !== null && decision.confidence !== undefined
            ? `${(decision.confidence * 100).toFixed(1)}%`
            : 'N/A'
        )
      ),
      h('div', null,
        h('div', { className: 'decision-detail-label' }, 'Requires Human Approval'),
        h('div', { className: 'decision-detail-val', style: { color: decision.requires_human_approval ? '#fbbf24' : '#10b981' } },
          decision.requires_human_approval ? 'YES (Mandatory)' : 'NO'
        )
      ),
      h('div', null,
        h('div', { className: 'decision-detail-label' }, 'Approval Status'),
        h('div', { className: 'decision-detail-val' },
          h('span', { className: `status-badge ${getApprovalClass(decision.approval_status)}` }, decision.approval_status)
        )
      )
    ),

    // Action Controls
    isPending && h('div', { className: 'approval-actions' },
      isViewer && h('span', { style: { fontSize: '0.8rem', color: '#94a3b8', marginRight: 'auto' } },
        '🔒 Viewers have read-only access. ML_ENGINEER or ADMIN required to approve/reject.'
      ),
      h('button', {
        className: 'btn btn-danger',
        onClick: () => onReject(decision),
        disabled: isViewer || isLoading,
        title: isViewer ? 'Viewers cannot reject recommendations' : 'Reject this recommendation',
      }, isLoading ? 'Processing...' : '✕ Reject Recommendation'),
      h('button', {
        className: 'btn btn-success',
        onClick: () => onApprove(decision),
        disabled: isViewer || isLoading,
        title: isViewer ? 'Viewers cannot approve recommendations' : 'Approve this recommendation',
      }, isLoading ? 'Processing...' : '✓ Approve Recommendation')
    )
  );
}

/**
 * Model Card Component
 */
function ModelCard({ model, isSelected, onSelect, onEvaluate, actionLoading, userRole }) {
  const isEvaluating = actionLoading === `evaluating-${model.model_id}`;
  const isViewer = userRole === 'VIEWER';
  const hasDecision = !!model.latest_decision;
  const decision = model.latest_decision;

  return h('div', { className: `model-card ${isSelected ? 'selected' : ''}` },
    h('div', { className: 'model-card-top' },
      h('div', null,
        h('h3', { className: 'model-name' }, model.name),
        h('div', { className: 'model-meta' }, `${model.framework} · ID: ${String(model.model_id).substring(0, 8)}...`)
      ),
      h('span', { className: `status-badge ${model.status === 'ACTIVE' ? 'healthy' : 'insufficient'}` }, model.status)
    ),

    // Health Meter
    h(HealthMeter, {
      score: model.latest_health_score,
      status: model.latest_health_status,
    }),

    // Inline Metrics
    h('div', { className: 'metrics-row' },
      h('div', { className: 'metric-item' },
        h('span', { className: 'metric-item-name' }, 'Observations'),
        h('span', { className: 'metric-item-val' }, model.observation_count || 0)
      ),
      h('div', { className: 'metric-item' },
        h('span', { className: 'metric-item-name' }, 'Latest F1'),
        h('span', { className: 'metric-item-val' }, formatMetric(model.latest_f1_score, 3))
      ),
      h('div', { className: 'metric-item' },
        h('span', { className: 'metric-item-name' }, 'Health Status'),
        h('span', { className: `status-badge ${getHealthClass(model.latest_health_status)}`, style: { marginTop: '2px' } },
          model.latest_health_status || 'NO_DATA'
        )
      )
    ),

    // Latest Decision snippet
    hasDecision ? h('div', { style: { fontSize: '0.8rem', background: '#0f172a', padding: '0.6rem 0.75rem', borderRadius: '6px' } },
      h('div', { style: { display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' } },
        h('span', { style: { color: '#94a3b8' } }, 'Latest Recommendation:'),
        h('span', { className: `status-badge ${getApprovalClass(decision.approval_status)}`, style: { fontSize: '0.65rem', padding: '0.1rem 0.4rem' } }, decision.approval_status)
      ),
      h('div', { style: { fontWeight: 600, color: '#f8fafc' } }, decision.recommended_action),
      h('div', { style: { color: '#64748b', fontSize: '0.75rem', marginTop: '0.2rem' } }, `Priority: ${decision.priority} · ${formatDate(decision.created_at)}`)
    ) : h('div', { style: { fontSize: '0.8rem', color: '#64748b', fontStyle: 'italic', padding: '0.5rem 0' } },
      'No evaluation decisions recorded yet.'
    ),

    // Card Actions
    h('div', { style: { display: 'flex', gap: '0.5rem', marginTop: 'auto', paddingTop: '0.5rem' } },
      h('button', {
        className: `btn ${isSelected ? 'btn-primary' : 'btn-secondary'}`,
        style: { flex: 1, justifyContent: 'center' },
        onClick: () => onSelect(model.model_id),
      }, isSelected ? 'Focused' : 'Inspect Model'),
      h('button', {
        className: 'btn btn-outline',
        onClick: () => onEvaluate(model.model_id),
        disabled: isViewer || isEvaluating,
        title: isViewer ? 'Viewers cannot trigger evaluations' : 'Trigger AIMD Evaluation',
      }, isEvaluating ? 'Evaluating...' : '⚡ Trigger AIMD')
    )
  );
}

/**
 * Recent Decisions Audit Table
 */
function RecentDecisionsTable({ decisions, modelMap }) {
  if (!decisions || decisions.length === 0) {
    return h('div', { className: 'state-container', style: { padding: '2.5rem' } },
      h('div', { className: 'empty-icon' }, '📋'),
      h('h4', { className: 'empty-title' }, 'No Decisions Recorded'),
      h('p', { className: 'empty-desc' }, 'Trigger an AIMD evaluation on any model with monitoring observations to generate maintenance recommendations.')
    );
  }

  return h('div', { className: 'table-responsive' },
    h('table', null,
      h('thead', null,
        h('tr', null,
          h('th', null, 'Date & Time'),
          h('th', null, 'Model'),
          h('th', null, 'Recommended Action'),
          h('th', null, 'Priority'),
          h('th', null, 'Health Score'),
          h('th', null, 'Confidence'),
          h('th', null, 'Approval Status')
        )
      ),
      h('tbody', null,
        decisions.map((dec) => {
          const modelName = modelMap[dec.model_id]?.name || `${String(dec.model_id).substring(0, 8)}...`;
          return h('tr', { key: dec.id },
            h('td', { style: { whiteSpace: 'nowrap', fontSize: '0.8rem' } }, formatDate(dec.created_at)),
            h('td', { style: { fontWeight: 600 } }, modelName),
            h('td', null,
              h('span', { style: { fontWeight: 600, color: '#f8fafc' } }, dec.recommended_action)
            ),
            h('td', null,
              h('span', { className: `status-badge ${getPriorityClass(dec.priority)}` }, dec.priority)
            ),
            h('td', null,
              dec.health_score !== null && dec.health_score !== undefined ? `${formatMetric(dec.health_score, 1)}` : 'N/A'
            ),
            h('td', null,
              dec.confidence !== null && dec.confidence !== undefined ? `${(dec.confidence * 100).toFixed(1)}%` : 'N/A'
            ),
            h('td', null,
              h('span', { className: `status-badge ${getApprovalClass(dec.approval_status)}` }, dec.approval_status)
            )
          );
        })
      )
    )
  );
}

/**
 * Main Application Component
 */
export function App() {
  const [user, setUser] = useState(() => authStorage.getUser());
  const [dashboardData, setDashboardData] = useState(null);
  const [selectedModelId, setSelectedModelId] = useState('');
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const [alert, setAlert] = useState(null);

  // Auto-dismiss alert after 6 seconds
  useEffect(() => {
    if (alert) {
      const timer = setTimeout(() => setAlert(null), 6000);
      return () => clearTimeout(timer);
    }
  }, [alert]);

  // Handle unauthenticated event
  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null);
      setDashboardData(null);
      setAlert({ type: 'error', message: 'Session expired. Please log in again.' });
    };
    window.addEventListener('phoenixml-unauthorized', handleUnauthorized);
    return () => window.removeEventListener('phoenixml-unauthorized', handleUnauthorized);
  }, []);

  // Fetch dashboard overview
  const loadDashboard = useCallback(async (modelId = selectedModelId) => {
    setLoading(true);
    try {
      const data = await api.getDashboardOverview(modelId || null);
      setDashboardData(data);
    } catch (err) {
      setAlert({ type: 'error', message: `Failed to load dashboard: ${err.message}` });
    } finally {
      setLoading(false);
    }
  }, [selectedModelId]);

  // Initial load when user is present
  useEffect(() => {
    if (user) {
      loadDashboard(selectedModelId);
    }
  }, [user, selectedModelId, loadDashboard]);

  // Handle login
  const handleLoginSuccess = (authenticatedUser) => {
    setUser(authenticatedUser);
    setAlert({ type: 'success', message: `Welcome back, ${authenticatedUser.email}!` });
  };

  // Handle logout
  const handleLogout = () => {
    api.logout();
    setUser(null);
    setDashboardData(null);
    setSelectedModelId('');
    setAlert(null);
  };

  // Trigger AIMD model evaluation
  const handleEvaluate = async (modelId) => {
    if (user?.role === 'VIEWER') {
      setAlert({ type: 'error', message: 'Viewers cannot trigger model evaluations.' });
      return;
    }
    setActionLoading(`evaluating-${modelId}`);
    try {
      const res = await api.evaluateModel(modelId);
      setAlert({
        type: 'success',
        message: `Evaluation triggered successfully! AIMD Recommendation: ${res.recommended_action} (Priority: ${res.priority}).`,
      });
      await loadDashboard(selectedModelId);
    } catch (err) {
      setAlert({ type: 'error', message: `Evaluation failed: ${err.message}` });
    } finally {
      setActionLoading(null);
    }
  };

  // Approve a recommendation
  const handleApprove = async (decision) => {
    if (user?.role === 'VIEWER') {
      setAlert({ type: 'error', message: 'Viewers cannot approve recommendations.' });
      return;
    }
    setActionLoading(`approval-${decision.id}`);
    try {
      await api.updateApprovalStatus(decision.model_id, decision.id, 'APPROVED');
      setAlert({
        type: 'success',
        message: `Recommendation "${decision.recommended_action}" successfully APPROVED by operator.`,
      });
      await loadDashboard(selectedModelId);
    } catch (err) {
      setAlert({ type: 'error', message: `Approval failed: ${err.message}` });
    } finally {
      setActionLoading(null);
    }
  };

  // Reject a recommendation
  const handleReject = async (decision) => {
    if (user?.role === 'VIEWER') {
      setAlert({ type: 'error', message: 'Viewers cannot reject recommendations.' });
      return;
    }
    setActionLoading(`approval-${decision.id}`);
    try {
      await api.updateApprovalStatus(decision.model_id, decision.id, 'REJECTED');
      setAlert({
        type: 'success',
        message: `Recommendation "${decision.recommended_action}" successfully REJECTED by operator.`,
      });
      await loadDashboard(selectedModelId);
    } catch (err) {
      setAlert({ type: 'error', message: `Rejection failed: ${err.message}` });
    } finally {
      setActionLoading(null);
    }
  };

  // Map model ID to model card for quick lookups
  const modelMap = useMemo(() => {
    const map = {};
    if (dashboardData?.model_cards) {
      dashboardData.model_cards.forEach((c) => {
        map[c.model_id] = c;
      });
    }
    return map;
  }, [dashboardData]);

  // Find the most urgent pending decision to highlight in the review box
  const pendingDecision = useMemo(() => {
    if (!dashboardData) return null;
    // Check if selected model has a pending decision
    if (selectedModelId && modelMap[selectedModelId]?.latest_decision?.approval_status === 'PENDING') {
      return modelMap[selectedModelId].latest_decision;
    }
    // Otherwise, find the first pending decision in recent_decisions or model cards
    if (dashboardData.decision_summary?.recent_decisions) {
      const pending = dashboardData.decision_summary.recent_decisions.find(
        (d) => d.approval_status === 'PENDING'
      );
      if (pending) return pending;
    }
    // Fallback to selected model's latest decision even if approved/rejected
    if (selectedModelId && modelMap[selectedModelId]?.latest_decision) {
      return modelMap[selectedModelId].latest_decision;
    }
    return null;
  }, [dashboardData, selectedModelId, modelMap]);

  // If unauthenticated, display login screen
  if (!user) {
    return h(LoginScreen, { onLoginSuccess: handleLoginSuccess });
  }

  const modelCards = dashboardData?.model_cards || [];
  const recentDecisions = dashboardData?.decision_summary?.recent_decisions || [];

  return h('div', { className: 'dashboard-wrapper' },
    h(Navbar, {
      user,
      onLogout: handleLogout,
      onRefresh: () => loadDashboard(selectedModelId),
      loading,
    }),

    h('main', { className: 'container' },
      // Toast / Alert
      alert && h('div', { className: `alert ${alert.type === 'error' ? 'alert-error' : 'alert-success'}` },
        h('span', null, alert.message),
        h('button', {
          onClick: () => setAlert(null),
          style: { background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', fontWeight: 'bold' }
        }, '✕')
      ),

      // HITL Banner
      h(HITLBanner),

      // Loading state
      loading && !dashboardData ? (
        h('div', { className: 'state-container' },
          h('div', { className: 'spinner' }),
          h('p', { style: { color: '#94a3b8' } }, 'Loading telemetry & decision metrics...')
        )
      ) : (
        h('div', null,
          // Overview KPIs
          h(KPIGrid, { data: dashboardData }),

          // Filter bar
          h('div', { className: 'filter-bar' },
            h('span', { className: 'filter-label' }, 'Scope / Model Filter:'),
            h('select', {
              className: 'model-select',
              value: selectedModelId,
              onChange: (e) => setSelectedModelId(e.target.value),
            },
              h('option', { value: '' }, 'All Models (System Overview)'),
              modelCards.map((m) =>
                h('option', { key: m.model_id, value: m.model_id }, `${m.name} (${m.status})`)
              )
            ),
            selectedModelId && h('button', {
              className: 'btn btn-outline',
              style: { padding: '0.4rem 0.8rem', fontSize: '0.8rem' },
              onClick: () => setSelectedModelId(''),
            }, 'Reset Filter')
          ),

          // Pending Decision Review Box (if any pending decision or focused decision exists)
          pendingDecision && h('div', { className: 'section' },
            h('div', { className: 'section-header' },
              h('h2', { className: 'section-title' },
                h('span', null, '⚡'),
                pendingDecision.approval_status === 'PENDING'
                  ? 'Pending Operator Action (Mandatory Review)'
                  : 'Selected Model Decision Review'
              )
            ),
            h(DecisionReviewBox, {
              decision: pendingDecision,
              modelName: modelMap[pendingDecision.model_id]?.name,
              userRole: user?.role,
              onApprove: handleApprove,
              onReject: handleReject,
              actionLoading,
            })
          ),

          // Model Inventory Section
          h('section', { className: 'section' },
            h('div', { className: 'section-header' },
              h('h2', { className: 'section-title' },
                h('span', null, '📊'),
                selectedModelId ? 'Focused Model Card' : 'Registered Model Fleet'
              ),
              h('span', { style: { fontSize: '0.85rem', color: '#94a3b8' } },
                `${modelCards.length} model${modelCards.length === 1 ? '' : 's'} displayed`
              )
            ),
            modelCards.length === 0 ? (
              h('div', { className: 'state-container' },
                h('div', { className: 'empty-icon' }, '🔍'),
                h('h4', { className: 'empty-title' }, 'No Models Found'),
                h('p', { className: 'empty-desc' }, 'No registered spam models found in the database. Use the Model Registry API to register your first model.')
              )
            ) : (
              h('div', { className: 'models-grid' },
                modelCards
                  .filter((m) => !selectedModelId || m.model_id === selectedModelId)
                  .map((m) =>
                    h(ModelCard, {
                      key: m.model_id,
                      model: m,
                      isSelected: selectedModelId === m.model_id,
                      onSelect: (id) => setSelectedModelId(selectedModelId === id ? '' : id),
                      onEvaluate: handleEvaluate,
                      actionLoading,
                      userRole: user?.role,
                    })
                  )
              )
            )
          ),

          // Recent Decisions Table Section
          h('section', { className: 'section' },
            h('div', { className: 'section-header' },
              h('h2', { className: 'section-title' },
                h('span', null, '📜'),
                'Recent Decision Audit Trail'
              ),
              h('span', { style: { fontSize: '0.85rem', color: '#94a3b8' } },
                `Total Recorded: ${dashboardData?.decision_summary?.total_decisions || 0}`
              )
            ),
            h('div', { className: 'table-card' },
              h(RecentDecisionsTable, {
                decisions: recentDecisions,
                modelMap,
              })
            )
          )
        )
      )
    )
  );
}

// Mount App if root element exists
const rootEl = document.getElementById('root');
if (rootEl && window.ReactDOM) {
  const root = ReactDOM.createRoot(rootEl);
  root.render(h(App));
}
