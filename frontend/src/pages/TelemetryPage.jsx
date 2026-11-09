import React from 'react';
import {
  Activity,
  TrendingUp,
  Grid,
  AlertTriangle,
  ArrowRight,
  Database,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader.jsx';
import { MetricCard } from '../components/MetricCard.jsx';
import { StatusBadge } from '../components/StatusBadge.jsx';
import { EmptyState } from '../components/EmptyState.jsx';
import { LoadingState } from '../components/LoadingState.jsx';
import { formatDate, formatMetric } from '../lib/utils.js';

export function TelemetryPage({
  user,
  dashboardData,
  loading = false,
  onNavigate,
}) {
  const monitoringSummary = dashboardData?.monitoring_summary || {};
  const totalObservations = monitoringSummary.total_observations || 0;
  const latestObservationAt = monitoringSummary.latest_observation_at;
  const latestF1 = monitoringSummary.latest_f1;
  const latestAccuracy = monitoringSummary.latest_accuracy;

  if (loading && !dashboardData) {
    return <LoadingState message="Loading telemetry trends..." />;
  }

  return (
    <div className="dashboard-content">
      {/* Page Header */}
      <PageHeader
        icon={Activity}
        title="Model Telemetry & Performance Trends"
        subtitle="Historical time-series tracking of classification accuracy, precision, recall, F1 score, and observation traffic."
        badge={
          <StatusBadge variant="info" size="sm">
            Phase 3B · Milestone 3
          </StatusBadge>
        }
      />

      {/* Telemetry Summary Metrics */}
      <div className="kpi-grid">
        <MetricCard
          icon={Database}
          title="Total Observations"
          value={totalObservations}
          subtext={latestObservationAt ? `Latest: ${formatDate(latestObservationAt)}` : 'No observations recorded'}
          badge={
            <StatusBadge variant="healthy" size="sm">
              Recorded Telemetry
            </StatusBadge>
          }
        />
        <MetricCard
          icon={TrendingUp}
          title="Latest F1 Benchmark"
          value={latestF1 !== null && latestF1 !== undefined ? formatMetric(latestF1, 4) : 'N/A'}
          subtext="Harmonic mean of precision and recall"
          badge={
            latestF1 !== null && latestF1 !== undefined ? (
              <StatusBadge variant="healthy" size="sm">
                F1: {formatMetric(latestF1, 2)}
              </StatusBadge>
            ) : null
          }
        />
        <MetricCard
          icon={Activity}
          title="Latest Accuracy"
          value={latestAccuracy !== null && latestAccuracy !== undefined ? `${(latestAccuracy * 100).toFixed(1)}%` : 'N/A'}
          subtext="Correct predictions percentage"
        />
        <MetricCard
          icon={AlertTriangle}
          title="Degradation Tracking"
          value={totalObservations > 0 ? 'Active' : 'Standby'}
          subtext="Monitored against reference baseline"
          badge={
            <StatusBadge variant={totalObservations > 0 ? 'healthy' : 'neutral'} size="sm">
              {totalObservations > 0 ? 'Live Stream' : 'Awaiting Data'}
            </StatusBadge>
          }
        />
      </div>

      {/* Milestone 3 Roadmap & Capabilities */}
      <section className="section">
        <div className="section-header">
          <h2 className="section-title">
            <TrendingUp className="icon-sm text-primary" aria-hidden="true" />
            <span>Telemetry & Visualization Roadmap (Milestone 3)</span>
          </h2>
          <span className="section-meta">Native SVG Visualizations</span>
        </div>

        <div className="roadmap-grid">
          <div className="roadmap-card">
            <div className="roadmap-card-header">
              <TrendingUp className="icon-sm text-primary" aria-hidden="true" />
              <h3 className="roadmap-card-title">Time-Series Performance Charts</h3>
            </div>
            <p className="roadmap-card-desc">
              Interactive multi-metric charts plotting historical F1, accuracy, precision, and recall across observations. Rendered using dependency-free React SVG with theme-reactive tokens.
            </p>
            <span className="roadmap-badge">GET /api/spam-models/{'{id}'}/monitoring</span>
          </div>

          <div className="roadmap-card">
            <div className="roadmap-card-header">
              <Grid className="icon-sm text-primary" aria-hidden="true" />
              <h3 className="roadmap-card-title">2x2 Confusion Matrix Heatmap</h3>
            </div>
            <p className="roadmap-card-desc">
              Visual confusion matrix displaying True Positives, False Positives, True Negatives, and False Negatives calculated from real holdout test set evaluations.
            </p>
            <span className="roadmap-badge">POST /api/spam-models/{'{id}'}/evaluate-telemetry</span>
          </div>

          <div className="roadmap-card">
            <div className="roadmap-card-header">
              <AlertTriangle className="icon-sm text-primary" aria-hidden="true" />
              <h3 className="roadmap-card-title">Degradation Delta Comparator</h3>
            </div>
            <p className="roadmap-card-desc">
              Side-by-side comparator showing metric drops when evaluating shifted operational data against deterministic UCI reference benchmarks.
            </p>
            <span className="roadmap-badge">Shifted Distribution Delta</span>
          </div>
        </div>
      </section>

      {/* Placeholder State */}
      <section className="section">
        <EmptyState
          icon={Activity}
          title="Telemetry Explorer Coming in Milestone 3"
          description="Interactive SVG performance trend charts, confusion matrix heatmaps, and metric degradation comparators will be activated in Phase 3B Milestone 3. Observations continue to be recorded via real evaluations in the Fleet Overview."
          action={
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => onNavigate?.('dashboard')}
            >
              <span>Run Model Evaluations in Fleet Overview</span>
              <ArrowRight className="icon-xs" aria-hidden="true" />
            </button>
          }
        />
      </section>
    </div>
  );
}
