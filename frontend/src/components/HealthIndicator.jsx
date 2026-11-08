import React from 'react';
import { cn, formatMetric, getHealthClass } from '../lib/utils.js';

export function HealthIndicator({ score, status, showLabel = true, className }) {
  const numScore = score !== null && score !== undefined ? Math.max(0, Math.min(100, Number(score))) : 0;
  const hasScore = score !== null && score !== undefined && !isNaN(score);
  const healthStatus = status || (hasScore ? (numScore >= 80 ? 'HEALTHY' : numScore >= 60 ? 'WARNING' : 'CRITICAL') : 'NO_DATA');
  const healthClass = getHealthClass(healthStatus);

  return (
    <div className={cn('health-meter', className)}>
      {showLabel && (
        <div className="health-meter-labels">
          <span className="health-meter-title">System Health</span>
          <span className="health-meter-val">
            {hasScore ? `${formatMetric(score, 1)} / 100` : 'NO_DATA'}
          </span>
        </div>
      )}
      <div
        className="meter-track"
        role="progressbar"
        aria-valuenow={hasScore ? numScore : 0}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Model Health Score"
      >
        <div
          className={cn('meter-bar', healthClass)}
          style={{ width: `${hasScore ? numScore : 0}%` }}
        />
      </div>
    </div>
  );
}
