import React from 'react';
import { cn } from '../lib/utils.js';

export function PageHeader({
  title,
  subtitle,
  icon: Icon,
  badge,
  actions,
  className,
}) {
  return (
    <div className={cn('page-header', className)}>
      <div className="page-header-main">
        {Icon && (
          <div className="page-header-icon-box" aria-hidden="true">
            <Icon className="icon-md" />
          </div>
        )}
        <div className="page-header-text">
          <div className="page-header-title-row">
            <h1 className="page-header-title">{title}</h1>
            {badge && <div className="page-header-badge-wrap">{badge}</div>}
          </div>
          {subtitle && (
            <p className="page-header-subtitle">{subtitle}</p>
          )}
        </div>
      </div>

      {actions && (
        <div className="page-header-actions">
          {actions}
        </div>
      )}
    </div>
  );
}
