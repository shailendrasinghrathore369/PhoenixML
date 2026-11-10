import React from 'react';
import { Grid, CheckCircle2, AlertTriangle, AlertCircle, Info } from 'lucide-react';

/**
 * Format exact integer counts from backend evaluation metrics.
 * Preserves explicit zeros and displays N/A for missing or null values.
 * Never derives counts from rounded metrics.
 */
function formatCount(val) {
  if (val === 0) return '0';
  if (val === null || val === undefined || isNaN(val) || typeof val !== 'number') {
    return 'N/A';
  }
  return Number(val).toLocaleString();
}

/**
 * Calculates percentage of total for cell counts safely.
 */
function calcPercentage(count, total) {
  if (
    typeof count !== 'number' ||
    typeof total !== 'number' ||
    isNaN(count) ||
    isNaN(total) ||
    total <= 0
  ) {
    return null;
  }
  return ((count / total) * 100).toFixed(1) + '%';
}

export function ConfusionMatrix({
  metrics = null,
  datasetName = 'reference',
  title = '2x2 Confusion Matrix',
  subtitle = 'Binary classification outcomes comparing ground truth against model predictions',
  className = '',
}) {
  const tp = metrics?.true_positives ?? null;
  const fp = metrics?.false_positives ?? null;
  const tn = metrics?.true_negatives ?? null;
  const fn = metrics?.false_negatives ?? null;

  const hasAllCounts =
    typeof tp === 'number' &&
    typeof fp === 'number' &&
    typeof tn === 'number' &&
    typeof fn === 'number';

  const totalEvaluated = hasAllCounts
    ? tp + fp + tn + fn
    : metrics?.prediction_count ?? null;

  return (
    <div
      className={`confusion-matrix-card table-card ${className}`}
      data-testid="confusion-matrix-card"
      style={{
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.75rem',
          borderBottom: '1px solid var(--border-color)',
          paddingBottom: '0.75rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
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
            <Grid className="icon-sm" aria-hidden="true" />
          </div>
          <div>
            <h3
              style={{
                fontSize: '0.9375rem',
                fontWeight: 600,
                color: 'var(--text-primary)',
                margin: 0,
              }}
            >
              {title}
            </h3>
            <p
              style={{
                fontSize: '0.75rem',
                color: 'var(--text-secondary)',
                margin: '0.15rem 0 0 0',
              }}
            >
              {subtitle}
            </p>
          </div>
        </div>

        {datasetName && (
          <span
            className="status-badge neutral status-badge-sm"
            data-testid="confusion-matrix-dataset-badge"
            style={{ textTransform: 'capitalize' }}
          >
            {datasetName} Dataset
          </span>
        )}
      </div>

      {/* 2x2 Accessible Matrix Grid / Table */}
      <div style={{ width: '100%', overflowX: 'auto' }}>
        <table
          className="confusion-matrix-table"
          data-testid="confusion-matrix-table"
          role="table"
          aria-label={`${datasetName || 'Model'} Confusion Matrix`}
          style={{
            width: '100%',
            borderCollapse: 'separate',
            borderSpacing: '0.5rem',
            fontSize: '0.8125rem',
          }}
        >
          <caption className="sr-only">
            Confusion matrix displaying True Positives, False Positives, True Negatives, and False
            Negatives for {datasetName} evaluation.
          </caption>
          <thead>
            <tr>
              <th
                scope="col"
                rowSpan={2}
                style={{
                  width: '22%',
                  textAlign: 'left',
                  verticalAlign: 'bottom',
                  padding: '0.5rem 0.75rem',
                  color: 'var(--text-muted)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                Actual \ Predicted
              </th>
              <th
                scope="col"
                colSpan={2}
                style={{
                  textAlign: 'center',
                  padding: '0.5rem',
                  color: 'var(--text-secondary)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  borderBottom: '1px solid var(--border-color)',
                }}
              >
                Predicted Class
              </th>
            </tr>
            <tr>
              <th
                scope="col"
                style={{
                  width: '39%',
                  textAlign: 'center',
                  padding: '0.5rem',
                  color: 'var(--color-primary, #3b82f6)',
                  fontWeight: 600,
                }}
              >
                Predicted Positive (Spam)
              </th>
              <th
                scope="col"
                style={{
                  width: '39%',
                  textAlign: 'center',
                  padding: '0.5rem',
                  color: 'var(--text-secondary)',
                  fontWeight: 600,
                }}
              >
                Predicted Negative (Ham)
              </th>
            </tr>
          </thead>
          <tbody>
            {/* Row 1: Actual Spam (Positive) */}
            <tr>
              <th
                scope="row"
                style={{
                  textAlign: 'left',
                  verticalAlign: 'middle',
                  padding: '0.75rem',
                  color: 'var(--color-primary, #3b82f6)',
                  fontWeight: 600,
                  whiteSpace: 'nowrap',
                }}
              >
                Actual Positive (Spam)
              </th>

              {/* Cell: True Positive (TP) */}
              <td
                data-testid="cell-true-positives"
                aria-label={`True Positives: ${formatCount(tp)}`}
                style={{
                  backgroundColor: 'var(--healthy-bg, rgba(16, 185, 129, 0.1))',
                  border: '1px solid var(--healthy-border, rgba(16, 185, 129, 0.35))',
                  borderRadius: 'var(--radius-md, 6px)',
                  padding: '0.875rem 1rem',
                  textAlign: 'center',
                  verticalAlign: 'middle',
                }}
              >
                <div
                  style={{
                    fontSize: '0.6875rem',
                    fontWeight: 600,
                    color: 'var(--color-healthy, #10b981)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    marginBottom: '0.25rem',
                  }}
                >
                  True Positive (TP)
                </div>
                <div
                  data-testid="count-true-positives"
                  style={{
                    fontFamily: 'var(--font-mono, monospace)',
                    fontSize: '1.25rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                  }}
                >
                  {formatCount(tp)}
                </div>
                <div
                  style={{
                    fontSize: '0.6875rem',
                    color: 'var(--text-muted)',
                    marginTop: '0.25rem',
                  }}
                >
                  {calcPercentage(tp, totalEvaluated)
                    ? `${calcPercentage(tp, totalEvaluated)} of total`
                    : 'Correct spam detection'}
                </div>
              </td>

              {/* Cell: False Negative (FN) */}
              <td
                data-testid="cell-false-negatives"
                aria-label={`False Negatives: ${formatCount(fn)}`}
                style={{
                  backgroundColor: 'var(--critical-bg, rgba(244, 63, 94, 0.1))',
                  border: '1px solid var(--critical-border, rgba(244, 63, 94, 0.35))',
                  borderRadius: 'var(--radius-md, 6px)',
                  padding: '0.875rem 1rem',
                  textAlign: 'center',
                  verticalAlign: 'middle',
                }}
              >
                <div
                  style={{
                    fontSize: '0.6875rem',
                    fontWeight: 600,
                    color: 'var(--color-critical, #f43f5e)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    marginBottom: '0.25rem',
                  }}
                >
                  False Negative (FN)
                </div>
                <div
                  data-testid="count-false-negatives"
                  style={{
                    fontFamily: 'var(--font-mono, monospace)',
                    fontSize: '1.25rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                  }}
                >
                  {formatCount(fn)}
                </div>
                <div
                  style={{
                    fontSize: '0.6875rem',
                    color: 'var(--text-muted)',
                    marginTop: '0.25rem',
                  }}
                >
                  {calcPercentage(fn, totalEvaluated)
                    ? `${calcPercentage(fn, totalEvaluated)} of total`
                    : 'Missed spam (leaked)'}
                </div>
              </td>
            </tr>

            {/* Row 2: Actual Ham (Negative) */}
            <tr>
              <th
                scope="row"
                style={{
                  textAlign: 'left',
                  verticalAlign: 'middle',
                  padding: '0.75rem',
                  color: 'var(--text-secondary)',
                  fontWeight: 600,
                  whiteSpace: 'nowrap',
                }}
              >
                Actual Negative (Ham)
              </th>

              {/* Cell: False Positive (FP) */}
              <td
                data-testid="cell-false-positives"
                aria-label={`False Positives: ${formatCount(fp)}`}
                style={{
                  backgroundColor: 'var(--warning-bg, rgba(245, 158, 11, 0.1))',
                  border: '1px solid var(--warning-border, rgba(245, 158, 11, 0.35))',
                  borderRadius: 'var(--radius-md, 6px)',
                  padding: '0.875rem 1rem',
                  textAlign: 'center',
                  verticalAlign: 'middle',
                }}
              >
                <div
                  style={{
                    fontSize: '0.6875rem',
                    fontWeight: 600,
                    color: 'var(--color-warning, #f59e0b)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    marginBottom: '0.25rem',
                  }}
                >
                  False Positive (FP)
                </div>
                <div
                  data-testid="count-false-positives"
                  style={{
                    fontFamily: 'var(--font-mono, monospace)',
                    fontSize: '1.25rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                  }}
                >
                  {formatCount(fp)}
                </div>
                <div
                  style={{
                    fontSize: '0.6875rem',
                    color: 'var(--text-muted)',
                    marginTop: '0.25rem',
                  }}
                >
                  {calcPercentage(fp, totalEvaluated)
                    ? `${calcPercentage(fp, totalEvaluated)} of total`
                    : 'Ham falsely flagged'}
                </div>
              </td>

              {/* Cell: True Negative (TN) */}
              <td
                data-testid="cell-true-negatives"
                aria-label={`True Negatives: ${formatCount(tn)}`}
                style={{
                  backgroundColor: 'var(--primary-bg-subtle, rgba(37, 99, 235, 0.08))',
                  border: '1px solid var(--primary-border-subtle, rgba(37, 99, 235, 0.35))',
                  borderRadius: 'var(--radius-md, 6px)',
                  padding: '0.875rem 1rem',
                  textAlign: 'center',
                  verticalAlign: 'middle',
                }}
              >
                <div
                  style={{
                    fontSize: '0.6875rem',
                    fontWeight: 600,
                    color: 'var(--color-primary, #3b82f6)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    marginBottom: '0.25rem',
                  }}
                >
                  True Negative (TN)
                </div>
                <div
                  data-testid="count-true-negatives"
                  style={{
                    fontFamily: 'var(--font-mono, monospace)',
                    fontSize: '1.25rem',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                  }}
                >
                  {formatCount(tn)}
                </div>
                <div
                  style={{
                    fontSize: '0.6875rem',
                    color: 'var(--text-muted)',
                    marginTop: '0.25rem',
                  }}
                >
                  {calcPercentage(tn, totalEvaluated)
                    ? `${calcPercentage(tn, totalEvaluated)} of total`
                    : 'Correct ham delivery'}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Summary Footer */}
      {typeof totalEvaluated === 'number' && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '0.5rem',
            paddingTop: '0.5rem',
            borderTop: '1px solid var(--border-color)',
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
          }}
        >
          <div>
            Total Evaluated Samples:{' '}
            <strong style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
              {totalEvaluated.toLocaleString()}
            </strong>
          </div>
          {hasAllCounts && (
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <span>
                Accurate calls:{' '}
                <strong style={{ color: 'var(--color-healthy)' }}>
                  {((tp + tn) / (totalEvaluated || 1) * 100).toFixed(1)}%
                </strong>
              </span>
              <span>
                Errors (FP+FN):{' '}
                <strong style={{ color: 'var(--color-critical)' }}>
                  {((fp + fn) / (totalEvaluated || 1) * 100).toFixed(1)}%
                </strong>
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
