import React from 'react';
import { cn } from '../lib/utils.js';

export function MetricCard({
  title,
  value,
  subtext,
  badge,
  icon: Icon,
  highlight = false,
  className,
  onClick,
}) {
  return (
    <div
      onClick={onClick}
      className={cn(
        'kpi-card',
        highlight ? 'highlight-pending border-amber-500' : '',
        onClick && 'cursor-pointer',
        className
      )}
    >
      <div className="kpi-header">
        <div className="kpi-title-wrap">
          {Icon && (
            <div className={cn('kpi-icon-box', highlight ? 'highlight' : 'primary')}>
              <Icon className="icon-sm" aria-hidden="true" />
            </div>
          )}
          <span className="kpi-title">{title}</span>
        </div>
        {badge && <div className="kpi-badge-wrap">{badge}</div>}
      </div>

      <div className="kpi-value-wrap">
        <div className={cn('kpi-value', highlight && 'highlight')}>
          {value}
        </div>
      </div>

      {subtext && (
        <div className="kpi-sub">
          {subtext}
        </div>
      )}
    </div>
  );
}
