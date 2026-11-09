import React from 'react';
import {
  LayoutDashboard,
  Cpu,
  History,
  Zap,
  Filter,
  RotateCcw,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader.jsx';
import { HITLBanner } from '../components/HITLBanner.jsx';
import { KPIGrid } from '../components/KPIGrid.jsx';
import { DecisionReviewBox } from '../components/DecisionReviewBox.jsx';
import { ModelCard } from '../components/ModelCard.jsx';
import { RecentDecisionsTable } from '../components/RecentDecisionsTable.jsx';
import { LoadingState } from '../components/LoadingState.jsx';
import { EmptyState } from '../components/EmptyState.jsx';
import { StatusBadge } from '../components/StatusBadge.jsx';

export function DashboardPage({
  user,
  dashboardData,
  selectedModelId,
  setSelectedModelId,
  loading,
  actionLoading,
  evalResults,
  modelMap,
  pendingDecision,
  handleEvaluate,
  handleRealEvaluate,
  handleApprove,
  handleReject,
}) {
  const modelCards = dashboardData?.model_cards || [];
  const recentDecisions = dashboardData?.decision_summary?.recent_decisions || [];

  if (loading && !dashboardData) {
    return <LoadingState message="Loading telemetry & decision metrics..." />;
  }

  return (
    <div className="dashboard-content">
      {/* Page Header */}
      <PageHeader
        icon={LayoutDashboard}
        title="Fleet Operations & Decision Support"
        subtitle="Deterministic MLOps governance, real performance telemetry, and human-in-the-loop approval workflows."
        badge={
          <StatusBadge variant="info" size="sm">
            Live Telemetry
          </StatusBadge>
        }
      />

      {/* HITL Advisory Banner */}
      <HITLBanner />

      {/* KPI Overview Grid */}
      <KPIGrid data={dashboardData} />

      {/* Model Filter Bar */}
      <div className="filter-bar">
        <div className="filter-group">
          <Filter className="icon-sm filter-icon" aria-hidden="true" />
          <span className="filter-label">
            Scope / Model Filter:
          </span>
          <select
            className="model-select"
            value={selectedModelId}
            onChange={(e) => setSelectedModelId(e.target.value)}
            aria-label="Filter by registered model"
          >
            <option value="">All Models (System Overview)</option>
            {modelCards.map((m) => (
              <option key={m.model_id} value={m.model_id}>
                {m.name} ({m.status})
              </option>
            ))}
          </select>
        </div>

        {selectedModelId && (
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => setSelectedModelId('')}
            aria-label="Reset model filter"
          >
            <RotateCcw className="icon-xs" aria-hidden="true" />
            <span>Reset Filter</span>
          </button>
        )}
      </div>

      {/* Mandatory Human Review Box (Highlighted pending or focused decision) */}
      {pendingDecision && (
        <section className="section">
          <div className="section-header">
            <h2 className="section-title">
              <Zap className="icon-sm text-warning" aria-hidden="true" />
              <span>
                {pendingDecision.approval_status === 'PENDING'
                  ? 'Pending Operator Action (Mandatory Review)'
                  : 'Selected Model Decision Review'}
              </span>
            </h2>
          </div>
          <DecisionReviewBox
            decision={pendingDecision}
            modelName={modelMap[pendingDecision.model_id]?.name}
            userRole={user?.role}
            onApprove={handleApprove}
            onReject={handleReject}
            actionLoading={actionLoading}
          />
        </section>
      )}

      {/* Model Inventory Section */}
      <section className="section">
        <div className="section-header">
          <h2 className="section-title">
            <Cpu className="icon-sm text-primary" aria-hidden="true" />
            <span>{selectedModelId ? 'Focused Model Card' : 'Registered Model Fleet'}</span>
          </h2>
          <span className="section-meta">
            {modelCards.length} model{modelCards.length === 1 ? '' : 's'} displayed
          </span>
        </div>

        {modelCards.length === 0 ? (
          <EmptyState
            icon={Cpu}
            title="No Models Found"
            description="No registered spam models found in the database. Use the Model Registry API to register your first model."
          />
        ) : (
          <div className="models-grid">
            {modelCards
              .filter((m) => !selectedModelId || m.model_id === selectedModelId)
              .map((m) => (
                <ModelCard
                  key={m.model_id}
                  model={m}
                  isSelected={selectedModelId === m.model_id}
                  onSelect={(id) => setSelectedModelId(selectedModelId === id ? '' : id)}
                  onEvaluate={handleEvaluate}
                  onRealEvaluate={handleRealEvaluate}
                  evalResult={evalResults[m.model_id]}
                  actionLoading={actionLoading}
                  userRole={user?.role}
                />
              ))}
          </div>
        )}
      </section>

      {/* Recent Decisions Audit Trail Section */}
      <section className="section">
        <div className="section-header">
          <h2 className="section-title">
            <History className="icon-sm text-indigo" aria-hidden="true" />
            <span>Recent Decision Audit Trail</span>
          </h2>
          <span className="section-meta">
            Total Recorded: {dashboardData?.decision_summary?.total_decisions || 0}
          </span>
        </div>

        <div className="table-card">
          <RecentDecisionsTable
            decisions={recentDecisions}
            modelMap={modelMap}
          />
        </div>
      </section>
    </div>
  );
}
