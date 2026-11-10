import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { ConfusionMatrix } from '../components/ConfusionMatrix.jsx';
import { TelemetryPage } from '../pages/TelemetryPage.jsx';
import { ThemeProvider } from '../context/ThemeContext.jsx';
import { api } from '../lib/api.js';

describe('ConfusionMatrix Component', () => {
  const sampleMetrics = {
    accuracy: 0.9901,
    precision: 0.9600,
    recall: 0.9664,
    f1_score: 0.9632,
    prediction_count: 1115,
    true_positives: 144,
    false_positives: 6,
    true_negatives: 959,
    false_negatives: 6,
  };

  it('renders exact backend counts for TP, FP, TN, FN with proper accessibility semantics', () => {
    render(
      <ConfusionMatrix
        metrics={sampleMetrics}
        datasetName="Reference (UCI Holdout)"
      />
    );

    expect(screen.getByTestId('confusion-matrix-card')).toBeInTheDocument();
    expect(screen.getByTestId('confusion-matrix-table')).toBeInTheDocument();
    expect(screen.getByText('Reference (UCI Holdout) Dataset')).toBeInTheDocument();

    // Headers & Class Labels
    expect(screen.getByText('Actual \\ Predicted')).toBeInTheDocument();
    expect(screen.getByText('Predicted Class')).toBeInTheDocument();
    expect(screen.getByText('Predicted Positive (Spam)')).toBeInTheDocument();
    expect(screen.getByText('Predicted Negative (Ham)')).toBeInTheDocument();
    expect(screen.getByText('Actual Positive (Spam)')).toBeInTheDocument();
    expect(screen.getByText('Actual Negative (Ham)')).toBeInTheDocument();

    // Exact integer counts
    expect(screen.getByTestId('count-true-positives')).toHaveTextContent('144');
    expect(screen.getByTestId('count-false-positives')).toHaveTextContent('6');
    expect(screen.getByTestId('count-true-negatives')).toHaveTextContent('959');
    expect(screen.getByTestId('count-false-negatives')).toHaveTextContent('6');

    // Total evaluated summary
    expect(screen.getByText(/total evaluated samples:/i)).toHaveTextContent('1,115');
  });

  it('renders explicit zero counts correctly and displays N/A for null or missing values', () => {
    const zeroMetrics = {
      true_positives: 0,
      false_positives: 0,
      true_negatives: 100,
      false_negatives: null, // missing/null
    };

    render(<ConfusionMatrix metrics={zeroMetrics} datasetName="Sparse Test" />);

    // Explicit zeros must be '0', not 'N/A'
    expect(screen.getByTestId('count-true-positives')).toHaveTextContent('0');
    expect(screen.getByTestId('count-false-positives')).toHaveTextContent('0');
    expect(screen.getByTestId('count-true-negatives')).toHaveTextContent('100');

    // Null/missing must be 'N/A'
    expect(screen.getByTestId('count-false-negatives')).toHaveTextContent('N/A');
  });
});

describe('TelemetryPage Dataset Evaluation & Degradation Comparator', () => {
  const sampleModels = [
    {
      id: 'model-eval-1',
      name: 'SpamModel-LogisticRegression',
      framework: 'scikit-learn',
      algorithm: 'LogisticRegression',
      status: 'ACTIVE',
    },
    {
      id: 'model-eval-2',
      name: 'CandidateModel-NaiveBayes',
      framework: 'scikit-learn',
      algorithm: 'MultinomialNB',
      status: 'DEVELOPMENT',
    },
  ];

  const sampleObservations = [
    {
      id: 'obs-init-1',
      model_id: 'model-eval-1',
      observed_at: '2026-11-10T10:00:00Z',
      prediction_count: 50,
      accuracy: 0.95,
      precision: 0.92,
      recall: 0.90,
      f1_score: 0.91,
    },
  ];

  const mockRefEvaluationResponse = {
    model_id: 'model-eval-1',
    model_name: 'SpamModel-LogisticRegression',
    model_version: '1.0.0',
    evaluated_at: '2026-11-10T12:00:00Z',
    observation_id: 'obs-ref-new',
    observation_recorded: true,
    metrics: {
      accuracy: 0.9901,
      precision: 0.9600,
      recall: 0.9664,
      f1_score: 0.9632,
      prediction_count: 1115,
      positive_prediction_count: 150,
      negative_prediction_count: 965,
      true_positives: 144,
      false_positives: 6,
      true_negatives: 959,
      false_negatives: 6,
    },
  };

  const mockShiftedEvaluationResponse = {
    model_id: 'model-eval-1',
    model_name: 'SpamModel-LogisticRegression',
    model_version: '1.0.0',
    evaluated_at: '2026-11-10T12:05:00Z',
    observation_id: 'obs-shift-new',
    observation_recorded: true,
    metrics: {
      accuracy: 0.7754,
      precision: 0.9101,
      recall: 0.4266,
      f1_score: 0.5809,
      prediction_count: 2017,
      positive_prediction_count: 320,
      negative_prediction_count: 1697,
      true_positives: 290,
      false_positives: 30,
      true_negatives: 1274,
      false_negatives: 423,
    },
  };

  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(api, 'listModels').mockResolvedValue(sampleModels);
    vi.spyOn(api, 'listObservations').mockResolvedValue(sampleObservations);
  });

  it('renders evaluation trigger buttons and initial explanatory empty state', async () => {
    render(
      <ThemeProvider>
        <TelemetryPage user={{ role: 'ADMIN' }} selectedModelId="model-eval-1" />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('section-dataset-comparator')).toBeInTheDocument();
      expect(screen.getByTestId('btn-run-reference-eval')).toBeInTheDocument();
      expect(screen.getByTestId('btn-run-shifted-eval')).toBeInTheDocument();
      expect(screen.getByTestId('comparison-empty-state')).toBeInTheDocument();
      expect(screen.getByText(/no active evaluations recorded in this session/i)).toBeInTheDocument();
    });
  });

  it('requires user confirmation before triggering reference evaluation and calls API with reference payload', async () => {
    const evalSpy = vi.spyOn(api, 'evaluateModelTelemetry').mockResolvedValue(mockRefEvaluationResponse);
    const listObsSpy = vi.spyOn(api, 'listObservations').mockResolvedValue(sampleObservations);

    render(
      <ThemeProvider>
        <TelemetryPage user={{ role: 'ADMIN' }} selectedModelId="model-eval-1" />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('btn-run-reference-eval')).toBeInTheDocument();
    });

    // Click Run Reference Evaluation -> Opens ConfirmationDialog
    fireEvent.click(screen.getByTestId('btn-run-reference-eval'));

    // Confirmation dialog appears
    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeInTheDocument();
    expect(screen.getByText('Confirm Reference Dataset Evaluation')).toBeInTheDocument();
    expect(screen.getByText(/deterministic UCI holdout test set/i)).toBeInTheDocument();

    // Confirm execution
    const confirmBtn = within(dialog).getByRole('button', { name: 'Run Reference Evaluation' });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(evalSpy).toHaveBeenCalledWith('model-eval-1', {
        use_reference_test_set: true,
        record_monitoring_observation: true,
        dataset_name: 'reference',
      });
      // Observations refreshed after evaluation
      expect(listObsSpy).toHaveBeenCalled();
    });

    // After reference evaluation: prompt says comparison requires both results
    await waitFor(() => {
      expect(screen.getByTestId('comparison-requires-both')).toBeInTheDocument();
      expect(screen.getByText(/comparison requires both results/i)).toBeInTheDocument();
      // Confusion matrix for Reference appears
      expect(screen.getByTestId('confusion-matrix-card')).toBeInTheDocument();
      expect(screen.getByTestId('count-true-positives')).toHaveTextContent('144');
    });
  });

  it('canceling confirmation dialog does not execute API call', async () => {
    const evalSpy = vi.spyOn(api, 'evaluateModelTelemetry');

    render(
      <ThemeProvider>
        <TelemetryPage user={{ role: 'ADMIN' }} selectedModelId="model-eval-1" />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('btn-run-reference-eval')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('btn-run-reference-eval'));
    expect(screen.getByRole('dialog')).toBeInTheDocument();

    // Click Cancel
    const cancelBtn = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelBtn);

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(evalSpy).not.toHaveBeenCalled();
  });

  it('prevents duplicate submissions while evaluation request is running', async () => {
    let resolveEvaluation;
    const pendingPromise = new Promise((resolve) => {
      resolveEvaluation = resolve;
    });

    vi.spyOn(api, 'evaluateModelTelemetry').mockReturnValue(pendingPromise);

    render(
      <ThemeProvider>
        <TelemetryPage user={{ role: 'ADMIN' }} selectedModelId="model-eval-1" />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('btn-run-reference-eval')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('btn-run-reference-eval'));
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Run Reference Evaluation' }));

    // Buttons should now be disabled while evaluation is running
    await waitFor(() => {
      expect(screen.getByTestId('btn-run-reference-eval')).toBeDisabled();
      expect(screen.getByTestId('btn-run-shifted-eval')).toBeDisabled();
    });

    // Resolve evaluation
    resolveEvaluation(mockRefEvaluationResponse);

    await waitFor(() => {
      expect(screen.getByTestId('btn-run-reference-eval')).not.toBeDisabled();
      expect(screen.getByTestId('btn-run-shifted-eval')).not.toBeDisabled();
    });
  });

  it('runs shifted evaluation and compares both datasets with exact percentage-point (pp) degradation deltas', async () => {
    vi.spyOn(api, 'evaluateModelTelemetry')
      .mockResolvedValueOnce(mockRefEvaluationResponse)
      .mockResolvedValueOnce(mockShiftedEvaluationResponse);

    render(
      <ThemeProvider>
        <TelemetryPage user={{ role: 'ADMIN' }} selectedModelId="model-eval-1" />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('btn-run-reference-eval')).toBeInTheDocument();
    });

    // 1. Run Reference
    fireEvent.click(screen.getByTestId('btn-run-reference-eval'));
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Run Reference Evaluation' }));

    await waitFor(() => {
      expect(screen.getByTestId('comparison-requires-both')).toBeInTheDocument();
    });

    // 2. Run Shifted
    fireEvent.click(screen.getByTestId('btn-run-shifted-eval'));
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Run Shifted Evaluation' }));

    // 3. Both are evaluated -> Full Comparison Table renders
    await waitFor(() => {
      expect(screen.getByTestId('dataset-comparison-table')).toBeInTheDocument();
    });

    // Verification of exact values & degradation deltas in percentage points (pp)
    // Accuracy: Ref 99.01%, Shifted 77.54%, Delta: -21.47 pp
    const accRow = screen.getByTestId('comparison-row-accuracy');
    expect(accRow).toHaveTextContent('99.01%');
    expect(accRow).toHaveTextContent('77.54%');
    expect(within(accRow).getByTestId('delta-accuracy')).toHaveTextContent('-21.47 pp');

    // F1 Score: Ref 96.32%, Shifted 58.09%, Delta: -38.23 pp
    const f1Row = screen.getByTestId('comparison-row-f1_score');
    expect(f1Row).toHaveTextContent('96.32%');
    expect(f1Row).toHaveTextContent('58.09%');
    expect(within(f1Row).getByTestId('delta-f1_score')).toHaveTextContent('-38.23 pp');

    // Operational degradation contextual disclaimer is displayed
    expect(screen.getByText(/degradation proxy note/i)).toBeInTheDocument();
    expect(screen.getByText(/do not declare statistical concept drift alone/i)).toBeInTheDocument();

    // Toggle between Reference and Shifted Confusion Matrices
    expect(screen.getByTestId('tab-confusion-reference')).toBeInTheDocument();
    expect(screen.getByTestId('tab-confusion-shifted')).toBeInTheDocument();

    // Initially active is Shifted
    expect(screen.getByTestId('count-true-positives')).toHaveTextContent('290');

    // Switch to Reference matrix
    fireEvent.click(screen.getByTestId('tab-confusion-reference'));
    expect(screen.getByTestId('count-true-positives')).toHaveTextContent('144');
  });

  it('disables evaluation buttons for VIEWER users and handles 403 API permission denial', async () => {
    const authError = new Error('Forbidden');
    authError.status = 403;
    vi.spyOn(api, 'evaluateModelTelemetry').mockRejectedValue(authError);

    // Render as VIEWER
    const { rerender } = render(
      <ThemeProvider>
        <TelemetryPage user={{ role: 'VIEWER' }} selectedModelId="model-eval-1" />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('btn-run-reference-eval')).toBeDisabled();
      expect(screen.getByTestId('btn-run-shifted-eval')).toBeDisabled();
      expect(screen.getByText(/evaluation requires ml engineer or admin role/i)).toBeInTheDocument();
    });

    // Now render as ML_ENGINEER with an unexpected 403 from server
    rerender(
      <ThemeProvider>
        <TelemetryPage user={{ role: 'ML_ENGINEER' }} selectedModelId="model-eval-1" />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('btn-run-reference-eval')).not.toBeDisabled();
    });

    fireEvent.click(screen.getByTestId('btn-run-reference-eval'));
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Run Reference Evaluation' }));

    // Expect clear access denied error alert
    await waitFor(() => {
      expect(screen.getByTestId('eval-error-alert')).toBeInTheDocument();
      expect(screen.getByText(/only ml engineers and administrators can evaluate model telemetry/i)).toBeInTheDocument();
    });
  });

  it('resets evaluation results when switching target model', async () => {
    vi.spyOn(api, 'evaluateModelTelemetry').mockResolvedValue(mockRefEvaluationResponse);

    const handleSelectModel = vi.fn();

    render(
      <ThemeProvider>
        <TelemetryPage
          user={{ role: 'ADMIN' }}
          selectedModelId="model-eval-1"
          setSelectedModelId={handleSelectModel}
        />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('btn-run-reference-eval')).toBeInTheDocument();
    });

    // Run Reference on model-eval-1
    fireEvent.click(screen.getByTestId('btn-run-reference-eval'));
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Run Reference Evaluation' }));

    await waitFor(() => {
      expect(screen.getByTestId('confusion-matrix-card')).toBeInTheDocument();
    });

    // Switch model dropdown to model-eval-2
    const select = screen.getByLabelText(/select registered model/i);
    fireEvent.change(select, { target: { value: 'model-eval-2' } });

    // Expect evaluation state to be reset (empty state shown for model-eval-2)
    await waitFor(() => {
      expect(screen.getByTestId('comparison-empty-state')).toBeInTheDocument();
      expect(screen.queryByTestId('confusion-matrix-card')).not.toBeInTheDocument();
    });
  });
});
