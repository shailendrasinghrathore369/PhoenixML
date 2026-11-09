import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { cn } from '../lib/utils.js';

export function ErrorState({
  title = 'An error occurred',
  message,
  onRetry,
  className,
}) {
  return (
    <div
      role="alert"
      className={cn(
        'flex items-start gap-3.5 p-4 rounded-xl border border-rose-500/30 bg-rose-950/20 text-rose-200 text-xs shadow-sm',
        className
      )}
    >
      <div className="p-1 rounded-md bg-rose-500/20 text-rose-400 mt-0.5 flex-shrink-0">
        <AlertCircle className="w-4 h-4" />
      </div>
      <div className="flex-1">
        <h4 className="font-semibold text-rose-300 mb-0.5">{title}</h4>
        <p className="text-rose-200/90 leading-relaxed">{message}</p>
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md border border-rose-500/40 text-rose-300 hover:bg-rose-500/20 transition-colors flex-shrink-0"
        >
          <RefreshCw className="w-3 h-3" />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
}
