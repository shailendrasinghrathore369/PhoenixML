import React from 'react';
import {
  History,
  ShieldCheck,
  CheckCircle,
  XCircle,
  Clock,
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
    </div>
  );
}
