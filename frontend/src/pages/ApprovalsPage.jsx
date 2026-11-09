import React from 'react';
import {
  CheckSquare,
  ShieldCheck,
  Zap,
  ArrowRight,
  Clock,
  XCircle,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader.jsx';
import { HITLBanner } from '../components/HITLBanner.jsx';
import { MetricCard } from '../components/MetricCard.jsx';
import { StatusBadge } from '../components/StatusBadge.jsx';
import { DecisionReviewBox } from '../components/DecisionReviewBox.jsx';
import { EmptyState } from '../components/EmptyState.jsx';
import { LoadingState } from '../components/LoadingState.jsx';

export function ApprovalsPage({
  user,
  dashboardData,
  pendingDecision,
  modelMap = {},
  handleApprove,
  handleReject,
  actionLoading,
  loading = false,
  onNavigate,
}) {
  const decisionSummary = dashboardData?.decision_summary || {};
  const pendingCount = decisionSummary.pending_approvals_count || 0;
  const totalDecisions = decisionSummary.total_decisions || 0;
  const approvedCount = decisionSummary.approved_count || 0;
  const rejectedCount = decisionSummary.rejected_count || 0;

  if (loading && !dashboardData) {
    return <LoadingState message="Loading approval queue..." />;
  }

  return (
    <div className="dashboard-content">
      {/* Page Header */}
      <PageHeader
        icon={CheckSquare}
        title="Human-in-the-Loop Approval Queue"
        subtitle="Mandatory human authorization queue for all AIMD automated maintenance recommendations."
        badge={
          <StatusBadge variant={pendingCount > 0 ? 'pending' : 'healthy'} size="sm">
            {pendingCount > 0 ? `${pendingCount} Action Required` : 'All Clear'}
          </StatusBadge>
        }
      />

      {/* Advisory Banner */}
      <HITLBanner />

      {/* Approval Queue Metrics */}
      <div className="kpi-grid">
        <MetricCard
          icon={Clock}
          title="Pending Approvals"
          value={pendingCount}
          highlight={pendingCount > 0}
          badge={
            <StatusBadge variant={pendingCount > 0 ? 'pending' : 'approved'} size="sm">
              {pendingCount > 0 ? 'Action Required' : 'Queue Empty'}
            </StatusBadge>
          }
          subtext="Requiring operator decision"
        />
        <MetricCard
          icon={ShieldCheck}
          title="Approved Actions"
          value={approvedCount}
          subtext="Authorized by operators"
          badge={
            <StatusBadge variant="approved" size="sm">
              Authorized
            </StatusBadge>
          }
        />
        <MetricCard
          icon={XCircle}
          title="Rejected Actions"
          value={rejectedCount}
          subtext="Declined with rationale"
          badge={
            <StatusBadge variant="rejected" size="sm">
              Declined
            </StatusBadge>
          }
        />
        <MetricCard
          icon={Zap}
          title="Total AIMD Recommendations"
          value={totalDecisions}
          subtext="Generated across model lifetime"
        />
      </div>

      {/* Active Decision Review Section */}
      <section className="section">
        <div className="section-header">
          <h2 className="section-title">
            <Zap className="icon-sm text-warning" aria-hidden="true" />
            <span>
              {pendingDecision
                ? 'Action Required: Operator Decision Review'
                : 'Approval Queue Status'}
            </span>
          </h2>
          <span className="section-meta">
            {pendingDecision ? 'Mandatory Review Required' : '0 Pending Items'}
          </span>
        </div>

        {pendingDecision ? (
          <DecisionReviewBox
            decision={pendingDecision}
            modelName={modelMap[pendingDecision.model_id]?.name}
            userRole={user?.role}
            onApprove={handleApprove}
            onReject={handleReject}
            actionLoading={actionLoading}
          />
        ) : (
          <EmptyState
            icon={CheckSquare}
            title="Approval Queue is Clear"
            description="There are currently no pending AIMD recommendations requiring human intervention. All models are operating within normal parameters or have already been authorized."
            action={
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={() => onNavigate?.('dashboard')}
              >
                <span>Return to Fleet Operations</span>
                <ArrowRight className="icon-xs" aria-hidden="true" />
              </button>
            }
          />
        )}
      </section>
    </div>
  );
}
