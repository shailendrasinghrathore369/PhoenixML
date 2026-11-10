import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  Activity,
  TrendingUp,
  Grid,
  AlertTriangle,
  ArrowRight,
  Database,
  Filter,
  History,
  ChevronLeft,
  ChevronRight,
  Cpu,
  Layers,
  Info,
  X,
  Play,
  AlertCircle,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader.jsx';
import { MetricCard } from '../components/MetricCard.jsx';
import { StatusBadge } from '../components/StatusBadge.jsx';
import { DataTable } from '../components/DataTable.jsx';
import { EmptyState } from '../components/EmptyState.jsx';
import { LoadingState } from '../components/LoadingState.jsx';
import { ErrorState } from '../components/ErrorState.jsx';
import { TelemetryChart } from '../components/TelemetryChart.jsx';
import { ConfirmationDialog } from '../components/ConfirmationDialog.jsx';
import { ConfusionMatrix } from '../components/ConfusionMatrix.jsx';
import { api } from '../lib/api.js';
import { formatDate, formatMetric, canPerformActions } from '../lib/utils.js';

const PAGE_SIZE = 10;

export function TelemetryPage({
  user,
  dashboardData,
  selectedModelId,
  setSelectedModelId,
  modelMap = {},
  loading = false,
  onNavigate,
  toast,
}) {
  // Extract seed models from dashboard overview if available
  const initialModels = useMemo(() => {
    if (dashboardData?.model_cards && Array.isArray(dashboardData.model_cards)) {
      return dashboardData.model_cards.map((c) => ({
        id: c.model_id || c.id,
        name: c.name,
        status: c.status || 'DEVELOPMENT',
        framework: c.framework || 'scikit-learn',
        algorithm: c.algorithm || '',
        ...c,
      }));
    }
    return [];
  }, [dashboardData]);

  const [models, setModels] = useState(initialModels);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [modelsError, setModelsError] = useState(null);

  const [internalModelId, setInternalModelId] = useState('');
  const [observations, setObservations] = useState([]);
  const [obsLoading, setObsLoading] = useState(false);
  const [obsError, setObsError] = useState(null);
  const [skip, setSkip] = useState(0);

  // Real dataset evaluation and comparison state
  const [referenceResult, setReferenceResult] = useState(null);
  const [shiftedResult, setShiftedResult] = useState(null);
  const [evaluatingDataset, setEvaluatingDataset] = useState(null);
  const [evalConfirmType, setEvalConfirmType] = useState(null);
  const [evalError, setEvalError] = useState(null);
  const [activeConfusionDataset, setActiveConfusionDataset] = useState('reference');

  // Sync initialModels if dashboardData loads later
  useEffect(() => {
    if (initialModels.length > 0 && models.length === 0) {
      setModels(initialModels);
    }
  }, [initialModels, models.length]);

  // Load registered models from Model Registry API
  useEffect(() => {
    let isMounted = true;
    const fetchModels = async () => {
      setModelsLoading(true);
      setModelsError(null);
      try {
        const data = await api.listModels({ skip: 0, limit: 100 });
        if (isMounted && Array.isArray(data)) {
          setModels(data);
        }
      } catch (err) {
        if (isMounted) {
          if (initialModels.length === 0) {
            let msg = err.message || 'Failed to load registered models.';
            if (err.status === 403 || msg.toLowerCase().includes('forbidden') || msg.toLowerCase().includes('permission')) {
              msg = 'Access denied: You do not have permission to view registered models.';
            }
            setModelsError(msg);
            toast?.error?.(msg);
          }
        }
      } finally {
        if (isMounted) {
          setModelsLoading(false);
        }
      }
    };

    fetchModels();

    return () => {
      isMounted = false;
    };
  }, [user?.id, user?.role, initialModels.length, toast]);

  // Determine current active model ID
  const effectiveModelId = useMemo(() => {
    if (selectedModelId) return selectedModelId;
    if (internalModelId) return internalModelId;
    if (models.length > 0) return models[0].id || models[0].model_id;
    return '';
  }, [selectedModelId, internalModelId, models]);

  // Auto-select first model in parent state if none selected
  useEffect(() => {
    if (!selectedModelId && effectiveModelId && setSelectedModelId) {
      setSelectedModelId(effectiveModelId);
    }
  }, [selectedModelId, effectiveModelId, setSelectedModelId]);

  // Model object lookup
  const selectedModel = useMemo(() => {
    if (!effectiveModelId) return null;
    return (
      models.find((m) => (m.id || m.model_id) === effectiveModelId) ||
      modelMap[effectiveModelId] ||
      null
    );
  }, [models, effectiveModelId, modelMap]);

  // Fetch observations for selected model
  const fetchObservations = useCallback(async (modelId, currentSkip) => {
    if (!modelId) {
      setObservations([]);
      return;
    }
    setObsLoading(true);
    setObsError(null);
    try {
      const data = await api.listObservations(modelId, { skip: currentSkip, limit: PAGE_SIZE });
      setObservations(Array.isArray(data) ? data : []);
    } catch (err) {
      let msg = err.message || 'Failed to load telemetry observations.';
      if (err.status === 403 || msg.toLowerCase().includes('forbidden') || msg.toLowerCase().includes('permission')) {
        msg = 'Access denied: You do not have permission to view observations for this model.';
      } else if (err.status === 404 || msg.toLowerCase().includes('not found')) {
        msg = 'Model not found or has no available telemetry records.';
      }
      setObsError(msg);
      toast?.error?.(msg);
    } finally {
      setObsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    if (effectiveModelId) {
      fetchObservations(effectiveModelId, skip);
    } else {
      setObservations([]);
    }
  }, [effectiveModelId, skip, fetchObservations]);

  // Track previous modelId to discard stale evaluation results on model switch
  const prevModelIdRef = useRef(effectiveModelId);
  useEffect(() => {
    if (prevModelIdRef.current && prevModelIdRef.current !== effectiveModelId) {
      setReferenceResult(null);
      setShiftedResult(null);
      setEvalError(null);
    }
    prevModelIdRef.current = effectiveModelId;
  }, [effectiveModelId]);

  // Handle model change from dropdown without page reload
  const handleModelChange = (newModelId) => {
    if (setSelectedModelId) {
      setSelectedModelId(newModelId);
    }
    setInternalModelId(newModelId);
    setSkip(0);
    setReferenceResult(null);
    setShiftedResult(null);
    setEvalError(null);
  };

  const isAuthorized = canPerformActions(user?.role);

  // Trigger confirmation dialog for evaluation
  const handleStartEvaluation = (datasetType) => {
    setEvalError(null);
    setEvalConfirmType(datasetType);
  };

  // Execute confirmed evaluation against backend API
  const handleConfirmEvaluation = async () => {
    const datasetType = evalConfirmType;
    if (!datasetType || !effectiveModelId) return;

    setEvaluatingDataset(datasetType);
    setEvalError(null);
    try {
      const payload =
        datasetType === 'reference'
          ? {
              use_reference_test_set: true,
              record_monitoring_observation: true,
              dataset_name: 'reference',
            }
          : {
              use_reference_test_set: false,
              record_monitoring_observation: true,
              dataset_name: 'shifted',
            };

      const res = await api.evaluateModelTelemetry(effectiveModelId, payload);
      if (datasetType === 'reference') {
        setReferenceResult(res);
        setActiveConfusionDataset('reference');
      } else {
        setShiftedResult(res);
        setActiveConfusionDataset('shifted');
      }

      toast?.success?.(
        `Successfully completed ${datasetType} evaluation! Monitoring observation recorded.`
      );

      // Refresh observations log & chart with newly recorded observation
      await fetchObservations(effectiveModelId, skip);
    } catch (err) {
      let msg = err.message || `Failed to execute ${datasetType} evaluation.`;
      if (
        err.status === 403 ||
        msg.toLowerCase().includes('forbidden') ||
        msg.toLowerCase().includes('permission') ||
        msg.toLowerCase().includes('not authorized')
      ) {
        msg = 'Access denied: Only ML Engineers and Administrators can evaluate model telemetry.';
      }
      setEvalError(msg);
      toast?.error?.(msg);
    } finally {
      setEvaluatingDataset(null);
      setEvalConfirmType(null);
    }
  };

  // Helper to calculate percentage-point delta between reference and shifted metrics
  const calcMetricDelta = (refVal, shiftedVal) => {
    if (
      refVal === null ||
      refVal === undefined ||
      shiftedVal === null ||
      shiftedVal === undefined ||
      isNaN(refVal) ||
      isNaN(shiftedVal)
    ) {
      return { delta: null, formatted: 'N/A', isDegraded: false };
    }
    const delta = (shiftedVal - refVal) * 100;
    const sign = delta > 0 ? '+' : '';
    const formatted = `${sign}${delta.toFixed(2)} pp`;
    return {
      delta,
      formatted,
      isDegraded: delta < -0.001,
    };
  };

  // Pagination handlers
  const handlePrevPage = () => {
    setSkip((prev) => Math.max(0, prev - PAGE_SIZE));
  };

  const handleNextPage = () => {
    setSkip((prev) => prev + PAGE_SIZE);
  };

  // Sort observations newest first (consistent with backend behavior)
  const sortedObservations = useMemo(() => {
    if (!Array.isArray(observations)) return [];
    return [...observations].sort((a, b) => {
      const timeA = new Date(a.observed_at || a.created_at || a.timestamp || 0).getTime();
      const timeB = new Date(b.observed_at || b.created_at || b.timestamp || 0).getTime();
      return timeB - timeA;
    });
  }, [observations]);

  // Calculate summary metrics strictly from real observations without fabricated data
  const metricsSummary = useMemo(() => {
    if (!sortedObservations || sortedObservations.length === 0) {
      return {
        hasData: false,
        latestObs: null,
        latestF1: null,
        latestAccuracy: null,
        latestPrecision: null,
        latestRecall: null,
        avgF1: null,
        avgAccuracy: null,
        avgPrecision: null,
        avgRecall: null,
        f1Count: 0,
        accCount: 0,
        precCount: 0,
        recallCount: 0,
        totalPredictions: 0,
      };
    }

    const latest = sortedObservations[0];

    const calcAvg = (accessor) => {
      const valid = sortedObservations
        .map(accessor)
        .filter((v) => v !== null && v !== undefined && !isNaN(v) && typeof v === 'number');
      if (valid.length === 0) return { avg: null, count: 0 };
      const sum = valid.reduce((acc, curr) => acc + curr, 0);
      return { avg: sum / valid.length, count: valid.length };
    };

    const f1Stats = calcAvg((o) => o.f1_score ?? o.f1);
    const accStats = calcAvg((o) => o.accuracy);
    const precStats = calcAvg((o) => o.precision);
    const recStats = calcAvg((o) => o.recall);

    const totalPredictions = sortedObservations.reduce(
      (sum, o) => sum + (typeof o.prediction_count === 'number' ? o.prediction_count : 0),
      0
    );

    return {
      hasData: true,
      latestObs: latest,
      latestF1: latest.f1_score ?? latest.f1 ?? null,
      latestAccuracy: latest.accuracy ?? null,
      latestPrecision: latest.precision ?? null,
      latestRecall: latest.recall ?? null,
      avgF1: f1Stats.avg,
      avgAccuracy: accStats.avg,
      avgPrecision: precStats.avg,
      avgRecall: recStats.avg,
      f1Count: f1Stats.count,
      accCount: accStats.count,
      precCount: precStats.count,
      recallCount: recStats.count,
      totalPredictions,
    };
  }, [sortedObservations]);

  // Retry handler
  const handleRetry = () => {
    if (modelsError && models.length === 0) {
      api.listModels({ skip: 0, limit: 100 })
        .then((data) => {
          if (Array.isArray(data)) {
            setModels(data);
            setModelsError(null);
          }
        })
        .catch((err) => {
          setModelsError(err.message || 'Failed to load registered models.');
        });
    } else if (effectiveModelId) {
      fetchObservations(effectiveModelId, skip);
    }
  };

  // Table columns definition
  const columns = [
    {
      key: 'observed_at',
      header: 'Observed At',
      render: (val, row) => (
        <span className="font-mono text-xs">
          {formatDate(val || row.created_at || row.timestamp)}
        </span>
      ),
    },
    {
      key: 'prediction_count',
      header: 'Total Predictions',
      align: 'right',
      render: (val) => (
        <span className="font-mono">
          {val !== null && val !== undefined ? Number(val).toLocaleString() : 'N/A'}
        </span>
      ),
    },
    {
      key: 'positive_prediction_count',
      header: 'Positive (Spam)',
      align: 'right',
      render: (val) => (
        <span className="font-mono text-emerald-400">
          {val !== null && val !== undefined ? Number(val).toLocaleString() : 'N/A'}
        </span>
      ),
    },
    {
      key: 'negative_prediction_count',
      header: 'Negative (Ham)',
      align: 'right',
      render: (val) => (
        <span className="font-mono text-sky-400">
          {val !== null && val !== undefined ? Number(val).toLocaleString() : 'N/A'}
        </span>
      ),
    },
    {
      key: 'accuracy',
      header: 'Accuracy',
      align: 'right',
      render: (val) => (
        <span className="font-mono">
          {val !== null && val !== undefined ? formatMetric(val, 4) : 'N/A'}
        </span>
      ),
    },
    {
      key: 'precision',
      header: 'Precision',
      align: 'right',
      render: (val) => (
        <span className="font-mono">
          {val !== null && val !== undefined ? formatMetric(val, 4) : 'N/A'}
        </span>
      ),
    },
    {
      key: 'recall',
      header: 'Recall',
      align: 'right',
      render: (val) => (
        <span className="font-mono">
          {val !== null && val !== undefined ? formatMetric(val, 4) : 'N/A'}
        </span>
      ),
    },
    {
      key: 'f1_score',
      header: 'F1 Score',
      align: 'right',
      render: (val, row) => {
        const score = val ?? row.f1;
        return (
          <span className="font-mono font-semibold text-primary">
            {score !== null && score !== undefined ? formatMetric(score, 4) : 'N/A'}
          </span>
        );
      },
    },
  ];

  // Global loading when models and dashboard data are completely absent
  if (loading && !dashboardData && models.length === 0) {
    return (
      <div className="dashboard-content">
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
        <LoadingState message="Loading telemetry & observations..." />
      </div>
    );
  }

  // Model loading state
  if (modelsLoading && models.length === 0) {
    return (
      <div className="dashboard-content">
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
        <LoadingState message="Loading registered models..." />
      </div>
    );
  }

  // Models error state when no models could be retrieved
  if (modelsError && models.length === 0) {
    return (
      <div className="dashboard-content">
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
        <ErrorState
          title="Unable to Load Models"
          message={modelsError}
          onRetry={handleRetry}
        />
      </div>
    );
  }

  // Empty state when fleet has zero registered models
  if (!modelsLoading && models.length === 0) {
    return (
      <div className="dashboard-content">
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
        <EmptyState
          icon={Cpu}
          title="No Registered Models Found"
          description="There are no registered models in your scope. Models must be registered before telemetry observations can be tracked."
          action={
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => onNavigate?.('models')}
            >
              <span>Go to Model Registry</span>
              <ArrowRight className="icon-xs" aria-hidden="true" />
            </button>
          }
        />
      </div>
    );
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

      {/* Model Selector Bar */}
      <div className="filter-bar">
        <div className="filter-group">
          <Filter className="icon-sm filter-icon" aria-hidden="true" />
          <label htmlFor="telemetry-model-select" className="filter-label">
            Model Scope:
          </label>
          <select
            id="telemetry-model-select"
            className="model-select"
            value={effectiveModelId}
            onChange={(e) => handleModelChange(e.target.value)}
            aria-label="Select registered model"
            disabled={modelsLoading}
          >
            {models.map((m) => {
              const mId = m.id || m.model_id;
              return (
                <option key={mId} value={mId}>
                  {m.name} ({m.status || 'DEVELOPMENT'})
                </option>
              );
            })}
          </select>
        </div>

        {selectedModel && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              Framework: <strong style={{ color: 'var(--text-primary)' }}>{selectedModel.framework || 'scikit-learn'}</strong>
            </span>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
              Algorithm: <strong style={{ color: 'var(--text-primary)' }}>{selectedModel.algorithm || 'LogisticRegression'}</strong>
            </span>
            <StatusBadge variant={selectedModel.status === 'ACTIVE' ? 'healthy' : 'neutral'} size="sm">
              {selectedModel.status || 'DEVELOPMENT'}
            </StatusBadge>
          </div>
        )}
      </div>

      {/* Telemetry Summary Metrics */}
      <div className="kpi-grid">
        <MetricCard
          icon={TrendingUp}
          title="Latest F1 Score"
          value={metricsSummary.latestF1 !== null ? formatMetric(metricsSummary.latestF1, 4) : 'N/A'}
          subtext={
            metricsSummary.latestObs?.observed_at
              ? `Observed: ${formatDate(metricsSummary.latestObs.observed_at)}`
              : 'No observation data'
          }
          badge={
            <StatusBadge variant={metricsSummary.latestF1 !== null ? 'healthy' : 'neutral'} size="sm">
              Latest Observation
            </StatusBadge>
          }
        />
        <MetricCard
          icon={TrendingUp}
          title="Historical Avg F1"
          value={metricsSummary.avgF1 !== null ? formatMetric(metricsSummary.avgF1, 4) : 'N/A'}
          subtext={
            metricsSummary.f1Count > 0
              ? `Mean of ${metricsSummary.f1Count} recorded observation${metricsSummary.f1Count > 1 ? 's' : ''}`
              : 'No valid metric values'
          }
          badge={
            <StatusBadge variant="info" size="sm">
              Historical Average
            </StatusBadge>
          }
        />
        <MetricCard
          icon={Activity}
          title="Latest Accuracy"
          value={
            metricsSummary.latestAccuracy !== null
              ? `${(metricsSummary.latestAccuracy * 100).toFixed(1)}%`
              : 'N/A'
          }
          subtext={
            metricsSummary.latestObs?.prediction_count !== undefined && metricsSummary.latestObs?.prediction_count !== null
              ? `${metricsSummary.latestObs.prediction_count.toLocaleString()} predictions evaluated`
              : 'No observation data'
          }
          badge={
            <StatusBadge variant={metricsSummary.latestAccuracy !== null ? 'healthy' : 'neutral'} size="sm">
              Latest Observation
            </StatusBadge>
          }
        />
        <MetricCard
          icon={Activity}
          title="Historical Avg Accuracy"
          value={
            metricsSummary.avgAccuracy !== null
              ? `${(metricsSummary.avgAccuracy * 100).toFixed(1)}%`
              : 'N/A'
          }
          subtext={
            metricsSummary.accCount > 0
              ? `Mean of ${metricsSummary.accCount} recorded observation${metricsSummary.accCount > 1 ? 's' : ''}`
              : 'No valid metric values'
          }
          badge={
            <StatusBadge variant="info" size="sm">
              Historical Average
            </StatusBadge>
          }
        />
        <MetricCard
          icon={Database}
          title="Historical Avg Precision"
          value={metricsSummary.avgPrecision !== null ? formatMetric(metricsSummary.avgPrecision, 4) : 'N/A'}
          subtext={
            metricsSummary.precCount > 0
              ? `Mean of ${metricsSummary.precCount} observation${metricsSummary.precCount > 1 ? 's' : ''}`
              : 'No valid precision data'
          }
          badge={
            <StatusBadge variant="neutral" size="sm">
              Historical Average
            </StatusBadge>
          }
        />
        <MetricCard
          icon={Database}
          title="Historical Avg Recall"
          value={metricsSummary.avgRecall !== null ? formatMetric(metricsSummary.avgRecall, 4) : 'N/A'}
          subtext={
            metricsSummary.recallCount > 0
              ? `Mean of ${metricsSummary.recallCount} observation${metricsSummary.recallCount > 1 ? 's' : ''}`
              : 'No valid recall data'
          }
          badge={
            <StatusBadge variant="neutral" size="sm">
              Historical Average
            </StatusBadge>
          }
        />
      </div>

      {/* Observation Table / State Section */}
      <section className="section">
        {obsError ? (
          <ErrorState
            title="Failed to Load Telemetry Observations"
            message={obsError}
            onRetry={handleRetry}
          />
        ) : obsLoading && sortedObservations.length === 0 ? (
          <LoadingState message="Loading historical observations for selected model..." />
        ) : sortedObservations.length === 0 ? (
          <EmptyState
            icon={Activity}
            title="No Historical Observations Recorded"
            description={`No monitoring observations have been recorded for ${selectedModel?.name || 'this model'} yet. Run model evaluations in the Fleet Overview to record genuine telemetry.`}
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
        ) : (
          <div>
            {/* Native SVG Time-Series Chart Visualizer */}
            <TelemetryChart
              observations={observations}
              modelName={selectedModel?.name}
              loading={obsLoading}
            />

            {/* Real Dataset Evaluation, Degradation Comparator & Confusion Matrix Section */}
            <div
              className="dataset-comparator-section"
              data-testid="section-dataset-comparator"
              style={{ marginTop: '2rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}
            >
              <div className="section-header">
                <h2 className="section-title">
                  <Layers className="icon-sm text-primary" aria-hidden="true" />
                  <span>Dataset Evaluation & Degradation Comparator</span>
                </h2>
                <span className="section-meta">
                  Reference (UCI) vs Shifted (Operational Proxy)
                </span>
              </div>

              <div
                className="table-card"
                style={{
                  padding: '1.25rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1.25rem',
                }}
              >
                {/* Evaluation Action Bar */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '1rem',
                    borderBottom: '1px solid var(--border-color)',
                    paddingBottom: '1rem',
                  }}
                >
                  <div>
                    <h3
                      style={{
                        fontSize: '0.9375rem',
                        fontWeight: 600,
                        color: 'var(--text-primary)',
                        margin: 0,
                      }}
                    >
                      Ground-Truth Evaluation Triggers
                    </h3>
                    <p
                      style={{
                        fontSize: '0.8125rem',
                        color: 'var(--text-secondary)',
                        margin: '0.2rem 0 0 0',
                      }}
                    >
                      Evaluate genuine model performance against reference benchmark or operational distribution shift
                    </p>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      className="btn btn-sm btn-outline"
                      disabled={!isAuthorized || !!evaluatingDataset}
                      onClick={() => handleStartEvaluation('reference')}
                      data-testid="btn-run-reference-eval"
                      aria-label="Run Reference Evaluation"
                      style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}
                    >
                      {evaluatingDataset === 'reference' ? (
                        <span className="btn-spinner" aria-hidden="true" />
                      ) : (
                        <Database className="icon-xs text-primary" aria-hidden="true" />
                      )}
                      <span>Run Reference Evaluation</span>
                    </button>

                    <button
                      type="button"
                      className="btn btn-sm btn-outline"
                      disabled={!isAuthorized || !!evaluatingDataset}
                      onClick={() => handleStartEvaluation('shifted')}
                      data-testid="btn-run-shifted-eval"
                      aria-label="Run Shifted Evaluation"
                      style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}
                    >
                      {evaluatingDataset === 'shifted' ? (
                        <span className="btn-spinner" aria-hidden="true" />
                      ) : (
                        <AlertTriangle className="icon-xs text-warning" aria-hidden="true" />
                      )}
                      <span>Run Shifted Evaluation</span>
                    </button>

                    {!isAuthorized && (
                      <span
                        style={{
                          fontSize: '0.75rem',
                          color: 'var(--text-muted)',
                          fontStyle: 'italic',
                        }}
                      >
                        Read-only: Evaluation requires ML Engineer or Admin role
                      </span>
                    )}
                  </div>
                </div>

                {/* Evaluation Error Alert */}
                {evalError && (
                  <div
                    className="alert alert-critical"
                    data-testid="eval-error-alert"
                    role="alert"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '0.75rem',
                      padding: '0.75rem 1rem',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--critical-bg)',
                      border: '1px solid var(--critical-border)',
                      color: 'var(--color-critical)',
                      fontSize: '0.8125rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <AlertCircle className="icon-sm" aria-hidden="true" />
                      <span>{evalError}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setEvalError(null)}
                      aria-label="Dismiss error"
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'inherit',
                        cursor: 'pointer',
                        padding: '0.25rem',
                      }}
                    >
                      <X className="icon-xs" aria-hidden="true" />
                    </button>
                  </div>
                )}

                {/* Evaluated Dataset Status Badges */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1.25rem',
                    flexWrap: 'wrap',
                    fontSize: '0.75rem',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.375rem',
                      color: referenceResult ? 'var(--text-primary)' : 'var(--text-muted)',
                    }}
                  >
                    <span
                      style={{
                        display: 'inline-block',
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        backgroundColor: referenceResult ? 'var(--color-healthy)' : 'var(--border-color)',
                      }}
                    />
                    <span>Reference Dataset:</span>
                    <strong>
                      {referenceResult
                        ? `Evaluated (${formatDate(referenceResult.evaluated_at)}) · N=${referenceResult.metrics?.prediction_count}`
                        : 'Not evaluated in session'}
                    </strong>
                  </div>

                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.375rem',
                      color: shiftedResult ? 'var(--text-primary)' : 'var(--text-muted)',
                    }}
                  >
                    <span
                      style={{
                        display: 'inline-block',
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        backgroundColor: shiftedResult ? 'var(--color-warning)' : 'var(--border-color)',
                      }}
                    />
                    <span>Shifted Dataset:</span>
                    <strong>
                      {shiftedResult
                        ? `Evaluated (${formatDate(shiftedResult.evaluated_at)}) · N=${shiftedResult.metrics?.prediction_count}`
                        : 'Not evaluated in session'}
                    </strong>
                  </div>
                </div>

                {/* Comparison Table or Explanatory State */}
                {!referenceResult && !shiftedResult ? (
                  <div
                    data-testid="comparison-empty-state"
                    style={{
                      padding: '2rem 1rem',
                      textAlign: 'center',
                      backgroundColor: 'var(--surface-subtle, rgba(0, 0, 0, 0.02))',
                      borderRadius: 'var(--radius-md)',
                      border: '1px dashed var(--border-color)',
                      color: 'var(--text-secondary)',
                      fontSize: '0.8125rem',
                    }}
                  >
                    <p style={{ margin: '0 0 0.5rem 0', fontWeight: 600, color: 'var(--text-primary)' }}>
                      No active evaluations recorded in this session.
                    </p>
                    <p style={{ margin: 0 }}>
                      Run both Reference (UCI Holdout) and Shifted (Operational) evaluations above to inspect empirical performance degradation and confusion matrices.
                    </p>
                  </div>
                ) : !referenceResult || !shiftedResult ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <div
                      data-testid="comparison-requires-both"
                      style={{
                        padding: '1rem',
                        backgroundColor: 'var(--warning-bg, rgba(245, 158, 11, 0.08))',
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid var(--warning-border, rgba(245, 158, 11, 0.35))',
                        color: 'var(--text-primary)',
                        fontSize: '0.8125rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                      }}
                    >
                      <Info className="icon-sm text-warning" aria-hidden="true" />
                      <span>
                        Comparison requires both results. Run the <strong>{!referenceResult ? 'Reference' : 'Shifted'}</strong> evaluation to compute side-by-side performance degradation deltas.
                      </span>
                    </div>

                    {/* Single evaluated dataset card */}
                    <div
                      className="kpi-grid"
                      style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}
                    >
                      {(() => {
                        const single = referenceResult || shiftedResult;
                        const isRef = !!referenceResult;
                        return [
                          { label: 'Accuracy', val: single.metrics?.accuracy },
                          { label: 'Precision', val: single.metrics?.precision },
                          { label: 'Recall', val: single.metrics?.recall },
                          { label: 'F1 Score', val: single.metrics?.f1_score },
                        ].map((item) => (
                          <div
                            key={item.label}
                            className="kpi-card"
                            style={{ padding: '0.75rem 1rem' }}
                          >
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                              {isRef ? 'Reference' : 'Shifted'} {item.label}
                            </div>
                            <div
                              style={{
                                fontSize: '1.25rem',
                                fontWeight: 700,
                                fontFamily: 'var(--font-mono)',
                                color: 'var(--text-primary)',
                                marginTop: '0.25rem',
                              }}
                            >
                              {item.val !== null && item.val !== undefined
                                ? `${(item.val * 100).toFixed(2)}%`
                                : 'N/A'}
                            </div>
                          </div>
                        ));
                      })()}
                    </div>
                  </div>
                ) : (
                  /* Both Evaluated: Full Side-by-Side Comparison Table */
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div style={{ width: '100%', overflowX: 'auto' }}>
                      <table
                        className="dataset-comparison-table"
                        data-testid="dataset-comparison-table"
                        style={{
                          width: '100%',
                          borderCollapse: 'collapse',
                          fontSize: '0.8125rem',
                        }}
                      >
                        <thead>
                          <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left' }}>
                            <th scope="col" style={{ padding: '0.75rem 1rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                              Metric
                            </th>
                            <th scope="col" style={{ padding: '0.75rem 1rem', color: 'var(--color-healthy)', fontWeight: 600, textAlign: 'right' }}>
                              Reference (UCI Holdout)
                            </th>
                            <th scope="col" style={{ padding: '0.75rem 1rem', color: 'var(--color-warning)', fontWeight: 600, textAlign: 'right' }}>
                              Shifted (Operational)
                            </th>
                            <th scope="col" style={{ padding: '0.75rem 1rem', color: 'var(--text-secondary)', fontWeight: 600, textAlign: 'right' }}>
                              Degradation Delta
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {[
                            { name: 'Accuracy', key: 'accuracy' },
                            { name: 'Precision', key: 'precision' },
                            { name: 'Recall', key: 'recall' },
                            { name: 'F1 Score', key: 'f1_score' },
                          ].map(({ name, key }) => {
                            const refVal = referenceResult.metrics?.[key];
                            const shiftedVal = shiftedResult.metrics?.[key];
                            const deltaInfo = calcMetricDelta(refVal, shiftedVal);
                            return (
                              <tr
                                key={key}
                                data-testid={`comparison-row-${key}`}
                                style={{ borderBottom: '1px solid var(--border-subtle, rgba(255, 255, 255, 0.05))' }}
                              >
                                <th scope="row" style={{ padding: '0.75rem 1rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                                  {name}
                                </th>
                                <td style={{ padding: '0.75rem 1rem', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                  {refVal !== null && refVal !== undefined ? `${(refVal * 100).toFixed(2)}%` : 'N/A'}
                                </td>
                                <td style={{ padding: '0.75rem 1rem', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                  {shiftedVal !== null && shiftedVal !== undefined ? `${(shiftedVal * 100).toFixed(2)}%` : 'N/A'}
                                </td>
                                <td style={{ padding: '0.75rem 1rem', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                  <span
                                    data-testid={`delta-${key}`}
                                    style={{
                                      fontWeight: 700,
                                      color: deltaInfo.isDegraded
                                        ? 'var(--color-critical, #f43f5e)'
                                        : 'var(--color-healthy, #10b981)',
                                    }}
                                  >
                                    {deltaInfo.formatted}
                                  </span>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>

                    {/* Degradation Context Disclaimer (Part D) */}
                    <div
                      style={{
                        padding: '0.75rem 1rem',
                        borderRadius: 'var(--radius-md)',
                        backgroundColor: 'var(--surface-subtle, rgba(0, 0, 0, 0.03))',
                        border: '1px solid var(--border-subtle, #334155)',
                        fontSize: '0.75rem',
                        color: 'var(--text-secondary)',
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '0.5rem',
                        lineHeight: 1.45,
                      }}
                    >
                      <Info className="icon-xs text-primary" style={{ marginTop: '0.125rem', flexShrink: 0 }} aria-hidden="true" />
                      <span>
                        <strong>Degradation Proxy Note:</strong> The shifted dataset serves as an empirical proxy for operational degradation under altered spam distributions (promotional phrasing, obfuscated keywords). Performance drops quantify empirical degradation and do not declare statistical concept drift alone.
                      </span>
                    </div>
                  </div>
                )}

                {/* Confusion Matrix Section (When at least one evaluation exists) */}
                {(referenceResult || shiftedResult) && (
                  <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    {referenceResult && shiftedResult && (
                      <div
                        role="tablist"
                        aria-label="Select Confusion Matrix Dataset"
                        style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}
                      >
                        <button
                          type="button"
                          className={`btn btn-sm ${activeConfusionDataset === 'reference' ? 'btn-primary' : 'btn-outline'}`}
                          onClick={() => setActiveConfusionDataset('reference')}
                          aria-pressed={activeConfusionDataset === 'reference'}
                          data-testid="tab-confusion-reference"
                        >
                          Reference Confusion Matrix
                        </button>
                        <button
                          type="button"
                          className={`btn btn-sm ${activeConfusionDataset === 'shifted' ? 'btn-primary' : 'btn-outline'}`}
                          onClick={() => setActiveConfusionDataset('shifted')}
                          aria-pressed={activeConfusionDataset === 'shifted'}
                          data-testid="tab-confusion-shifted"
                        >
                          Shifted Confusion Matrix
                        </button>
                      </div>
                    )}

                    <ConfusionMatrix
                      metrics={
                        activeConfusionDataset === 'shifted' && shiftedResult
                          ? shiftedResult.metrics
                          : referenceResult
                          ? referenceResult.metrics
                          : shiftedResult?.metrics
                      }
                      datasetName={
                        activeConfusionDataset === 'shifted' && shiftedResult
                          ? 'Shifted (Operational)'
                          : 'Reference (UCI Holdout)'
                      }
                    />
                  </div>
                )}
              </div>
            </div>

            <div className="section-header" style={{ marginTop: '2rem' }}>
              <h2 className="section-title">
                <History className="icon-sm text-primary" aria-hidden="true" />
                <span>Historical Observations Log</span>
              </h2>
              <span className="section-meta">
                Sorted newest first · Page {Math.floor(skip / PAGE_SIZE) + 1}
              </span>
            </div>

            <div className="table-card">
              <DataTable
                columns={columns}
                data={sortedObservations}
                keyField="id"
                emptyTitle="No Historical Observations"
                emptyDescription="No observations have been recorded for this model yet."
              />
              <div
                className="table-pagination"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.75rem 1.25rem',
                  borderTop: '1px solid var(--border-color)',
                  flexWrap: 'wrap',
                  gap: '0.75rem',
                }}
              >
                <div
                  className="pagination-info"
                  style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}
                >
                  {`Showing ${skip + 1} to ${skip + sortedObservations.length} observations · Page ${Math.floor(skip / PAGE_SIZE) + 1}`}
                </div>
                <div
                  className="pagination-actions"
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                >
                  <button
                    type="button"
                    className="btn btn-outline btn-sm"
                    disabled={skip === 0 || obsLoading}
                    onClick={handlePrevPage}
                    aria-label="Previous page"
                  >
                    <ChevronLeft className="icon-xs" aria-hidden="true" />
                    <span>Previous</span>
                  </button>
                  <button
                    type="button"
                    className="btn btn-outline btn-sm"
                    disabled={sortedObservations.length < PAGE_SIZE || obsLoading}
                    onClick={handleNextPage}
                    aria-label="Next page"
                  >
                    <span>Next</span>
                    <ChevronRight className="icon-xs" aria-hidden="true" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </section>

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

      {/* Confirmation Dialog for Triggering Real Dataset Evaluations */}
      <ConfirmationDialog
        isOpen={!!evalConfirmType}
        onClose={() => !evaluatingDataset && setEvalConfirmType(null)}
        onConfirm={handleConfirmEvaluation}
        title={
          evalConfirmType === 'reference'
            ? 'Confirm Reference Dataset Evaluation'
            : 'Confirm Shifted Dataset Evaluation'
        }
        description={
          evalConfirmType === 'reference'
            ? `Evaluate "${selectedModel?.name || 'selected model'}" against the deterministic UCI holdout test set? This will evaluate genuine performance metrics and record a monitoring observation in PhoenixML.`
            : `Evaluate "${selectedModel?.name || 'selected model'}" against the operational distribution shift dataset? This evaluates real degradation patterns and records a monitoring observation in PhoenixML.`
        }
        confirmText={
          evalConfirmType === 'reference'
            ? 'Run Reference Evaluation'
            : 'Run Shifted Evaluation'
        }
        confirmVariant="primary"
        loading={!!evaluatingDataset}
      />
    </div>
  );
}
