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

  const Icon = iconMap[type] || Info;
  const safeType = ['success', 'warning', 'error', 'info'].includes(type) ? type : 'info';
  // Use role="alert" for critical errors; role="status" for non-critical notifications to prevent excessive speech interruption
  const ariaRole = type === 'error' ? 'alert' : 'status';

  return (
    <div
      role={ariaRole}
      className={cn('toast-card', safeType)}
    >
      <div className="toast-layout">
        <div className={cn('toast-icon-box', safeType)}>
          <Icon className="icon-sm" />
        </div>
        <div className="toast-content">
          {title && (
            <h5 className="toast-title">
              {title}
            </h5>
          )}
          <p className="toast-message">
            {message}
          </p>
        </div>
        <button
          type="button"
          onClick={() => onDismiss(id)}
          className="toast-close-btn"
          title="Dismiss notification"
          aria-label="Dismiss notification"
        >
          <X className="icon-xs" />
        </button>
      </div>
    </div>
  );
}

export function ToastContainer({ toasts = [], onDismiss }) {
  if (!toasts || toasts.length === 0) return null;

  return (
    <div
      role="region"
      aria-label="Notifications"
      aria-live="polite"
      aria-atomic="false"
      className="toast-container"
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
}
