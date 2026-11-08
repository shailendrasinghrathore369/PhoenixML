import React from 'react';
import { cn, formatMetric, getHealthClass } from '../lib/utils.js';

export function HealthIndicator({ score, status, showLabel = true, className }) {
  const numScore = score !== null && score !== undefined ? Math.max(0, Math.min(100, Number(score))) : 0;
  const hasScore = score !== null && score !== undefined && !isNaN(score);
  const healthStatus = status || (hasScore ? (numScore >= 80 ? 'HEALTHY' : numScore >= 60 ? 'WARNING' : 'CRITICAL') : 'NO_DATA');
  const healthClass = getHealthClass(healthStatus);

  const barColor = {
    healthy: 'bg-emerald-500',
    warning: 'bg-amber-500',
    critical: 'bg-rose-500',
    insufficient: 'bg-slate-600',
  }[healthClass] || 'bg-slate-600';

  return (
    <div className={cn('w-full', className)}>
      {showLabel && (
        <div className="flex justify-between items-center text-xs mb-1.5">
          <span className="text-slate-400 font-medium">System Health</span>
          <span className="text-slate-200 font-semibold font-mono">
            {hasScore ? `${formatMetric(score, 1)} / 100` : 'NO_DATA'}
          </span>
        </div>
      )}
      <div
        className="w-full h-2 bg-slate-800 rounded-full overflow-hidden border border-slate-700/60"
        role="progressbar"
        aria-valuenow={hasScore ? numScore : 0}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Model Health Score"
      >
        <div
          className={cn('h-full transition-all duration-500 ease-out rounded-full', barColor)}
          style={{ width: `${hasScore ? numScore : 0}%` }}
        />
      </div>
    </div>
  );
}
