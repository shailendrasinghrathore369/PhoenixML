import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TelemetryChart, METRIC_CONFIGS } from '../components/TelemetryChart.jsx';
import { TelemetryPage } from '../pages/TelemetryPage.jsx';
import { ThemeProvider } from '../context/ThemeContext.jsx';
import { api } from '../lib/api.js';

describe('TelemetryChart (Time-Series SVG Visualizer)', () => {
  const sampleObservations = [
    {
      id: 'obs-older',
      model_id: 'model-1',
      observed_at: '2026-11-09T10:00:00Z',
      prediction_count: 100,
      accuracy: 0.91,
      precision: 0.88,
      recall: 0.85,
      f1_score: 0.8647,
    },
    {
      id: 'obs-newer',
      model_id: 'model-1',
      observed_at: '2026-11-10T15:00:00Z',
      prediction_count: 120,
      accuracy: 0.95,
      precision: 0.92,
      recall: 0.89,
      f1_score: 0.9047,
    },
  ];

  it('renders real chronological values from oldest to newest on the x-axis', () => {
    // Pass observations in reverse order (newer first) to ensure chart sorts them chronologically
    const reversed = [...sampleObservations].reverse();
    render(<TelemetryChart observations={reversed} modelName="SpamSMS-LR" />);

    expect(screen.getByTestId('telemetry-chart')).toBeInTheDocument();
    expect(screen.getByTestId('telemetry-chart-svg')).toBeInTheDocument();

    // Check that points are rendered for both observations
    const f1Older = screen.getByTestId('chart-point-f1_score-0');
    const f1Newer = screen.getByTestId('chart-point-f1_score-1');
    expect(f1Older).toBeInTheDocument();
    expect(f1Newer).toBeInTheDocument();

    // Chronological order: older point (index 0) must have cx < newer point (index 1) cx
    const cxOlder = parseFloat(f1Older.getAttribute('cx'));
    const cxNewer = parseFloat(f1Newer.getAttribute('cx'));
    expect(cxOlder).toBeLessThan(cxNewer);

    // Y values: higher score (0.9047) should be higher up on chart (lower cy in SVG)
    const cyOlder = parseFloat(f1Older.getAttribute('cy'));
    const cyNewer = parseFloat(f1Newer.getAttribute('cy'));
    expect(cyNewer).toBeLessThan(cyOlder);
  });

  it('supports viewing all metrics or one metric at a time via selector controls', () => {
    render(<TelemetryChart observations={sampleObservations} />);

    // Default: All Metrics active
    const allBtn = screen.getByTestId('metric-selector-all');
    expect(allBtn).toHaveAttribute('aria-pressed', 'true');

    // All 4 metrics have rendered points
    METRIC_CONFIGS.forEach((m) => {
      expect(screen.getByTestId(`chart-point-${m.key}-0`)).toBeInTheDocument();
      expect(screen.getByTestId(`chart-point-${m.key}-1`)).toBeInTheDocument();
    });

    // Select F1 Score only
    const f1Btn = screen.getByTestId('metric-selector-f1_score');
    fireEvent.click(f1Btn);
    expect(f1Btn).toHaveAttribute('aria-pressed', 'true');
    expect(allBtn).toHaveAttribute('aria-pressed', 'false');

    // Only F1 points should exist, other metrics should be filtered out
    expect(screen.getByTestId('chart-point-f1_score-0')).toBeInTheDocument();
    expect(screen.queryByTestId('chart-point-accuracy-0')).not.toBeInTheDocument();
    expect(screen.queryByTestId('chart-point-precision-0')).not.toBeInTheDocument();
    expect(screen.queryByTestId('chart-point-recall-0')).not.toBeInTheDocument();

    // Select Accuracy
    const accBtn = screen.getByTestId('metric-selector-accuracy');
    fireEvent.click(accBtn);
    expect(accBtn).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByTestId('chart-point-accuracy-0')).toBeInTheDocument();
    expect(screen.queryByTestId('chart-point-f1_score-0')).not.toBeInTheDocument();

    // Switch back to All Metrics
    fireEvent.click(allBtn);
    expect(allBtn).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByTestId('chart-point-f1_score-0')).toBeInTheDocument();
    expect(screen.getByTestId('chart-point-accuracy-0')).toBeInTheDocument();
  });

  it('handles sparse observations and null/missing values without fabricating or interpolating points', () => {
    // 3 observations: obs 0 has F1, obs 1 has NULL F1, obs 2 has F1
    const sparseObs = [
      {
        id: 'obs-1',
        observed_at: '2026-11-08T10:00:00Z',
        f1_score: 0.85,
        accuracy: null,
      },
      {
        id: 'obs-2',
        observed_at: '2026-11-09T10:00:00Z',
        f1_score: null, // missing F1
        accuracy: 0.90,
      },
      {
        id: 'obs-3',
        observed_at: '2026-11-10T10:00:00Z',
        f1_score: 0.92,
        accuracy: null,
      },
    ];

    render(<TelemetryChart observations={sparseObs} />);

    // F1 should only have points at index 0 and 2 (NO point at index 1)
    expect(screen.getByTestId('chart-point-f1_score-0')).toBeInTheDocument();
    expect(screen.queryByTestId('chart-point-f1_score-1')).not.toBeInTheDocument();
    expect(screen.getByTestId('chart-point-f1_score-2')).toBeInTheDocument();

    // Accuracy should ONLY have a point at index 1 (NO points at index 0 or 2)
    expect(screen.queryByTestId('chart-point-accuracy-0')).not.toBeInTheDocument();
    expect(screen.getByTestId('chart-point-accuracy-1')).toBeInTheDocument();
    expect(screen.queryByTestId('chart-point-accuracy-2')).not.toBeInTheDocument();

    // Verify no line was drawn bridging across the missing F1 gap:
    // With indices 0 and 2 valid, segments are [ [pt0], [pt2] ], each length 1.
    // Length 1 segments do NOT produce a line path!
    const svg = screen.getByTestId('telemetry-chart-svg');
    const f1Group = svg.querySelector('.series-f1_score');
    expect(f1Group.querySelectorAll('path').length).toBe(0);
  });

  it('renders explanatory empty state when insufficient data exists', () => {
    // Empty observations array
    const { rerender } = render(<TelemetryChart observations={[]} />);
    expect(screen.getByTestId('telemetry-chart-empty')).toBeInTheDocument();
    expect(screen.getByText('Insufficient Observation Data')).toBeInTheDocument();
    expect(screen.getByText(/no telemetry observations recorded/i)).toBeInTheDocument();

    // Non-empty observations array but all metric fields are null
    const allNullObs = [
      {
        id: 'obs-null-1',
        observed_at: '2026-11-10T10:00:00Z',
        f1_score: null,
        accuracy: null,
        precision: null,
        recall: null,
      },
    ];
    rerender(<TelemetryChart observations={allNullObs} />);
    expect(screen.getByTestId('telemetry-chart-empty')).toBeInTheDocument();
    expect(screen.getByText(/none of the recorded observations contain valid/i)).toBeInTheDocument();
  });

  it('renders single-observation state properly without division-by-zero or crashing', () => {
    const singleObs = [
      {
        id: 'obs-single',
        observed_at: '2026-11-10T10:00:00Z',
        f1_score: 0.88,
        accuracy: 0.91,
        precision: 0.89,
        recall: 0.87,
      },
    ];

    render(<TelemetryChart observations={singleObs} />);

    expect(screen.getByTestId('telemetry-chart-svg')).toBeInTheDocument();
    expect(screen.getByText(/single observation recorded/i)).toBeInTheDocument();

    // Points should be centered on x-axis
    const pt = screen.getByTestId('chart-point-f1_score-0');
    expect(pt).toBeInTheDocument();
    const cx = parseFloat(pt.getAttribute('cx'));
    expect(isNaN(cx)).toBe(false);
    expect(cx).toBeGreaterThan(0);
  });

  it('displays accessible tooltip with timestamp, metric name, and exact value on hover and focus', () => {
    render(<TelemetryChart observations={sampleObservations} />);

    const pt = screen.getByTestId('chart-point-f1_score-0');

    // Tooltip should not be visible before hover
    expect(screen.queryByTestId('telemetry-tooltip')).not.toBeInTheDocument();

    // Hover point
    fireEvent.mouseEnter(pt);
    const tooltip = screen.getByTestId('telemetry-tooltip');
    expect(tooltip).toBeInTheDocument();
    expect(tooltip).toHaveAttribute('role', 'tooltip');
    expect(tooltip).toHaveTextContent('F1 Score');
    expect(tooltip).toHaveTextContent('0.8647');
    expect(tooltip).toHaveTextContent('86.5%');

    // Mouse leave removes tooltip
    fireEvent.mouseLeave(pt);
    expect(screen.queryByTestId('telemetry-tooltip')).not.toBeInTheDocument();
  });

  it('supports keyboard navigation: focus, Enter, and Escape controls for tooltips', () => {
    render(<TelemetryChart observations={sampleObservations} />);

    const pt = screen.getByTestId('chart-point-f1_score-1');

    // Check aria-label accessibility
    expect(pt.getAttribute('aria-label')).toContain('F1 Score');
    expect(pt.getAttribute('aria-label')).toContain('0.9047');
    expect(pt).toHaveAttribute('tabindex', '0');

    // Focus displays tooltip
    fireEvent.focus(pt);
    expect(screen.getByTestId('telemetry-tooltip')).toBeInTheDocument();
    expect(screen.getByTestId('telemetry-tooltip')).toHaveTextContent('0.9047');

    // Escape hides tooltip
    fireEvent.keyDown(pt, { key: 'Escape' });
    expect(screen.queryByTestId('telemetry-tooltip')).not.toBeInTheDocument();

    // Blur also hides tooltip
    fireEvent.focus(pt);
    expect(screen.getByTestId('telemetry-tooltip')).toBeInTheDocument();
    fireEvent.blur(pt);
    expect(screen.queryByTestId('telemetry-tooltip')).not.toBeInTheDocument();
  });

  it('uses 0–100% y-axis grid lines with percentage labels', () => {
    render(<TelemetryChart observations={sampleObservations} />);

    const svg = screen.getByTestId('telemetry-chart-svg');
    const gridY = svg.querySelector('.chart-grid-y');
    expect(gridY).toBeInTheDocument();

    // Verify 0%, 25%, 50%, 75%, 100% labels
    expect(gridY.textContent).toContain('100%');
    expect(gridY.textContent).toContain('75%');
    expect(gridY.textContent).toContain('50%');
    expect(gridY.textContent).toContain('25%');
    expect(gridY.textContent).toContain('0%');
  });

  it('supports dark/light themes cleanly using design tokens', () => {
    const { container, rerender } = render(
      <ThemeProvider>
        <TelemetryChart observations={sampleObservations} />
      </ThemeProvider>
    );

    const chartEl = screen.getByTestId('telemetry-chart');
    expect(chartEl).toHaveClass('table-card');

    // Switch theme attribute on documentElement
    document.documentElement.setAttribute('data-theme', 'light');
    rerender(
      <ThemeProvider>
        <TelemetryChart observations={sampleObservations} />
      </ThemeProvider>
    );
    expect(screen.getByTestId('telemetry-chart-svg')).toBeInTheDocument();

    // Restore default theme
    document.documentElement.setAttribute('data-theme', 'dark');
  });
});

describe('TelemetryPage Integration with TelemetryChart', () => {
  const sampleModels = [
    {
      id: 'model-a',
      name: 'SpamModel-A',
      framework: 'scikit-learn',
      algorithm: 'LogisticRegression',
      status: 'ACTIVE',
    },
    {
      id: 'model-b',
      name: 'SpamModel-B',
      framework: 'scikit-learn',
      algorithm: 'MultinomialNB',
      status: 'DEVELOPMENT',
    },
  ];

  const obsModelA = [
    {
      id: 'obs-a1',
      model_id: 'model-a',
      observed_at: '2026-11-10T12:00:00Z',
      prediction_count: 100,
      positive_prediction_count: 40,
      negative_prediction_count: 60,
      accuracy: 0.95,
      precision: 0.92,
      recall: 0.90,
      f1_score: 0.9097,
    },
  ];

  const obsModelB = [
    {
      id: 'obs-b1',
      model_id: 'model-b',
      observed_at: '2026-11-10T14:00:00Z',
      prediction_count: 50,
      positive_prediction_count: 20,
      negative_prediction_count: 30,
      accuracy: 0.88,
      precision: 0.85,
      recall: 0.82,
      f1_score: 0.8347,
    },
  ];

  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(api, 'listModels').mockResolvedValue(sampleModels);
    vi.spyOn(api, 'listObservations').mockImplementation(async (modelId) => {
      if (modelId === 'model-b') return obsModelB;
      return obsModelA;
    });
  });

  it('renders TelemetryChart below summary cards and above the observation table', async () => {
    render(
      <ThemeProvider>
        <TelemetryPage user={{ role: 'ADMIN' }} selectedModelId="model-a" />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('telemetry-chart')).toBeInTheDocument();
      expect(screen.getByTestId('telemetry-chart-svg')).toBeInTheDocument();
      expect(screen.getByText('Historical Observations Log')).toBeInTheDocument();
    });

    // Check metric controls inside chart
    expect(screen.getByTestId('metric-selector-all')).toBeInTheDocument();
    expect(screen.getByTestId('metric-selector-f1_score')).toBeInTheDocument();
  });

  it('updates TelemetryChart points when model selection changes', async () => {
    const handleSelectModel = vi.fn();

    render(
      <ThemeProvider>
        <TelemetryPage
          user={{ role: 'ADMIN' }}
          selectedModelId="model-a"
          setSelectedModelId={handleSelectModel}
        />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('telemetry-chart-svg')).toBeInTheDocument();
      expect(screen.getByTestId('chart-point-f1_score-0')).toBeInTheDocument();
    });

    // Initial point has Model A's F1 score 0.9097
    const ptA = screen.getByTestId('chart-point-f1_score-0');
    expect(ptA.getAttribute('aria-label')).toContain('0.9097');

    // Switch model dropdown to Model B
    const select = screen.getByLabelText(/select registered model/i);
    fireEvent.change(select, { target: { value: 'model-b' } });
    expect(handleSelectModel).toHaveBeenCalledWith('model-b');
  });
});
