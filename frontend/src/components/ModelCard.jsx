import React from 'react';
import { Cpu, FlaskConical, TrendingDown, Zap, Search, CheckCircle } from 'lucide-react';
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
      className={cn(
        'model-card flex flex-col justify-between p-5 rounded-xl border bg-slate-900/80 text-slate-100 shadow-sm transition-all',
        isSelected
          ? 'selected border-blue-500/60 bg-slate-900 shadow-[0_0_15px_rgba(37,99,235,0.15)] ring-1 ring-blue-500/40'
          : 'border-slate-800 hover:border-slate-700 hover:bg-slate-800/40',
        className
      )}
    >
      <div className="model-card-top flex items-start justify-between gap-3 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-blue-400 flex-shrink-0" />
            <h3 className="model-name text-sm font-bold text-slate-100 truncate max-w-[200px]">
              {model.name}
            </h3>
          </div>
          <div className="model-meta text-[11px] text-slate-400 mt-1 font-mono">
            {model.framework} · ID: {String(model.model_id).substring(0, 8)}...
          </div>
        </div>
        <StatusBadge variant={model.status === 'ACTIVE' ? 'healthy' : 'insufficient'} size="sm">
          {model.status}
        </StatusBadge>
      </div>

      {/* Health Meter */}
      <div className="mb-4">
        <HealthIndicator
          score={model.latest_health_score}
          status={model.latest_health_status}
        />
      </div>

      {/* Inline Metrics */}
      <div className="metrics-row grid grid-cols-3 gap-2 p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/60 mb-4 text-center">
        <div className="metric-item">
          <span className="metric-item-name block text-[10px] uppercase font-semibold text-slate-400">
            Observations
          </span>
          <span className="metric-item-val text-xs font-bold font-mono text-slate-200">
            {model.observation_count || 0}
          </span>
        </div>
        <div className="metric-item">
          <span className="metric-item-name block text-[10px] uppercase font-semibold text-slate-400">
            Latest F1
          </span>
          <span className="metric-item-val text-xs font-bold font-mono text-slate-200">
            {formatMetric(model.latest_f1_score, 3)}
          </span>
        </div>
        <div className="metric-item">
          <span className="metric-item-name block text-[10px] uppercase font-semibold text-slate-400">
            Health Status
          </span>
          <span className="mt-0.5 inline-block">
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
            'p-3 rounded-lg border text-xs mb-4 animate-in fade-in',
            evalResult.datasetName === 'shifted'
              ? 'bg-rose-950/20 border-rose-500/35 text-rose-200'
              : 'bg-emerald-950/20 border-emerald-500/30 text-emerald-200'
          )}
        >
          <div className="flex items-center justify-between font-semibold mb-2">
            <span className="flex items-center gap-1.5">
              {evalResult.datasetName === 'shifted' ? (
                <>
                  <TrendingDown className="w-3.5 h-3.5 text-rose-400" />
                  <span className="text-rose-400">📉 Shifted Evaluation Results (Degraded):</span>
                </>
              ) : (
                <>
                  <FlaskConical className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-emerald-400">🔬 Reference Evaluation Results:</span>
                </>
              )}
            </span>
            <span className="text-[10px] font-mono text-slate-400">
              {evalResult.metrics.prediction_count} test samples
            </span>
          </div>

          <div className="grid grid-cols-4 gap-2 text-center py-1">
            <div>
              <div className="text-[10px] text-slate-400">Accuracy</div>
              <div className="font-bold font-mono text-slate-100">
                {(evalResult.metrics.accuracy * 100).toFixed(2)}%
              </div>
            </div>
            <div>
              <div className="text-[10px] text-slate-400">F1 Score</div>
              <div className="font-bold font-mono text-slate-100">
                {(evalResult.metrics.f1_score * 100).toFixed(2)}%
              </div>
            </div>
            <div>
              <div className="text-[10px] text-slate-400">Precision</div>
              <div className="font-bold font-mono text-slate-100">
                {(evalResult.metrics.precision * 100).toFixed(2)}%
              </div>
            </div>
            <div>
              <div className="text-[10px] text-slate-400">Recall</div>
              <div className="font-bold font-mono text-slate-100">
                {(evalResult.metrics.recall * 100).toFixed(2)}%
              </div>
            </div>
          </div>

          {evalResult.metrics.true_positives !== undefined && (
            <div className="flex justify-between items-center mt-2 pt-2 border-t border-slate-800 text-[10px] font-mono text-slate-400">
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
        <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/80 text-xs mb-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-slate-400 font-medium">Latest Recommendation:</span>
            <StatusBadge variant={getApprovalClass(decision.approval_status)} size="sm">
              {decision.approval_status}
            </StatusBadge>
          </div>
          <div className="font-semibold text-slate-200 truncate">
            {decision.recommended_action}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Priority: {decision.priority} · {formatDate(decision.created_at)}
          </div>
        </div>
      ) : (
        <div className="text-xs text-slate-400 italic p-3 text-center mb-4 border border-dashed border-slate-800 rounded-lg">
          No evaluation decisions recorded yet.
        </div>
      )}

      {/* Card Actions */}
      <div className="flex flex-wrap gap-2 pt-3 border-t border-slate-800/80 mt-auto">
        <button
          type="button"
          onClick={() => onSelect(model.model_id)}
          className={cn(
            'btn flex-1 min-w-[110px] inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg transition-colors',
            isSelected
              ? 'btn-primary bg-blue-600 text-white hover:bg-blue-700'
              : 'btn-secondary bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
          )}
        >
          <Search className="w-3.5 h-3.5" />
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
            className="btn btn-success flex-1 min-w-[160px] inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors disabled:opacity-50"
          >
            {isRefEvaluating ? (
              <span className="w-3.5 h-3.5 rounded-full border-2 border-white/30 border-t-white animate-spin" />
            ) : (
              <FlaskConical className="w-3.5 h-3.5" />
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
            className="btn flex-1 min-w-[160px] inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg bg-amber-600 hover:bg-amber-700 text-white transition-colors disabled:opacity-50"
          >
            {isShiftedEvaluating ? (
              <span className="w-3.5 h-3.5 rounded-full border-2 border-white/30 border-t-white animate-spin" />
            ) : (
              <TrendingDown className="w-3.5 h-3.5" />
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
          className="btn btn-outline flex-1 min-w-[120px] inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg border border-slate-700 hover:bg-slate-800 text-slate-200 transition-colors disabled:opacity-50"
        >
          {isEvaluating ? (
            <span className="w-3.5 h-3.5 rounded-full border-2 border-slate-300 border-t-blue-500 animate-spin" />
          ) : (
            <Zap className="w-3.5 h-3.5 text-amber-400" />
          )}
          <span>{isEvaluating ? 'Evaluating...' : '⚡ Trigger AIMD'}</span>
        </button>

        {showRealEval && (
          <div className="w-full text-center text-[11px] text-slate-400 italic mt-1">
            The model is not retrained. Only the evaluation data changes.
          </div>
        )}
      </div>
    </div>
  );
}
