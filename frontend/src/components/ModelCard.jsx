import React from 'react';
import { Cpu, FlaskConical, TrendingDown, Zap, Search } from 'lucide-react';
import { StatusBadge } from './StatusBadge.jsx';
import { HealthIndicator } from './HealthIndicator.jsx';
import { cn, formatDate, formatMetric, getApprovalClass, getHealthClass } from '../lib/utils.js';

export function ModelCard({
  model,
  isSelected,
  onSelect,
  onEvaluate,
  onRealEvaluate,
  evalResult,
  actionLoading,
  userRole,
  className,
}) {
  const isEvaluating = actionLoading === `evaluating-${model.model_id}`;
  const isRefEvaluating = actionLoading === `ref-eval-${model.model_id}`;
  const isShiftedEvaluating = actionLoading === `shifted-eval-${model.model_id}`;
  const isRealEvaluating = isRefEvaluating || isShiftedEvaluating;
  const isViewer = userRole === 'VIEWER';
  const hasDecision = !!model.latest_decision;
  const decision = model.latest_decision;
  const hasObservations = (model.observation_count || 0) > 0;
  const isRealModel =
    model.name === 'SpamSMS-LogisticRegression' ||
    (model.description && model.description.toLowerCase().includes('artifact'));
  const showRealEval = isRealModel || isSelected;

  return (
    <div
      className={cn('model-card', isSelected && 'selected', className)}
    >
      <div className="model-card-top">
        <div>
          <div className="model-title-wrap">
            <Cpu className="icon-sm model-icon" />
            <h3 className="model-name">
              {model.name}
            </h3>
          </div>
          <div className="model-meta">
            {model.framework} · ID: {String(model.model_id).substring(0, 8)}...
          </div>
        </div>
        <StatusBadge variant={model.status === 'ACTIVE' ? 'healthy' : 'insufficient'} size="sm">
          {model.status}
        </StatusBadge>
      </div>

      {/* Health Meter */}
      <div className="model-health-section">
        <HealthIndicator
          score={model.latest_health_score}
          status={model.latest_health_status}
        />
      </div>

      {/* Inline Metrics */}
      <div className="metrics-row">
        <div className="metric-item">
          <span className="metric-item-name">
            Observations
          </span>
          <span className="metric-item-val">
            {model.observation_count || 0}
          </span>
        </div>
        <div className="metric-item">
          <span className="metric-item-name">
            Latest F1
          </span>
          <span className="metric-item-val">
            {formatMetric(model.latest_f1_score, 3)}
          </span>
        </div>
        <div className="metric-item">
          <span className="metric-item-name">
            Health Status
          </span>
          <span className="metric-item-badge">
            <StatusBadge variant={getHealthClass(model.latest_health_status)} size="sm">
              {model.latest_health_status || 'NO_DATA'}
            </StatusBadge>
          </span>
        </div>
      </div>

      {/* Real Evaluation Metrics Result Banner */}
      {evalResult && evalResult.metrics && (
        <div
          className={cn(
            'eval-result-banner',
            evalResult.datasetName === 'shifted' ? 'shifted' : 'reference'
          )}
        >
          <div className="eval-result-header">
            <span className="eval-result-title">
              {evalResult.datasetName === 'shifted' ? (
                <>
                  <TrendingDown className="icon-xs" />
                  <span>📉 Shifted Evaluation Results (Degraded):</span>
                </>
              ) : (
                <>
                  <FlaskConical className="icon-xs" />
                  <span>🔬 Reference Evaluation Results:</span>
                </>
              )}
            </span>
            <span className="eval-result-sample-count">
              {evalResult.metrics.prediction_count} test samples
            </span>
          </div>

          <div className="eval-result-metrics-grid">
            <div>
              <div className="eval-metric-label">Accuracy</div>
              <div className="eval-metric-val">
                {(evalResult.metrics.accuracy * 100).toFixed(2)}%
              </div>
            </div>
            <div>
              <div className="eval-metric-label">F1 Score</div>
              <div className="eval-metric-val">
                {(evalResult.metrics.f1_score * 100).toFixed(2)}%
              </div>
            </div>
            <div>
              <div className="eval-metric-label">Precision</div>
              <div className="eval-metric-val">
                {(evalResult.metrics.precision * 100).toFixed(2)}%
              </div>
            </div>
            <div>
              <div className="eval-metric-label">Recall</div>
              <div className="eval-metric-val">
                {(evalResult.metrics.recall * 100).toFixed(2)}%
              </div>
            </div>
          </div>

          {evalResult.metrics.true_positives !== undefined && (
            <div className="eval-confusion-row">
              <span>TN: {evalResult.metrics.true_negatives}</span>
              <span>FP: {evalResult.metrics.false_positives}</span>
              <span>FN: {evalResult.metrics.false_negatives}</span>
              <span>TP: {evalResult.metrics.true_positives}</span>
            </div>
          )}
        </div>
      )}

      {/* Latest Decision snippet */}
      {hasDecision ? (
        <div className="model-decision-snippet">
          <div className="model-decision-snippet-header">
            <span className="model-decision-label">Latest Recommendation:</span>
            <StatusBadge variant={getApprovalClass(decision.approval_status)} size="sm">
              {decision.approval_status}
            </StatusBadge>
          </div>
          <div className="model-decision-action">
            {decision.recommended_action}
          </div>
          <div className="model-decision-meta">
            Priority: {decision.priority} · {formatDate(decision.created_at)}
          </div>
        </div>
      ) : (
        <div className="model-decision-snippet-empty">
          No evaluation decisions recorded yet.
        </div>
      )}

      {/* Card Actions */}
      <div className="model-card-actions">
        <button
          type="button"
          onClick={() => onSelect(model.model_id)}
          className={cn('btn', isSelected ? 'btn-primary' : 'btn-outline')}
          aria-label={isSelected ? `Focused on model ${model.name}` : `Inspect model ${model.name}`}
        >
          <Search className="icon-sm" />
          <span>{isSelected ? 'Focused' : 'Inspect Model'}</span>
        </button>

        {showRealEval && (
          <button
            type="button"
            onClick={() => onRealEvaluate(model.model_id, 'reference')}
            disabled={isViewer || isRealEvaluating || isEvaluating}
            title={
              isViewer
                ? 'Viewers cannot run real model evaluations'
                : 'Evaluate the model on its original holdout test set.'
            }
            className="btn btn-success"
            aria-label="Run reference evaluation on holdout test set"
          >
            {isRefEvaluating ? (
              <span className="btn-spinner" aria-hidden="true" />
            ) : (
              <FlaskConical className="icon-sm" />
            )}
            <span>{isRefEvaluating ? 'Evaluating Reference...' : '🔬 Run Reference Evaluation'}</span>
          </button>
        )}

        {showRealEval && (
          <button
            type="button"
            onClick={() => onRealEvaluate(model.model_id, 'shifted')}
            disabled={isViewer || isRealEvaluating || isEvaluating}
            title={
              isViewer
                ? 'Viewers cannot run real model evaluations'
                : 'Evaluate the same trained model on the new shifted operational dataset.'
            }
            className="btn btn-warning"
            aria-label="Run shifted data evaluation"
          >
            {isShiftedEvaluating ? (
              <span className="btn-spinner" aria-hidden="true" />
            ) : (
              <TrendingDown className="icon-sm" />
            )}
            <span>{isShiftedEvaluating ? 'Evaluating Shifted...' : '📉 Run Shifted Data Evaluation'}</span>
          </button>
        )}

        <button
          type="button"
          onClick={() => onEvaluate(model.model_id)}
          disabled={isViewer || isEvaluating || isRealEvaluating || !hasObservations}
          title={
            isViewer
              ? 'Viewers cannot trigger evaluations'
              : !hasObservations
              ? 'No monitoring observations. Run evaluation first.'
              : 'Trigger AIMD Evaluation'
          }
          className="btn btn-outline"
          aria-label="Trigger AIMD automated evaluation"
        >
          {isEvaluating ? (
            <span className="btn-spinner" aria-hidden="true" />
          ) : (
            <Zap className="icon-sm text-warning" />
          )}
          <span>{isEvaluating ? 'Evaluating...' : '⚡ Trigger AIMD'}</span>
        </button>

        {showRealEval && (
          <div className="model-eval-disclaimer">
            The model is not retrained. Only the evaluation data changes.
          </div>
        )}
      </div>
    </div>
  );
}
