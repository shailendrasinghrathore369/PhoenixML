import React, { useEffect, useRef } from 'react';
import { X, AlertTriangle } from 'lucide-react';
import { cn } from '../lib/utils.js';

export function ConfirmationDialog({
  isOpen,
  onClose,
  onConfirm,
  title = 'Confirm Action',
  description = 'Are you sure you want to proceed with this operation?',
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  confirmVariant = 'primary', // 'primary' | 'success' | 'danger'
  loading = false,
  children,
}) {
  const dialogRef = useRef(null);
  const previouslyFocusedElement = useRef(null);

  // Focus trap, initial focus, and focus return
  useEffect(() => {
    if (!isOpen) return;

    // Save invoking element
    previouslyFocusedElement.current = document.activeElement;

    // Focus the first focusable element inside the dialog after mount
    const timer = setTimeout(() => {
      if (!dialogRef.current) return;
      const focusable = dialogRef.current.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );
      if (focusable.length > 0) {
        focusable[0].focus();
      } else {
        dialogRef.current.focus();
      }
    }, 0);

    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && !loading) {
        e.preventDefault();
        onClose();
        return;
      }

      if (e.key === 'Tab' && dialogRef.current) {
        const focusable = dialogRef.current.querySelectorAll(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        if (focusable.length === 0) return;

        const firstElement = focusable[0];
        const lastElement = focusable[focusable.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      clearTimeout(timer);
      window.removeEventListener('keydown', handleKeyDown);
      // Restore focus to invoking element
      if (previouslyFocusedElement.current && typeof previouslyFocusedElement.current.focus === 'function') {
        previouslyFocusedElement.current.focus();
      }
    };
  }, [isOpen, loading, onClose]);

  if (!isOpen) return null;

  const confirmVariantClass = {
    primary: 'btn-primary',
    success: 'btn-success',
    danger: 'btn-danger',
  }[confirmVariant] || 'btn-primary';

  const iconVariantClass = {
    primary: 'primary',
    success: 'success',
    danger: 'danger',
  }[confirmVariant] || 'primary';

  return (
    <div
      className="dialog-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="dialog-title"
      aria-describedby="dialog-description"
      onClick={(e) => {
        if (e.target === e.currentTarget && !loading) {
          onClose();
        }
      }}
    >
      <div
        ref={dialogRef}
        className="dialog-card"
        onClick={(e) => e.stopPropagation()}
        tabIndex={-1}
      >
        <div className="dialog-header">
          <div className="dialog-title-group">
            <div className={cn('dialog-icon-box', iconVariantClass)}>
              <AlertTriangle className="icon-md" />
            </div>
            <h2 id="dialog-title" className="dialog-title">
              {title}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="dialog-close-btn"
            title="Close dialog"
            aria-label="Close dialog"
          >
            <X className="icon-sm" />
          </button>
        </div>

        <p id="dialog-description" className="dialog-description">
          {description}
        </p>

        {children && <div className="dialog-body">{children}</div>}

        <div className="dialog-actions">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="btn btn-outline"
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={loading}
            className={cn('btn', confirmVariantClass)}
          >
            {loading && <span className="dialog-btn-spinner" aria-hidden="true" />}
            <span>{loading ? 'Processing...' : confirmText}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
