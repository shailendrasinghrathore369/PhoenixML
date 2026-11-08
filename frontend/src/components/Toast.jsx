import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from 'lucide-react';
import { cn } from '../lib/utils.js';

export function ToastItem({ toast, onDismiss }) {
  const { id, type = 'info', title, message } = toast;

  const iconMap = {
    success: CheckCircle2,
    warning: AlertTriangle,
    error: XCircle,
    info: Info,
  };

  const styleMap = {
    success: 'border-emerald-500/30 bg-slate-900/95 text-slate-100 shadow-[0_4px_16px_rgba(16,185,129,0.15)]',
    warning: 'border-amber-500/30 bg-slate-900/95 text-slate-100 shadow-[0_4px_16px_rgba(245,158,11,0.15)]',
    error: 'border-rose-500/30 bg-slate-900/95 text-slate-100 shadow-[0_4px_16px_rgba(244,63,94,0.15)]',
    info: 'border-blue-500/30 bg-slate-900/95 text-slate-100 shadow-[0_4px_16px_rgba(37,99,235,0.15)]',
  };

  const iconColorMap = {
    success: 'text-emerald-400 bg-emerald-500/15',
    warning: 'text-amber-400 bg-amber-500/15',
    error: 'text-rose-400 bg-rose-500/15',
    info: 'text-blue-400 bg-blue-500/15',
  };

  const Icon = iconMap[type] || Info;

  return (
    <div
      role="alert"
      className={cn(
        'w-80 md:w-96 rounded-xl border p-4 backdrop-blur-md transition-all duration-300 relative overflow-hidden',
        'animate-in slide-in-from-top-2 fade-in duration-200',
        styleMap[type] || styleMap.info
      )}
    >
      <div className="flex items-start gap-3">
        <div className={cn('p-1.5 rounded-lg flex-shrink-0 mt-0.5', iconColorMap[type])}>
          <Icon className="w-4 h-4" />
        </div>
        <div className="flex-1 pr-2">
          {title && (
            <h5 className="text-xs font-semibold text-slate-100 mb-0.5">
              {title}
            </h5>
          )}
          <p className="text-xs text-slate-300 leading-relaxed break-words">
            {message}
          </p>
        </div>
        <button
          type="button"
          onClick={() => onDismiss(id)}
          className="text-slate-400 hover:text-slate-100 p-1 rounded hover:bg-slate-800/80 transition-colors"
          title="Dismiss notification"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}

export function ToastContainer({ toasts = [], onDismiss }) {
  if (!toasts || toasts.length === 0) return null;

  return (
    <div
      aria-live="polite"
      className="fixed top-4 right-4 z-50 flex flex-col gap-2.5 max-w-full pointer-events-auto"
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
}
