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
      className={cn(
        'state-container flex flex-col items-center justify-center p-12 text-center',
        className
      )}
    >
      <div className="spinner w-8 h-8 rounded-full border-2 border-slate-700 border-t-blue-500 animate-spin mb-4" />
      <p className="text-xs text-slate-400 font-medium tracking-wide">
        {message}
      </p>
    </div>
  );
}
