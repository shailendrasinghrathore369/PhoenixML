import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { api } from '../lib/api.js';
import { isViewer } from '../lib/utils.js';

export function useDashboard(user, onNotify) {
  const [dashboardData, setDashboardData] = useState(null);
  const [selectedModelId, setSelectedModelId] = useState('');
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const [evalResults, setEvalResults] = useState({});

  const notifyRef = useRef(onNotify);
  useEffect(() => {
    notifyRef.current = onNotify;
  }, [onNotify]);

  const selectedModelIdRef = useRef(selectedModelId);
  useEffect(() => {
    selectedModelIdRef.current = selectedModelId;
  }, [selectedModelId]);

  // Fetch consolidated dashboard data with stable callback reference
  const loadDashboard = useCallback(async (modelId) => {
    const targetId = modelId !== undefined ? modelId : selectedModelIdRef.current;
    setLoading(true);
    try {
      const data = await api.getDashboardOverview(targetId || null);
      setDashboardData(data);
      return data;
    } catch (err) {
      if (notifyRef.current) {
        notifyRef.current.error?.(`Failed to load dashboard: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load when user is authenticated, or when model filter selection changes
  useEffect(() => {
    if (user) {
      loadDashboard(selectedModelId);
    }
  }, [user, selectedModelId, loadDashboard]);

  // Map model ID to model card for O(1) lookups
  const modelMap = useMemo(() => {
    const map = {};
    if (dashboardData?.model_cards) {
      dashboardData.model_cards.forEach((c) => {
        map[c.model_id] = c;
      });
    }
    return map;
  }, [dashboardData]);

  // Locate the most urgent pending decision to highlight for mandatory human review
  const pendingDecision = useMemo(() => {
    if (!dashboardData) return null;
    // Check if selected model has a pending decision
    if (selectedModelId && modelMap[selectedModelId]?.latest_decision?.approval_status === 'PENDING') {
      return modelMap[selectedModelId].latest_decision;
    }
    // Otherwise, find the first pending decision in recent_decisions
    if (dashboardData.decision_summary?.recent_decisions) {
      const pending = dashboardData.decision_summary.recent_decisions.find(
        (d) => d.approval_status === 'PENDING'
      );
      if (pending) return pending;
    }
    // Fallback to selected model's latest decision
    if (selectedModelId && modelMap[selectedModelId]?.latest_decision) {
      return modelMap[selectedModelId].latest_decision;
    }
    return null;
  }, [dashboardData, selectedModelId, modelMap]);

  // Trigger AIMD model evaluation across monitoring observations
  const handleEvaluate = async (modelId) => {
    if (isViewer(user?.role)) {
      onNotify?.error?.('Viewers have read-only permissions and cannot trigger model evaluations.');
      return;
    }
    const targetModel = modelMap[modelId];
    if (targetModel && (!targetModel.observation_count || targetModel.observation_count === 0)) {
      onNotify?.error?.(
        'Cannot trigger AIMD evaluation: model has zero monitoring observations. Run Real Evaluation first to record telemetry.'
      );
      return;
    }
    setActionLoading(`evaluating-${modelId}`);
    try {
      const res = await api.evaluateModel(modelId);
      onNotify?.success?.(
        `Evaluation triggered successfully! AIMD Recommendation: ${res.recommended_action} (Priority: ${res.priority}).`
      );
      await loadDashboard(selectedModelId);
    } catch (err) {
      onNotify?.error?.(`Evaluation failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Run real reference or shifted model evaluation against genuine dataset
  const handleRealEvaluate = async (modelId, datasetName = 'reference') => {
    if (isViewer(user?.role)) {
      onNotify?.error?.('Viewers have read-only permissions and cannot run real model evaluations.');
      return;
    }
    const isShifted = datasetName === 'shifted';
    setActionLoading(isShifted ? `shifted-eval-${modelId}` : `ref-eval-${modelId}`);
    try {
      const res = await api.evaluateModelTelemetry(modelId, {
        dataset_name: datasetName,
        use_reference_test_set: !isShifted,
        record_monitoring_observation: true,
      });
      setEvalResults((prev) => ({
        ...prev,
        [modelId]: {
          ...res,
          datasetName,
        },
      }));
      const metrics = res.metrics || {};
      const accStr = metrics.accuracy !== undefined ? (metrics.accuracy * 100).toFixed(2) + '%' : 'N/A';
      const f1Str = metrics.f1_score !== undefined ? (metrics.f1_score * 100).toFixed(2) + '%' : 'N/A';
      const precStr = metrics.precision !== undefined ? (metrics.precision * 100).toFixed(2) + '%' : 'N/A';
      const recStr = metrics.recall !== undefined ? (metrics.recall * 100).toFixed(2) + '%' : 'N/A';
      const countStr = metrics.prediction_count || (isShifted ? 2017 : 1115);
      const label = isShifted ? 'Shifted operational dataset' : 'Reference test set';

      if (isShifted) {
        onNotify?.warning?.(
          `${label} evaluation completed on ${countStr} samples! Accuracy: ${accStr} | F1: ${f1Str} | Precision: ${precStr} | Recall: ${recStr}. Monitoring observation recorded successfully.`
        );
      } else {
        onNotify?.success?.(
          `${label} evaluation completed on ${countStr} samples! Accuracy: ${accStr} | F1: ${f1Str} | Precision: ${precStr} | Recall: ${recStr}. Monitoring observation recorded successfully.`
        );
      }
      await loadDashboard(selectedModelId);
    } catch (err) {
      onNotify?.error?.(`Evaluation failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Human Operator: Approve AIMD recommendation
  const handleApprove = async (decision) => {
    if (isViewer(user?.role)) {
      onNotify?.error?.('Viewers have read-only permissions and cannot approve recommendations.');
      return;
    }
    setActionLoading(`approval-${decision.id}`);
    try {
      await api.updateApprovalStatus(decision.model_id, decision.id, 'APPROVED');
      onNotify?.success?.(
        `Recommendation "${decision.recommended_action}" successfully APPROVED by operator.`
      );
      await loadDashboard(selectedModelId);
    } catch (err) {
      onNotify?.error?.(`Approval failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Human Operator: Reject AIMD recommendation
  const handleReject = async (decision) => {
    if (isViewer(user?.role)) {
      onNotify?.error?.('Viewers have read-only permissions and cannot reject recommendations.');
      return;
    }
    setActionLoading(`approval-${decision.id}`);
    try {
      await api.updateApprovalStatus(decision.model_id, decision.id, 'REJECTED');
      onNotify?.success?.(
        `Recommendation "${decision.recommended_action}" successfully REJECTED by operator.`
      );
      await loadDashboard(selectedModelId);
    } catch (err) {
      onNotify?.error?.(`Rejection failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  return {
    dashboardData,
    selectedModelId,
    setSelectedModelId,
    loading,
    actionLoading,
    evalResults,
    modelMap,
    pendingDecision,
    loadDashboard,
    handleEvaluate,
    handleRealEvaluate,
    handleApprove,
    handleReject,
  };
}
