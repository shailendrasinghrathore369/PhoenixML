import React, { useState, useMemo } from 'react';
import {
  FlaskConical,
  Send,
  Layers,
  RotateCcw,
  Sparkles,
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  ShieldAlert,
} from 'lucide-react';
import { StatusBadge } from './StatusBadge.jsx';
import { EmptyState } from './EmptyState.jsx';
import { api } from '../lib/api.js';
import { cn } from '../lib/utils.js';

export const PLAYGROUND_PRESETS = [
  {
    id: 'phishing',
    name: 'Spam phishing message',
    badge: 'Phishing',
    text: 'URGENT! Your online bank access is temporarily locked due to unauthorized attempts. Verify your credentials at https://auth-secure-verify.net/login immediately to restore service.',
  },
  {
    id: 'ham',
    name: 'Typical ham conversation',
    badge: 'Ham',
    text: 'Hey Sam, are we still meeting up for coffee around 3:30 today? Let me know if you need me to grab anything from the office.',
  },
  {
    id: 'marketing',
    name: 'Marketing offer',
    badge: 'Marketing',
    text: 'Exclusive offer: Claim your complimentary $500 gift voucher today! Reply CLAIM to 68820 within 24 hours to secure your entry. Terms and conditions apply.',
  },
  {
    id: 'alert',
    name: 'Urgent account alert',
    badge: 'Account Alert',
    text: 'SECURITY ALERT: Your one-time verification passcode is 739201. Never disclose this PIN to anyone. If you did not initiate this request, call fraud support now.',
  },
];

/**
 * Format API errors into human-readable messages.
 * Maps 401, 403, 404, 422, and network failures.
 */
export function formatInferenceError(err) {
  if (!err) return 'Inference request failed. Please check network and server status.';
  if (err.status === 401) {
    return 'Authentication session expired (401). Please sign in again.';
  }
  if (err.status === 403) {
    return 'Forbidden (403): You do not have permission to run inference on this model.';
  }
  if (err.status === 404) {
    return 'Model not found (404): The specified model artifact is unavailable.';
  }
  if (err.status === 422) {
    return 'Validation error (422): Inference payload was rejected by the server.';
  }
  if (
    err.name === 'TypeError' ||
    err.message?.toLowerCase().includes('failed to fetch') ||
    err.message?.toLowerCase().includes('network')
  ) {
    return 'Network error: Unable to reach the inference endpoint. Verify server connection.';
  }
  return err.message || 'Inference execution failed.';
}

/**
 * Interactive Prediction Playground Component
 */
export function PredictionPlayground({
  models = [],
  selectedModelId = null,
  onSelectModelId = () => {},
  onNavigateToInventory = () => {},
  toast = null,
}) {
  const [mode, setMode] = useState('single'); // 'single' | 'batch'
  const [singleText, setSingleText] = useState('');
  const [batchText, setBatchText] = useState('');
  const [singleResult, setSingleResult] = useState(null);
  const [batchResult, setBatchResult] = useState(null);
  const [isPredicting, setIsPredicting] = useState(false);
  const [predictError, setPredictError] = useState(null);
  const [validationError, setValidationError] = useState(null);

  // Filter eligible models:
  // Must be real models from inventory.
  // Default to model selected from inventory row, otherwise first ACTIVE model.
  const activeModels = useMemo(() => {
    return models.filter((m) => m.status === 'ACTIVE');
  }, [models]);

  const eligibleModels = useMemo(() => {
    if (selectedModelId) {
      const selected = models.find((m) => m.id === selectedModelId);
      if (selected && !activeModels.some((m) => m.id === selected.id)) {
        return [selected, ...activeModels];
      }
    }
    return activeModels;
  }, [models, activeModels, selectedModelId]);

  const currentModel = useMemo(() => {
    if (selectedModelId) {
      const found = eligibleModels.find((m) => m.id === selectedModelId);
      if (found) return found;
    }
    return activeModels[0] || eligibleModels[0] || null;
  }, [eligibleModels, activeModels, selectedModelId]);

  // Handle switching model
  const handleModelChange = (modelId) => {
    onSelectModelId(modelId);
    setPredictError(null);
    setValidationError(null);
  };

  // Preset population (does NOT auto-execute)
  const handleApplyPreset = (preset) => {
    setValidationError(null);
    if (mode === 'single') {
      setSingleText(preset.text);
    } else {
      setBatchText((prev) => (prev.trim() ? `${prev.trim()}\n${preset.text}` : preset.text));
    }
  };

  // Single SMS Prediction submission
  const handleSingleSubmit = async (e) => {
    e.preventDefault();
    if (!currentModel) return;

    const trimmed = singleText.trim();
    if (!trimmed) {
      setValidationError('SMS message text cannot be empty.');
      return;
    }
    if (trimmed.length > 5000) {
      setValidationError('SMS text exceeds maximum length of 5000 characters.');
      return;
    }

    setValidationError(null);
    setPredictError(null);
    setIsPredicting(true);

    try {
      const res = await api.predict(currentModel.id, { text: trimmed });
      const prediction = res?.predictions?.[0] || null;
      if (prediction) {
        setSingleResult(prediction);
        toast?.success?.(
          `Classified as ${prediction.predicted_label.toUpperCase()} (${(prediction.confidence * 100).toFixed(1)}% confidence)`
        );
      }
    } catch (err) {
      const msg = formatInferenceError(err);
      setPredictError(msg);
      toast?.error?.(`Inference failed: ${msg}`);
      // Previous singleResult is preserved
    } finally {
      setIsPredicting(false);
    }
  };

  // Batch SMS Prediction submission
  const handleBatchSubmit = async (e) => {
    e.preventDefault();
    if (!currentModel) return;

    const lines = batchText
      .split('\n')
      .map((l) => l.trim())
      .filter((l) => l.length > 0);

    if (lines.length === 0) {
      setValidationError('Please enter at least one valid SMS message line.');
      return;
    }

    const overLimit = lines.find((l) => l.length > 5000);
    if (overLimit) {
      setValidationError('One or more SMS lines exceed the maximum 5000 character limit.');
      return;
    }

    setValidationError(null);
    setPredictError(null);
    setIsPredicting(true);

    try {
      const res = await api.predict(currentModel.id, { texts: lines });
      if (res) {
        setBatchResult(res);
        toast?.success?.(
          `Batch classified: ${res.total_predictions} messages (${res.spam_count} spam, ${res.ham_count} ham)`
        );
      }
    } catch (err) {
      const msg = formatInferenceError(err);
      setPredictError(msg);
      toast?.error?.(`Batch inference failed: ${msg}`);
      // Previous batchResult is preserved
    } finally {
      setIsPredicting(false);
    }
  };

  // Empty state when no eligible active models exist
  if (eligibleModels.length === 0 || !currentModel) {
    return (
      <div className="playground-tab-view">
        <EmptyState
          title="No Active Models Available"
          description="The Prediction Playground requires at least one ACTIVE spam detection model. Activate an existing candidate model or register a new production model to begin interactive testing."
          action={
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={onNavigateToInventory}
              aria-label="Return to Model Inventory"
            >
              <ArrowLeft className="icon-xs" aria-hidden="true" />
              <span>Return to Model Inventory</span>
            </button>
          }
        />
      </div>
    );
  }

  const batchLinesCount = batchText
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l.length > 0).length;

  return (
    <div className="playground-tab-view">
      {/* Target Model Selection Banner */}
      <div className="playground-model-banner">
        <div className="playground-model-info">
          <span className="playground-kicker">Target Testing Model</span>
          <h3 className="playground-model-title">{currentModel.name}</h3>
          <div className="playground-model-meta">
            <span>Framework: {currentModel.framework}</span>
            <span>·</span>
            <span>Algorithm: {currentModel.algorithm || 'Standard Pipeline'}</span>
            <span>·</span>
            <StatusBadge
              variant={currentModel.status === 'ACTIVE' ? 'healthy' : 'info'}
              size="sm"
            >
              {currentModel.status}
            </StatusBadge>
          </div>
        </div>

        <div className="playground-banner-actions">
          <div className="form-group mb-0">
            <select
              className="form-input"
              value={currentModel.id}
              onChange={(e) => handleModelChange(e.target.value)}
              aria-label="Select model for prediction playground"
              disabled={isPredicting}
            >
              {eligibleModels.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.framework} · {m.status})
                </option>
              ))}
            </select>
          </div>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={onNavigateToInventory}
            disabled={isPredicting}
          >
            <ArrowLeft className="icon-xs" aria-hidden="true" />
            <span>Back to Inventory</span>
          </button>
        </div>
      </div>

      {/* Mode Navigation & Preset Library Toolbar */}
      <div className="playground-toolbar-card">
        <div className="playground-toolbar-header-row">
          <div>
            <h4 className="stage-card-title">Prediction Playground Console</h4>
            <p className="playground-toolbar-hint">
              Interactive real-time spam classification, calibrated probabilities, and batch SMS inference.
            </p>
          </div>
        </div>

        <div className="playground-toolbar-top">
          <div className="mode-tabs-group" role="tablist" aria-label="Prediction Input Mode">
            <button
              type="button"
              role="tab"
              aria-selected={mode === 'single'}
              className={cn('mode-tab-btn', mode === 'single' && 'active')}
              onClick={() => {
                setMode('single');
                setValidationError(null);
                setPredictError(null);
              }}
              disabled={isPredicting}
            >
              <Send className="icon-xs" aria-hidden="true" />
              <span>Single SMS</span>
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={mode === 'batch'}
              className={cn('mode-tab-btn', mode === 'batch' && 'active')}
              onClick={() => {
                setMode('batch');
                setValidationError(null);
                setPredictError(null);
              }}
              disabled={isPredicting}
            >
              <Layers className="icon-xs" aria-hidden="true" />
              <span>Batch SMS</span>
            </button>
          </div>

          <span className="playground-toolbar-hint">
            Select a preset to populate input without auto-running inference
          </span>
        </div>

        {/* Preset Library Buttons */}
        <div className="preset-library-bar">
          <span className="preset-label">
            <Sparkles className="icon-xs text-primary" aria-hidden="true" />
            <span>Example Presets:</span>
          </span>
          <div className="preset-chips-wrap">
            {PLAYGROUND_PRESETS.map((preset) => (
              <button
                key={preset.id}
                type="button"
                className="preset-chip-btn"
                onClick={() => handleApplyPreset(preset)}
                disabled={isPredicting}
                title={`Click to load "${preset.name}" into ${mode} input`}
              >
                <span>{preset.name}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error Alert Display */}
      {predictError && (
        <div className="alert alert-error" role="alert">
          <AlertCircle className="icon-sm" aria-hidden="true" />
          <div className="alert-content">
            <strong>Inference Request Failed</strong>
            <p>{predictError}</p>
          </div>
        </div>
      )}

      {/* Mode View 1: Single SMS Prediction */}
      {mode === 'single' && (
        <div className="playground-grid">
          {/* Input Panel */}
          <div className="playground-card">
            <div className="playground-card-header">
              <h4 className="playground-card-title">SMS Message Input</h4>
              <span className="char-counter">
                {singleText.length} / 5000 characters
              </span>
            </div>

            <form onSubmit={handleSingleSubmit}>
              <div className="form-group">
                <textarea
                  id="playground-single-input"
                  className={cn(
                    'form-input form-textarea playground-textarea',
                    validationError && 'input-error'
                  )}
                  placeholder="Enter or paste SMS text to classify (e.g. 'URGENT: Verify your account access...')"
                  value={singleText}
                  onChange={(e) => {
                    setSingleText(e.target.value);
                    setValidationError(null);
                  }}
                  disabled={isPredicting}
                  rows={5}
                  maxLength={5000}
                  aria-label="SMS text message"
                />
                {validationError && (
                  <div className="form-field-error" role="alert">
                    {validationError}
                  </div>
                )}
              </div>

              <div className="playground-actions-bar">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isPredicting || !singleText.trim()}
                >
                  {isPredicting ? (
                    <>
                      <span className="dialog-btn-spinner" aria-hidden="true" />
                      <span>Classifying SMS...</span>
                    </>
                  ) : (
                    <>
                      <Send className="icon-xs" aria-hidden="true" />
                      <span>Classify SMS</span>
                    </>
                  )}
                </button>

                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => {
                    setSingleText('');
                    setValidationError(null);
                  }}
                  disabled={isPredicting || !singleText}
                >
                  <RotateCcw className="icon-xs" aria-hidden="true" />
                  <span>Clear Input</span>
                </button>
              </div>
            </form>
          </div>

          {/* Results Panel */}
          <div className="playground-card">
            <div className="playground-card-header">
              <h4 className="playground-card-title">Model Classification Output</h4>
              {singleResult && (
                <StatusBadge
                  variant={singleResult.is_spam ? 'critical' : 'healthy'}
                  size="sm"
                >
                  {singleResult.predicted_label.toUpperCase()}
                </StatusBadge>
              )}
            </div>

            {singleResult ? (
              <div className="playground-result-body">
                {/* Hero Stat Box */}
                <div
                  className={cn(
                    'result-hero-box',
                    singleResult.is_spam ? 'hero-spam' : 'hero-ham'
                  )}
                >
                  <div className="hero-badge-row">
                    <span className="hero-kicker">Predicted Label</span>
                    <StatusBadge
                      variant={singleResult.is_spam ? 'critical' : 'healthy'}
                      size="md"
                    >
                      {singleResult.predicted_label.toUpperCase()}
                    </StatusBadge>
                  </div>
                  <div className="hero-confidence-row">
                    <span className="hero-confidence-val">
                      {(singleResult.confidence * 100).toFixed(1)}%
                    </span>
                    <span className="hero-confidence-sub">Confidence Score</span>
                  </div>
                </div>

                {/* Accessible Confidence Meter */}
                <div className="meter-block">
                  <div className="meter-header">
                    <span className="meter-label">Model Confidence</span>
                    <span className="meter-num">
                      {(singleResult.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div
                    className="confidence-track"
                    role="progressbar"
                    aria-valuenow={Math.round(singleResult.confidence * 100)}
                    aria-valuemin="0"
                    aria-valuemax="100"
                    aria-label="Model Confidence Meter"
                  >
                    <div
                      className={cn(
                        'confidence-fill',
                        singleResult.is_spam ? 'critical' : 'healthy'
                      )}
                      style={{
                        width: `${Math.min(100, Math.max(0, singleResult.confidence * 100))}%`,
                      }}
                    />
                  </div>
                </div>

                {/* Class Probabilities Visualization */}
                <div className="prob-breakdown-card">
                  <span className="prob-card-title">Class Probabilities</span>
                  <div className="prob-grid">
                    <div className="prob-item">
                      <div className="prob-item-header">
                        <span className="prob-name text-critical">Spam Probability</span>
                        <span className="prob-pct">
                          {(singleResult.spam_probability * 100).toFixed(2)}%
                        </span>
                      </div>
                      <div
                        className="prob-track"
                        role="progressbar"
                        aria-valuenow={Math.round(singleResult.spam_probability * 100)}
                        aria-valuemin="0"
                        aria-valuemax="100"
                        aria-label="Spam Probability"
                      >
                        <div
                          className="prob-fill critical"
                          style={{
                            width: `${Math.min(100, Math.max(0, singleResult.spam_probability * 100))}%`,
                          }}
                        />
                      </div>
                    </div>

                    <div className="prob-item">
                      <div className="prob-item-header">
                        <span className="prob-name text-healthy">Ham Probability</span>
                        <span className="prob-pct">
                          {(singleResult.ham_probability * 100).toFixed(2)}%
                        </span>
                      </div>
                      <div
                        className="prob-track"
                        role="progressbar"
                        aria-valuenow={Math.round(singleResult.ham_probability * 100)}
                        aria-valuemin="0"
                        aria-valuemax="100"
                        aria-label="Ham Probability"
                      >
                        <div
                          className="prob-fill healthy"
                          style={{
                            width: `${Math.min(100, Math.max(0, singleResult.ham_probability * 100))}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Advisory Disclaimer */}
                <div className="playground-disclaimer">
                  <AlertCircle className="icon-xs text-muted" aria-hidden="true" />
                  <span>
                    Statistical Notice: Predictions represent machine learning probabilistic estimates generated by {singleResult.model_name || currentModel.name} and are not guaranteed truth.
                  </span>
                </div>
              </div>
            ) : (
              <div className="playground-awaiting-state">
                <FlaskConical className="icon-lg text-muted mb-2" aria-hidden="true" />
                <p className="awaiting-title">Awaiting Prediction Request</p>
                <p className="awaiting-desc">
                  Type an SMS text message or apply one of the example presets above, then click <strong>Classify SMS</strong> to view live classification probabilities.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Mode View 2: Batch SMS Prediction */}
      {mode === 'batch' && (
        <div className="playground-batch-view">
          {/* Input Panel */}
          <div className="playground-card">
            <div className="playground-card-header">
              <div>
                <h4 className="playground-card-title">Batch SMS Input</h4>
                <p className="playground-card-sub">
                  Enter multiple SMS messages, one individual message per line.
                </p>
              </div>
              <span className="char-counter">
                {batchLinesCount} {batchLinesCount === 1 ? 'message' : 'messages'} detected
              </span>
            </div>

            <form onSubmit={handleBatchSubmit}>
              <div className="form-group">
                <textarea
                  id="playground-batch-input"
                  className={cn(
                    'form-input form-textarea playground-textarea',
                    validationError && 'input-error'
                  )}
                  placeholder={`Free entry into our £1000 prize draw. Text PLAY to 80122\nHey man, are you free for lunch tomorrow?\nURGENT: Your account requires immediate verification.`}
                  value={batchText}
                  onChange={(e) => {
                    setBatchText(e.target.value);
                    setValidationError(null);
                  }}
                  disabled={isPredicting}
                  rows={6}
                  aria-label="Batch SMS text messages (one per line)"
                />
                {validationError && (
                  <div className="form-field-error" role="alert">
                    {validationError}
                  </div>
                )}
              </div>

              <div className="playground-actions-bar">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isPredicting || batchLinesCount === 0}
                >
                  {isPredicting ? (
                    <>
                      <span className="dialog-btn-spinner" aria-hidden="true" />
                      <span>Classifying Batch ({batchLinesCount})...</span>
                    </>
                  ) : (
                    <>
                      <Layers className="icon-xs" aria-hidden="true" />
                      <span>Classify Batch ({batchLinesCount})</span>
                    </>
                  )}
                </button>

                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => {
                    setBatchText('');
                    setValidationError(null);
                  }}
                  disabled={isPredicting || !batchText}
                >
                  <RotateCcw className="icon-xs" aria-hidden="true" />
                  <span>Clear Input</span>
                </button>
              </div>
            </form>
          </div>

          {/* Batch Results Output */}
          {batchResult && (
            <div className="playground-card">
              <div className="playground-card-header">
                <div>
                  <h4 className="playground-card-title">Batch Prediction Results</h4>
                  <p className="playground-card-sub">
                    Evaluated by {batchResult.model_name} ({batchResult.model_version})
                  </p>
                </div>
                <div className="batch-header-counts">
                  <StatusBadge variant="critical" size="sm">
                    {batchResult.spam_count} Spam
                  </StatusBadge>
                  <StatusBadge variant="healthy" size="sm">
                    {batchResult.ham_count} Ham
                  </StatusBadge>
                </div>
              </div>

              {/* Batch KPI Cards */}
              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="kpi-header">
                    <span className="kpi-title">Total Predictions</span>
                  </div>
                  <div className="kpi-value">{batchResult.total_predictions}</div>
                  <div className="kpi-subtext">Evaluated SMS messages</div>
                </div>

                <div className="kpi-card">
                  <div className="kpi-header">
                    <span className="kpi-title">Spam Detected</span>
                  </div>
                  <div className="kpi-value text-critical">{batchResult.spam_count}</div>
                  <div className="kpi-subtext">
                    {batchResult.total_predictions > 0
                      ? `${((batchResult.spam_count / batchResult.total_predictions) * 100).toFixed(1)}% of batch`
                      : '0%'}
                  </div>
                </div>

                <div className="kpi-card">
                  <div className="kpi-header">
                    <span className="kpi-title">Ham Verified</span>
                  </div>
                  <div className="kpi-value text-healthy">{batchResult.ham_count}</div>
                  <div className="kpi-subtext">
                    {batchResult.total_predictions > 0
                      ? `${((batchResult.ham_count / batchResult.total_predictions) * 100).toFixed(1)}% of batch`
                      : '0%'}
                  </div>
                </div>

                <div className="kpi-card">
                  <div className="kpi-header">
                    <span className="kpi-title">Batch Status</span>
                  </div>
                  <div className="kpi-value">
                    {batchResult.spam_count > 0 ? 'Threats Found' : 'Clean'}
                  </div>
                  <div className="kpi-subtext">
                    {batchResult.spam_count > 0 ? 'High probability spam present' : 'All messages classified as ham'}
                  </div>
                </div>
              </div>

              {/* Individual Classifications Table */}
              <div className="table-container mt-4">
                <table className="data-table" aria-label="Batch Classification Results">
                  <thead>
                    <tr>
                      <th scope="col" style={{ width: '40px' }}>#</th>
                      <th scope="col">Message Content</th>
                      <th scope="col">Predicted Label</th>
                      <th scope="col">Confidence</th>
                      <th scope="col">Spam Prob</th>
                      <th scope="col">Ham Prob</th>
                    </tr>
                  </thead>
                  <tbody>
                    {batchResult.predictions?.map((pred, idx) => (
                      <tr key={idx}>
                        <td className="text-muted font-mono">{idx + 1}</td>
                        <td className="batch-text-cell" title={pred.text}>
                          <span className="batch-text-preview">{pred.text}</span>
                        </td>
                        <td>
                          <StatusBadge
                            variant={pred.is_spam ? 'critical' : 'healthy'}
                            size="sm"
                          >
                            {pred.predicted_label.toUpperCase()}
                          </StatusBadge>
                        </td>
                        <td className="font-mono">
                          {(pred.confidence * 100).toFixed(1)}%
                        </td>
                        <td className="font-mono text-critical">
                          {(pred.spam_probability * 100).toFixed(1)}%
                        </td>
                        <td className="font-mono text-healthy">
                          {(pred.ham_probability * 100).toFixed(1)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Advisory Disclaimer */}
              <div className="playground-disclaimer mt-4">
                <AlertCircle className="icon-xs text-muted" aria-hidden="true" />
                <span>
                  Statistical Notice: Predictions represent machine learning probabilistic estimates generated by {batchResult.model_name} and are not guaranteed truth.
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
