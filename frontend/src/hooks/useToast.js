import { useState, useCallback, useMemo } from 'react';

let toastIdCounter = 0;

export function useToast() {
  const [toasts, setToasts] = useState([]);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(({ type = 'info', title = null, message, duration = 6000 }) => {
    let newId = null;

    setToasts((prev) => {
      // Prevent duplicate error or warning notifications with the same message
      if ((type === 'error' || type === 'warning') && prev.some((t) => t.type === type && t.message === message)) {
        return prev;
      }
      newId = ++toastIdCounter;
      return [...prev, { id: newId, type, title, message, duration, createdAt: Date.now() }];
    });

    if (duration > 0 && newId) {
      const scheduledId = newId;
      setTimeout(() => {
        dismissToast(scheduledId);
      }, duration);
    }

    return newId;
  }, [dismissToast]);

  const success = useCallback((message, title = 'Success') => {
    return addToast({ type: 'success', title, message });
  }, [addToast]);

  const error = useCallback((message, title = 'Error') => {
    return addToast({ type: 'error', title, message, duration: 8000 });
  }, [addToast]);

  const warning = useCallback((message, title = 'Warning') => {
    return addToast({ type: 'warning', title, message, duration: 7000 });
  }, [addToast]);

  const info = useCallback((message, title = 'Notice') => {
    return addToast({ type: 'info', title, message });
  }, [addToast]);

  return useMemo(() => ({
    toasts,
    addToast,
    dismissToast,
    success,
    error,
    warning,
    info,
  }), [toasts, addToast, dismissToast, success, error, warning, info]);
}
