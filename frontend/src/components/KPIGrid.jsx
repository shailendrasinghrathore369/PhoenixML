import React from 'react';
import { Cpu, Activity, ShieldCheck, CheckSquare } from 'lucide-react';
import { MetricCard } from './MetricCard.jsx';
import { StatusBadge } from './StatusBadge.jsx';
import { formatDate, formatMetric, getHealthClass } from '../lib/utils.js';

export function KPIGrid({ data, className }) {
  const models = data?.models_summary || {};
  const monitoring = data?.monitoring_summary || {};
  const health = data?.health_summary || {};
  const decisions = data?.decision_summary || {};

  const healthClass = getHealthClass(health.system_health_status);
  const pendingCount = decisions.pending_approvals_count || 0;

  return (
    <div className={`kpi-grid ${className || ''}`}>
      {/* KPI 1: Registered Models */}
      <MetricCard
        icon={Cpu}
        title="Registered Models"
        value={models.total_models || 0}
        badge={
          <StatusBadge variant="healthy" size="sm">
            {models.active_models || 0} Active
          </StatusBadge>
        }
        subtext={`Active: ${models.active_models || 0} · Dev: ${models.development_models || 0} · Archived: ${models.archived_models || 0}`}
      />

      {/* KPI 2: Telemetry & Observations */}
      <MetricCard
        icon={Activity}
        title="Telemetry & Observations"
        value={monitoring.total_observations || 0}
        badge={
          monitoring.latest_f1 !== null && monitoring.latest_f1 !== undefined ? (
            <StatusBadge variant="healthy" size="sm">
              F1: {formatMetric(monitoring.latest_f1, 2)}
            </StatusBadge>
          ) : null
        }
        subtext={
          monitoring.latest_observation_at
            ? `Latest: ${formatDate(monitoring.latest_observation_at)}`
            : 'No observations recorded'
        }
      />

      {/* KPI 3: Fleet Health Status */}
      <MetricCard
        icon={ShieldCheck}
        title="Fleet Health Status"
        value={
          health.average_health_score !== null && health.average_health_score !== undefined
            ? `${formatMetric(health.average_health_score, 1)}%`
            : 'N/A'
        }
        badge={
          <StatusBadge variant={healthClass} size="sm">
            {health.system_health_status || 'NO_DATA'}
          </StatusBadge>
        }
        subtext={`Healthy: ${health.healthy_count || 0} · Warning: ${health.warning_count || 0} · Critical: ${health.critical_count || 0}`}
      />

      {/* KPI 4: Pending Human Approvals */}
      <MetricCard
        icon={CheckSquare}
        title="Pending Human Approvals"
        value={pendingCount}
        highlight={pendingCount > 0}
        badge={
          <StatusBadge variant={pendingCount > 0 ? 'pending' : 'approved'} size="sm">
            {pendingCount > 0 ? 'Action Required' : 'All Clear'}
          </StatusBadge>
        }
        subtext={`Total Decisions: ${decisions.total_decisions || 0} · Approved: ${decisions.approved_count || 0} · Rejected: ${decisions.rejected_count || 0}`}
      />
    </div>
  );
}
