import React, { useState, useMemo, useRef, useCallback } from 'react';
import {
  TrendingUp,
  Activity,
  AlertCircle,
  HelpCircle,
  Eye,
} from 'lucide-react';
import { formatDate, formatMetric } from '../lib/utils.js';

export const METRIC_CONFIGS = [
  {
    key: 'f1_score',
    label: 'F1 Score',
    shortLabel: 'F1',
    colorVar: 'var(--chart-production, #3b82f6)',
    stroke: '#3b82f6',
    description: 'Harmonic mean of precision and recall',
    getValue: (obs) => {
      const val = obs.f1_score ?? obs.f1;
      return typeof val === 'number' && !isNaN(val) ? val : null;
    },
  },
  {
    key: 'accuracy',
    label: 'Accuracy',
    shortLabel: 'Acc',
    colorVar: 'var(--chart-baseline, #10b981)',
    stroke: '#10b981',
    description: 'Proportion of correct classifications across all evaluated samples',
    getValue: (obs) => {
      const val = obs.accuracy;
      return typeof val === 'number' && !isNaN(val) ? val : null;
    },
  },
  {
    key: 'precision',
    label: 'Precision',
    shortLabel: 'Prec',
    colorVar: 'var(--chart-warning, #f59e0b)',
    stroke: '#f59e0b',
    description: 'Proportion of true positive classifications among positive predictions',
    getValue: (obs) => {
      const val = obs.precision;
      return typeof val === 'number' && !isNaN(val) ? val : null;
    },
  },
  {
    key: 'recall',
    label: 'Recall',
    shortLabel: 'Rec',
    colorVar: '#a855f7',
    stroke: '#a855f7',
    description: 'Proportion of true positives detected out of all actual positives',
    getValue: (obs) => {
      const val = obs.recall;
      return typeof val === 'number' && !isNaN(val) ? val : null;
    },
  },
];

const SVG_WIDTH = 800;
const SVG_HEIGHT = 320;
const MARGIN = { top: 28, right: 32, bottom: 48, left: 56 };
const PLOT_WIDTH = SVG_WIDTH - MARGIN.left - MARGIN.right;
const PLOT_HEIGHT = SVG_HEIGHT - MARGIN.top - MARGIN.bottom;

// Standard Y-axis ticks for 0–100% scale
const Y_TICKS = [
  { val: 1.0, label: '100%' },
  { val: 0.75, label: '75%' },
  { val: 0.5, label: '50%' },
  { val: 0.25, label: '25%' },
  { val: 0.0, label: '0%' },
];

/**
 * Format timestamp nicely for short SVG x-axis ticks
 */
function formatShortTick(dateStr) {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '';
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
  } catch {
    return '';
  }
}

/**
 * Format short date (MM/DD) for SVG x-axis sub-labels
 */
function formatShortDate(dateStr) {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '';
    return d.toLocaleDateString([], { month: 'numeric', day: 'numeric' });
  } catch {
    return '';
  }
}

export function TelemetryChart({
  observations = [],
  modelName = '',
  loading = false,
  className = '',
}) {
  const [selectedMetric, setSelectedMetric] = useState('all');
  const [activeTooltip, setActiveTooltip] = useState(null);
  const containerRef = useRef(null);

  // Filter and chronologically sort observations (oldest -> newest)
  const chronologicalObs = useMemo(() => {
    if (!Array.isArray(observations)) return [];
    return [...observations]
      .filter((o) => o && (o.observed_at || o.created_at || o.timestamp))
      .sort((a, b) => {
        const ta = new Date(a.observed_at || a.created_at || a.timestamp).getTime();
        const tb = new Date(b.observed_at || b.created_at || b.timestamp).getTime();
        return ta - tb;
      });
  }, [observations]);

  // Determine active metrics based on selector
  const activeMetrics = useMemo(() => {
    if (selectedMetric === 'all') {
      return METRIC_CONFIGS;
    }
    return METRIC_CONFIGS.filter((m) => m.key === selectedMetric);
  }, [selectedMetric]);

  // Check how many observations have valid numeric values for active metrics
  const validPointCounts = useMemo(() => {
    const counts = {};
    METRIC_CONFIGS.forEach((m) => {
      counts[m.key] = chronologicalObs.filter((o) => m.getValue(o) !== null).length;
    });
    return counts;
  }, [chronologicalObs]);

  const totalValidActivePoints = useMemo(() => {
    return activeMetrics.reduce((sum, m) => sum + (validPointCounts[m.key] || 0), 0);
  }, [activeMetrics, validPointCounts]);

  const hasInsufficientData = chronologicalObs.length === 0 || totalValidActivePoints === 0;
  const isSingleObservation = chronologicalObs.length === 1;

  // X coordinate calculation
  const getX = useCallback(
    (timestamp, index) => {
      if (chronologicalObs.length <= 1) {
        return MARGIN.left + PLOT_WIDTH / 2;
      }
      const minTime = new Date(
        chronologicalObs[0].observed_at || chronologicalObs[0].created_at || chronologicalObs[0].timestamp
      ).getTime();
      const maxTime = new Date(
        chronologicalObs[chronologicalObs.length - 1].observed_at ||
          chronologicalObs[chronologicalObs.length - 1].created_at ||
          chronologicalObs[chronologicalObs.length - 1].timestamp
      ).getTime();

      if (maxTime === minTime) {
        return MARGIN.left + (index / (chronologicalObs.length - 1)) * PLOT_WIDTH;
      }

      const t = new Date(timestamp).getTime();
      const ratio = (t - minTime) / (maxTime - minTime);
      return MARGIN.left + Math.max(0, Math.min(1, ratio)) * PLOT_WIDTH;
    },
    [chronologicalObs]
  );

  // Y coordinate calculation (fixed 0–100% scale)
  const getY = useCallback((val) => {
    const clamped = Math.max(0, Math.min(1, Number(val)));
    return MARGIN.top + (1 - clamped) * PLOT_HEIGHT;
  }, []);

  // Build continuous line segments and points for each metric (never interpolating across nulls)
  const seriesData = useMemo(() => {
    return activeMetrics.map((metric) => {
      const segments = [];
      let currentSeg = [];

      chronologicalObs.forEach((obs, index) => {
        const val = metric.getValue(obs);
        const timestamp = obs.observed_at || obs.created_at || obs.timestamp;
        if (val !== null) {
          const point = {
            x: getX(timestamp, index),
            y: getY(val),
            val,
            formatted: formatMetric(val, 4),
            percentage: `${(val * 100).toFixed(1)}%`,
            timestamp,
            metricKey: metric.key,
            metricLabel: metric.label,
            stroke: metric.stroke,
            index,
            obs,
          };
          currentSeg.push(point);
        } else {
          if (currentSeg.length > 0) {
            segments.push(currentSeg);
            currentSeg = [];
          }
        }
      });
      if (currentSeg.length > 0) {
        segments.push(currentSeg);
      }

      // Flatten points for easy circle rendering and lookup
      const allPoints = segments.flat();

      return {
        metric,
        segments,
        allPoints,
      };
    });
  }, [activeMetrics, chronologicalObs, getX, getY]);

  // Compute x-axis ticks
  const xTicks = useMemo(() => {
    if (chronologicalObs.length === 0) return [];
    if (chronologicalObs.length === 1) {
      const obs = chronologicalObs[0];
      const t = obs.observed_at || obs.created_at || obs.timestamp;
      return [
        {
          x: MARGIN.left + PLOT_WIDTH / 2,
          timeLabel: formatShortTick(t),
          dateLabel: formatShortDate(t),
          fullDate: formatDate(t),
          raw: t,
        },
      ];
    }

    // Pick up to 5 evenly distributed ticks
    const maxTicks = Math.min(5, chronologicalObs.length);
    const step = (chronologicalObs.length - 1) / (maxTicks - 1);
    const ticks = [];
    const usedIndices = new Set();

    for (let i = 0; i < maxTicks; i++) {
      const idx = Math.round(i * step);
      if (!usedIndices.has(idx) && chronologicalObs[idx]) {
        usedIndices.add(idx);
        const obs = chronologicalObs[idx];
        const t = obs.observed_at || obs.created_at || obs.timestamp;
        ticks.push({
          x: getX(t, idx),
          timeLabel: formatShortTick(t),
          dateLabel: formatShortDate(t),
          fullDate: formatDate(t),
          raw: t,
        });
      }
    }
    return ticks;
  }, [chronologicalObs, getX]);

  // Tooltip position calculator relative to container
  const handlePointFocus = (point, targetEl) => {
    if (!targetEl || !containerRef.current) {
      setActiveTooltip({ point, xRatio: point.x / SVG_WIDTH, yRatio: point.y / SVG_HEIGHT });
      return;
    }
    const containerRect = containerRef.current.getBoundingClientRect();
    const targetRect = targetEl.getBoundingClientRect();
    setActiveTooltip({
      point,
      domX: targetRect.left + targetRect.width / 2 - containerRect.left,
      domY: targetRect.top - containerRect.top,
    });
  };

  const handlePointBlur = () => {
    setActiveTooltip(null);
  };

  return (
    <div
      ref={containerRef}
      className={`telemetry-chart-card table-card ${className}`}
      data-testid="telemetry-chart"
      data-model={modelName || undefined}
      style={{
        padding: '1.25rem',
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
      }}
    >
      {/* Header & Controls */}
      <div
        className="telemetry-chart-header"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
          borderBottom: '1px solid var(--border-color)',
          paddingBottom: '0.875rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '2rem',
              height: '2rem',
              borderRadius: 'var(--radius-md, 6px)',
              backgroundColor: 'var(--primary-bg-subtle, rgba(37, 99, 235, 0.12))',
              color: 'var(--color-primary, #3b82f6)',
            }}
          >
            <TrendingUp className="icon-sm" aria-hidden="true" />
          </div>
          <div>
            <h3
              style={{
                fontSize: '1rem',
                fontWeight: 600,
                color: 'var(--text-primary)',
                margin: 0,
                lineHeight: 1.25,
              }}
            >
              Performance Trajectory (Time-Series)
            </h3>
            <p
              style={{
                fontSize: '0.8125rem',
                color: 'var(--text-secondary)',
                margin: '0.2rem 0 0 0',
              }}
            >
              0–100% y-axis scale across chronological observations
            </p>
          </div>
        </div>

        {/* Metric Selection Controls */}
        <div
          role="group"
          aria-label="Filter metrics displayed on chart"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.375rem',
            flexWrap: 'wrap',
          }}
        >
          <button
            type="button"
            className={`btn btn-sm ${selectedMetric === 'all' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setSelectedMetric('all')}
            aria-pressed={selectedMetric === 'all'}
            data-testid="metric-selector-all"
            style={{ fontSize: '0.75rem', padding: '0.25rem 0.625rem' }}
          >
            All Metrics
          </button>
          {METRIC_CONFIGS.map((m) => {
            const isSelected = selectedMetric === m.key;
            return (
              <button
                key={m.key}
                type="button"
                className={`btn btn-sm ${isSelected ? 'btn-primary' : 'btn-outline'}`}
                onClick={() => setSelectedMetric(m.key)}
                aria-pressed={isSelected}
                data-testid={`metric-selector-${m.key}`}
                style={{
                  fontSize: '0.75rem',
                  padding: '0.25rem 0.625rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.375rem',
                }}
              >
                <span
                  style={{
                    display: 'inline-block',
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: m.stroke,
                  }}
                  aria-hidden="true"
                />
                <span>{m.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Explanatory Empty State if insufficient data */}
      {hasInsufficientData ? (
        <div
          className="telemetry-chart-empty"
          data-testid="telemetry-chart-empty"
          role="status"
          style={{
            padding: '3rem 1.5rem',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.75rem',
            borderRadius: 'var(--radius-lg, 8px)',
            backgroundColor: 'var(--surface-subtle, rgba(0, 0, 0, 0.02))',
            border: '1px dashed var(--border-color)',
          }}
        >
          <div
            style={{
              width: '2.75rem',
              height: '2.75rem',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: 'var(--bg-secondary)',
              color: 'var(--text-muted)',
            }}
          >
            <Activity className="icon-md" aria-hidden="true" />
          </div>
          <h4
            style={{
              fontSize: '0.9375rem',
              fontWeight: 600,
              color: 'var(--text-primary)',
              margin: 0,
            }}
          >
            Insufficient Observation Data
          </h4>
          <p
            style={{
              fontSize: '0.8125rem',
              color: 'var(--text-secondary)',
              maxWidth: '440px',
              margin: 0,
              lineHeight: 1.4,
            }}
          >
            {chronologicalObs.length === 0
              ? 'No telemetry observations recorded for this model yet. Run model evaluations to plot classification metrics over time.'
              : selectedMetric === 'all'
              ? 'None of the recorded observations contain valid F1, Accuracy, Precision, or Recall values.'
              : `None of the recorded observations contain valid ${
                  METRIC_CONFIGS.find((m) => m.key === selectedMetric)?.label || selectedMetric
                } values.`}
          </p>
        </div>
      ) : (
        /* Chart SVG Display */
        <div
          className="telemetry-svg-container"
          style={{
            width: '100%',
            overflowX: 'auto',
            position: 'relative',
          }}
        >
          {isSingleObservation && (
            <div
              style={{
                fontSize: '0.75rem',
                color: 'var(--text-muted)',
                marginBottom: '0.5rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.375rem',
              }}
            >
              <AlertCircle className="icon-xs text-primary" aria-hidden="true" />
              <span>
                Single observation recorded — additional observations will plot trajectory lines between evaluation intervals.
              </span>
            </div>
          )}

          <svg
            viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
            className="telemetry-chart-svg"
            data-testid="telemetry-chart-svg"
            role="img"
            aria-label={`Time-series performance chart displaying ${
              selectedMetric === 'all' ? 'F1 Score, Accuracy, Precision, Recall' : selectedMetric
            } from 0 to 100 percent`}
            style={{
              width: '100%',
              height: 'auto',
              minHeight: '260px',
              maxHeight: '380px',
              display: 'block',
              overflow: 'visible',
            }}
          >
            <defs>
              {/* Subtle gradient for single metric view */}
              {selectedMetric !== 'all' && (
                <linearGradient
                  id={`area-gradient-${selectedMetric}`}
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop
                    offset="0%"
                    stopColor={METRIC_CONFIGS.find((m) => m.key === selectedMetric)?.stroke || '#3b82f6'}
                    stopOpacity="0.25"
                  />
                  <stop
                    offset="100%"
                    stopColor={METRIC_CONFIGS.find((m) => m.key === selectedMetric)?.stroke || '#3b82f6'}
                    stopOpacity="0.0"
                  />
                </linearGradient>
              )}
            </defs>

            {/* Y-Axis Horizontal Gridlines & Labels */}
            <g className="chart-grid-y" aria-hidden="true">
              {Y_TICKS.map((tick) => {
                const y = getY(tick.val);
                return (
                  <g key={`y-tick-${tick.val}`}>
                    <line
                      x1={MARGIN.left}
                      y1={y}
                      x2={MARGIN.left + PLOT_WIDTH}
                      y2={y}
                      stroke="var(--border-color, #334155)"
                      strokeOpacity={tick.val === 0 ? 0.8 : 0.35}
                      strokeDasharray={tick.val === 0 ? undefined : '3 3'}
                      strokeWidth={1}
                    />
                    <text
                      x={MARGIN.left - 10}
                      y={y + 4}
                      textAnchor="end"
                      fontSize="11"
                      fontFamily="var(--font-mono, monospace)"
                      fill="var(--text-muted, #94a3b8)"
                    >
                      {tick.label}
                    </text>
                  </g>
                );
              })}
            </g>

            {/* X-Axis Baseline & Ticks */}
            <g className="chart-axis-x" aria-hidden="true">
              <line
                x1={MARGIN.left}
                y1={MARGIN.top + PLOT_HEIGHT}
                x2={MARGIN.left + PLOT_WIDTH}
                y2={MARGIN.top + PLOT_HEIGHT}
                stroke="var(--border-color, #334155)"
                strokeWidth={1.5}
              />
              {xTicks.map((tick, i) => (
                <g key={`x-tick-${i}`}>
                  <line
                    x1={tick.x}
                    y1={MARGIN.top + PLOT_HEIGHT}
                    x2={tick.x}
                    y2={MARGIN.top + PLOT_HEIGHT + 5}
                    stroke="var(--border-color, #334155)"
                    strokeWidth={1.5}
                  />
                  <text
                    x={tick.x}
                    y={MARGIN.top + PLOT_HEIGHT + 18}
                    textAnchor="middle"
                    fontSize="11"
                    fontFamily="var(--font-mono, monospace)"
                    fill="var(--text-secondary, #cbd5e1)"
                  >
                    {tick.timeLabel}
                  </text>
                  {tick.dateLabel && (
                    <text
                      x={tick.x}
                      y={MARGIN.top + PLOT_HEIGHT + 31}
                      textAnchor="middle"
                      fontSize="9.5"
                      fontFamily="var(--font-mono, monospace)"
                      fill="var(--text-muted, #94a3b8)"
                    >
                      {tick.dateLabel}
                    </text>
                  )}
                </g>
              ))}
            </g>

            {/* Active Vertical Crosshair Guide */}
            {activeTooltip?.point && (
              <line
                x1={activeTooltip.point.x}
                y1={MARGIN.top}
                x2={activeTooltip.point.x}
                y2={MARGIN.top + PLOT_HEIGHT}
                stroke="var(--text-dim, #64748b)"
                strokeWidth={1.25}
                strokeDasharray="3 3"
                pointerEvents="none"
              />
            )}

            {/* Plot Lines & Area Fills for each metric */}
            {seriesData.map(({ metric, segments }) => (
              <g key={`metric-series-${metric.key}`} className={`series-${metric.key}`}>
                {/* Area fill for single metric view */}
                {selectedMetric === metric.key &&
                  segments.map((seg, sIdx) => {
                    if (seg.length < 2) return null;
                    const areaPath = `M ${seg[0].x} ${seg[0].y} ` +
                      seg.slice(1).map((p) => `L ${p.x} ${p.y}`).join(' ') +
                      ` L ${seg[seg.length - 1].x} ${MARGIN.top + PLOT_HEIGHT} ` +
                      ` L ${seg[0].x} ${MARGIN.top + PLOT_HEIGHT} Z`;
                    return (
                      <path
                        key={`area-${metric.key}-${sIdx}`}
                        d={areaPath}
                        fill={`url(#area-gradient-${selectedMetric})`}
                        pointerEvents="none"
                      />
                    );
                  })}

                {/* Trajectory Lines connecting consecutive points without interpolating across missing gaps */}
                {segments.map((seg, sIdx) => {
                  if (seg.length < 2) return null;
                  const linePath = `M ${seg[0].x} ${seg[0].y} ` +
                    seg.slice(1).map((p) => `L ${p.x} ${p.y}`).join(' ');
                  return (
                    <path
                      key={`line-${metric.key}-${sIdx}`}
                      d={linePath}
                      fill="none"
                      stroke={metric.stroke}
                      strokeWidth={2.5}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  );
                })}
              </g>
            ))}

            {/* Data Points (Focusable & Hoverable Circles) */}
            {seriesData.map(({ metric, allPoints }) => (
              <g key={`metric-points-${metric.key}`} className={`points-${metric.key}`}>
                {allPoints.map((pt) => {
                  const isActive = activeTooltip?.point === pt;
                  return (
                    <g key={`pt-${metric.key}-${pt.index}`}>
                      {/* Active Halo */}
                      {isActive && (
                        <circle
                          cx={pt.x}
                          cy={pt.y}
                          r={10}
                          fill="none"
                          stroke={pt.stroke}
                          strokeWidth={2}
                          opacity={0.65}
                          pointerEvents="none"
                        />
                      )}
                      <circle
                        cx={pt.x}
                        cy={pt.y}
                        r={isActive ? 6 : 4.5}
                        fill={pt.stroke}
                        stroke="var(--bg-card, #0f172a)"
                        strokeWidth={2}
                        tabIndex={0}
                        role="button"
                        aria-label={`${pt.metricLabel}: ${pt.formatted} (${pt.percentage}) recorded at ${formatDate(
                          pt.timestamp
                        )}`}
                        data-testid={`chart-point-${pt.metricKey}-${pt.index}`}
                        onMouseEnter={(e) => handlePointFocus(pt, e.currentTarget)}
                        onMouseLeave={handlePointBlur}
                        onFocus={(e) => handlePointFocus(pt, e.currentTarget)}
                        onBlur={handlePointBlur}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            handlePointFocus(pt, e.currentTarget);
                          } else if (e.key === 'Escape') {
                            handlePointBlur();
                          }
                        }}
                        style={{
                          cursor: 'pointer',
                          outline: 'none',
                          transition: 'r 0.15s ease, stroke-width 0.15s ease',
                        }}
                      />
                    </g>
                  );
                })}
              </g>
            ))}
          </svg>

          {/* Accessible Floating Tooltip Overlay */}
          {activeTooltip?.point && (
            <div
              role="tooltip"
              data-testid="telemetry-tooltip"
              className="telemetry-chart-tooltip"
              style={{
                position: 'absolute',
                left: `${
                  activeTooltip.domX !== undefined
                    ? activeTooltip.domX
                    : activeTooltip.xRatio * 100 + '%'
                }`,
                top: `${
                  activeTooltip.domY !== undefined
                    ? activeTooltip.domY
                    : activeTooltip.yRatio * 100 + '%'
                }`,
                transform: 'translate(-50%, -100%) translateY(-14px)',
                pointerEvents: 'none',
                zIndex: 60,
                backgroundColor: 'var(--bg-secondary, #1e293b)',
                border: '1px solid var(--border-color, #334155)',
                borderRadius: 'var(--radius-md, 6px)',
                boxShadow: 'var(--shadow-lg, 0 10px 15px -3px rgba(0, 0, 0, 0.3))',
                padding: '0.625rem 0.875rem',
                minWidth: '180px',
                color: 'var(--text-primary, #f8fafc)',
                fontSize: '0.8125rem',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '0.5rem',
                  borderBottom: '1px solid var(--border-color)',
                  paddingBottom: '0.25rem',
                  marginBottom: '0.375rem',
                }}
              >
                <span
                  style={{
                    fontSize: '0.75rem',
                    color: 'var(--text-muted)',
                    fontFamily: 'var(--font-mono, monospace)',
                  }}
                >
                  {formatDate(activeTooltip.point.timestamp)}
                </span>
                {activeTooltip.point.obs.prediction_count !== undefined && (
                  <span style={{ fontSize: '0.6875rem', color: 'var(--text-dim)' }}>
                    N={activeTooltip.point.obs.prediction_count}
                  </span>
                )}
              </div>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '0.75rem',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                  <span
                    style={{
                      display: 'inline-block',
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: activeTooltip.point.stroke,
                    }}
                    aria-hidden="true"
                  />
                  <strong style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    {activeTooltip.point.metricLabel}
                  </strong>
                </div>
                <div style={{ textAlign: 'right', fontFamily: 'var(--font-mono, monospace)' }}>
                  <span
                    style={{
                      fontWeight: 700,
                      color: activeTooltip.point.stroke,
                    }}
                  >
                    {activeTooltip.point.formatted}
                  </span>
                  <span
                    style={{
                      fontSize: '0.6875rem',
                      color: 'var(--text-muted)',
                      marginLeft: '0.25rem',
                    }}
                  >
                    ({activeTooltip.point.percentage})
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Metric Legend & Value Summary Bar */}
      <div
        className="telemetry-chart-legend"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'flex-start',
          gap: '1.25rem',
          flexWrap: 'wrap',
          borderTop: '1px solid var(--border-color)',
          paddingTop: '0.75rem',
          fontSize: '0.75rem',
        }}
      >
        {METRIC_CONFIGS.map((m) => {
          const count = validPointCounts[m.key] || 0;
          const isDimmed = selectedMetric !== 'all' && selectedMetric !== m.key;
          return (
            <div
              key={`legend-${m.key}`}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.375rem',
                opacity: isDimmed ? 0.35 : 1,
                transition: 'opacity 0.2s ease',
              }}
            >
              <span
                style={{
                  display: 'inline-block',
                  width: '10px',
                  height: '10px',
                  borderRadius: '2px',
                  backgroundColor: m.stroke,
                }}
                aria-hidden="true"
              />
              <span style={{ color: 'var(--text-secondary)' }}>{m.label}:</span>
              <strong style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                {count > 0 ? `${count} pts` : 'No data'}
              </strong>
            </div>
          );
        })}
      </div>
    </div>
  );
}
