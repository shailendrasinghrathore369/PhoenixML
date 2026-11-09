import React from 'react';
import {
  History,
  ShieldCheck,
  Filter,
  CheckCircle,
  XCircle,
  Clock,
  ArrowRight,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader.jsx';
import { MetricCard } from '../components/MetricCard.jsx';
import { StatusBadge } from '../components/StatusBadge.jsx';
import { RecentDecisionsTable } from '../components/RecentDecisionsTable.jsx';
import { LoadingState } from '../components/LoadingState.jsx';

export function AuditTrailPage({
  user,
  dashboardData,
  modelMap = {},
  loading = false,
  onNavigate,
}) {
  const decisionSummary = dashboardData?.decision_summary || {};
  const totalDecisions = decisionSummary.total_decisions || 0;
  const pendingCount = decisionSummary.pending_approvals_count || 0;
  const approvedCount = decisionSummary.approved_count || 0;
  const rejectedCount = decisionSummary.rejected_count || 0;
  const recentDecisions = decisionSummary.recent_decisions || [];

  if (loading && !dashboardData) {
    return <LoadingState message="Loading governance audit logs..." />;
  }

  return (
    <div className="dashboard-content">
      {/* Page Header */}
      <PageHeader
        icon={History}
        title="Decision Audit Trail & Governance Log"
        subtitle="Immutable chronological audit trail of all AIMD recommendations, operator decisions, and rationale records."
        badge={
          <StatusBadge variant="info" size="sm">
            Phase 3B · Milestone 4
          </StatusBadge>
        }
      />

      {/* Audit Stats KPIs */}
      <div className="kpi-grid">
        <MetricCard
          icon={History}
          title="Total Recorded Decisions"
          value={totalDecisions}
          subtext="Chronologically logged in database"
        />
        <MetricCard
          icon={Clock}
          title="Pending Authorization"
          value={pendingCount}
          highlight={pendingCount > 0}
          badge={
            <StatusBadge variant={pendingCount > 0 ? 'pending' : 'approved'} size="sm">
              {pendingCount > 0 ? 'Review Needed' : 'All Clear'}
            </StatusBadge>
          }
          subtext="Awaiting operator review"
        />
        <MetricCard
          icon={CheckCircle}
          title="Approved Records"
          value={approvedCount}
          subtext="Operator authorized actions"
          badge={
            <StatusBadge variant="approved" size="sm">
              Authorized
            </StatusBadge>
          }
        />
        <MetricCard
          icon={XCircle}
          title="Rejected Records"
          value={rejectedCount}
          subtext="Operator declined actions"
          badge={
            <StatusBadge variant="rejected" size="sm">
              Declined
            </StatusBadge>
          }
        />
      </div>

      {/* Real Audit Trail Table Section */}
      <section className="section">
        <div className="section-header">
          <h2 className="section-title">
            <ShieldCheck className="icon-sm text-primary" aria-hidden="true" />
            <span>Recorded Decision Governance Log</span>
          </h2>
          <span className="section-meta">
            Displaying {recentDecisions.length} of {totalDecisions} recorded decisions
          </span>
        </div>

        <div className="table-card">
          <RecentDecisionsTable
            decisions={recentDecisions}
            modelMap={modelMap}
          />
        </div>
      </section>

      {/* Milestone 4 Roadmap & Audit Filters Preview */}
      <section className="section">
        <div className="section-header">
          <h2 className="section-title">
            <Filter className="icon-sm text-primary" aria-hidden="true" />
            <span>Audit Trail Enhancements (Milestone 4)</span>
          </h2>
          <span className="section-meta">Advanced Querying & Deep Signals</span>
        </div>

        <div className="roadmap-grid">
          <div className="roadmap-card">
            <div className="roadmap-card-header">
              <Filter className="icon-sm text-primary" aria-hidden="true" />
              <h3 className="roadmap-card-title">Status & Priority Filtering</h3>
            </div>
            <p className="roadmap-card-desc">
              Filter audit records by approval status (Pending, Approved, Rejected) and recommendation priority (Critical, High, Medium, Low).
            </p>
            <span className="roadmap-badge">Query Filters</span>
          </div>

          <div className="roadmap-card">
            <div className="roadmap-card-header">
              <History className="icon-sm text-primary" aria-hidden="true" />
              <h3 className="roadmap-card-title">Full Multi-Page History</h3>
            </div>
            <p className="roadmap-card-desc">
              Paginated traversal across hundreds of historical decision records using backend pagination controls (`skip`, `limit`, and `total`).
            </p>
            <span className="roadmap-badge">GET /api/spam-models/{'{id}'}/decisions</span>
          </div>

          <div className="roadmap-card">
            <div className="roadmap-card-header">
              <ShieldCheck className="icon-sm text-primary" aria-hidden="true" />
              <h3 className="roadmap-card-title">Deep Explainability Inspector</h3>
            </div>
            <p className="roadmap-card-desc">
              Unpack structured `supporting_signals` into categorized evidence cards (health drops, performance trends, concept drift, data drift).
            </p>
            <span className="roadmap-badge">Signal Inspector</span>
          </div>
        </div>
      </section>
    </div>
  );
}
