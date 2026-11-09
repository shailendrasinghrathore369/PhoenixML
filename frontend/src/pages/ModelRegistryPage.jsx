import React from 'react';
import {
  Cpu,
  PlusCircle,
  FileCode,
  Archive,
  Trash2,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader.jsx';
import { MetricCard } from '../components/MetricCard.jsx';
import { StatusBadge } from '../components/StatusBadge.jsx';
import { EmptyState } from '../components/EmptyState.jsx';
import { LoadingState } from '../components/LoadingState.jsx';

export function ModelRegistryPage({
  user,
  dashboardData,
  loading = false,
  onNavigate,
}) {
  const modelsSummary = dashboardData?.models_summary || {};
  const totalModels = modelsSummary.total_models || 0;
  const activeModels = modelsSummary.active_models || 0;
  const devModels = modelsSummary.development_models || 0;
  const archivedModels = modelsSummary.archived_models || 0;

  if (loading && !dashboardData) {
    return <LoadingState message="Loading model registry inventory..." />;
  }

  return (
    <div className="dashboard-content">
      {/* Page Header */}
      <PageHeader
        icon={Cpu}
        title="Model Registry & Governance"
        subtitle="Centralized inventory for registering, versioning, inspecting, and archiving PhoenixML spam detection models."
        badge={
          <StatusBadge variant="info" size="sm">
            Phase 3B · Milestone 2
          </StatusBadge>
        }
      />

      {/* Model Inventory Summary Metrics */}
      <div className="kpi-grid">
        <MetricCard
          icon={Cpu}
          title="Total Registered Models"
          value={totalModels}
          subtext="Configured in database"
          badge={
            <StatusBadge variant="healthy" size="sm">
              {activeModels} Active
            </StatusBadge>
          }
        />
        <MetricCard
          icon={FileCode}
          title="In Development"
          value={devModels}
          subtext="Candidate models undergoing training"
        />
        <MetricCard
          icon={Archive}
          title="Archived Models"
          value={archivedModels}
          subtext="Retired from production serving"
        />
        <MetricCard
          icon={ShieldAlert}
          title="Access Policy"
          value={user?.role || 'VIEWER'}
          subtext={user?.role === 'ADMIN' ? 'Unrestricted Fleet Access' : user?.role === 'ML_ENGINEER' ? 'Owned Models Access' : 'Read-Only Access'}
          badge={
            <StatusBadge variant={user?.role === 'ADMIN' ? 'admin' : user?.role === 'ML_ENGINEER' ? 'ml-engineer' : 'viewer'} size="sm">
              {user?.role || 'VIEWER'}
            </StatusBadge>
          }
        />
      </div>

      {/* Milestone 2 Roadmap & Upcoming Capabilities */}
      <section className="section">
        <div className="section-header">
          <h2 className="section-title">
            <PlusCircle className="icon-sm text-primary" aria-hidden="true" />
            <span>Registry Governance Roadmap (Milestone 2)</span>
          </h2>
          <span className="section-meta">Full CRUD Architecture</span>
        </div>

        <div className="roadmap-grid">
          <div className="roadmap-card">
            <div className="roadmap-card-header">
              <PlusCircle className="icon-sm text-primary" aria-hidden="true" />
              <h3 className="roadmap-card-title">Interactive Model Registration</h3>
            </div>
            <p className="roadmap-card-desc">
              Modal dialog to register new spam classification pipelines, specify algorithm parameters, and link training artifacts directly to the PostgreSQL registry.
            </p>
            <span className="roadmap-badge">POST /api/spam-models</span>
          </div>

          <div className="roadmap-card">
            <div className="roadmap-card-header">
              <FileCode className="icon-sm text-primary" aria-hidden="true" />
              <h3 className="roadmap-card-title">Metadata & Version Tracking</h3>
            </div>
            <p className="roadmap-card-desc">
              Inspect model artifact versions, framework specifications (scikit-learn), dataset provenance, and historical update timestamps.
            </p>
            <span className="roadmap-badge">PUT /api/spam-models/{'{id}'}</span>
          </div>

          <div className="roadmap-card">
            <div className="roadmap-card-header">
              <Trash2 className="icon-sm text-primary" aria-hidden="true" />
              <h3 className="roadmap-card-title">Role-Gated Model Deletion</h3>
            </div>
            <p className="roadmap-card-desc">
              Safe deletion workflows with confirmation dialogs. Restricts model removal to ML Engineers and Admins, with automatic cascading telemetry cleanup.
            </p>
            <span className="roadmap-badge">DELETE /api/spam-models/{'{id}'}</span>
          </div>
        </div>
      </section>

      {/* Placeholder Console State */}
      <section className="section">
        <EmptyState
          icon={Cpu}
          title="Model Registry Console Coming in Milestone 2"
          description="Interactive model registration forms, editing dialogs, and tabular fleet controls will be implemented in Phase 3B Milestone 2. Active registered models currently operate in production and can be evaluated from the Fleet Overview."
          action={
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => onNavigate?.('dashboard')}
            >
              <span>View Active Models in Fleet Overview</span>
              <ArrowRight className="icon-xs" aria-hidden="true" />
            </button>
          }
        />
      </section>
    </div>
  );
}
