import React from 'react';
import { cn } from '../lib/utils.js';

export function StatusBadge({
  variant = 'neutral',
  children,
  className,
  dot = true,
  icon: Icon,
  size = 'md',
}) {
  const normalizedVariant = String(variant).toLowerCase();
  const sizeClass = size === 'sm' ? 'status-badge-sm' : 'status-badge-md';

  return (
    <span
      className={cn(
        'status-badge',
        normalizedVariant,
        sizeClass,
        className
      )}
    >
      {Icon && <Icon className="icon-xs" aria-hidden="true" />}
      {!Icon && dot && (
        <span className={cn('status-dot', normalizedVariant)} aria-hidden="true" />
      )}
      <span>{children}</span>
    </span>
  );
}
