import React from 'react';
import { cn } from '../lib/utils.js';

export function LoadingState({
  message = 'Loading telemetry & decision metrics...',
  className,
}) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn('state-container loading-state', className)}
    >
      <div className="spinner" aria-hidden="true" />
      <p className="loading-message">
        {message}
      </p>
    </div>
  );
}
