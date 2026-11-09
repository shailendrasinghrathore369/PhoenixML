import { useState, useEffect, useCallback } from 'react';

export const VALID_VIEWS = ['dashboard', 'models', 'approvals', 'telemetry', 'audit'];

export function parseViewFromHash() {
  if (typeof window === 'undefined') return 'dashboard';
  const clean = window.location.hash.replace(/^#\/?/, '').trim().toLowerCase();
  return VALID_VIEWS.includes(clean) ? clean : 'dashboard';
}

export function useNavigation(defaultView = 'dashboard') {
  const [currentView, setCurrentViewInternal] = useState(() => {
    return parseViewFromHash() || defaultView;
  });

  const navigateTo = useCallback((viewId) => {
    if (!VALID_VIEWS.includes(viewId)) return;
    setCurrentViewInternal(viewId);
    if (typeof window !== 'undefined') {
      const targetHash = `#/${viewId}`;
      if (window.location.hash !== targetHash) {
        window.location.hash = targetHash;
      }
    }
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Ensure initial hash matches currentView if hash is empty
    if (!window.location.hash) {
      window.location.hash = `#/${currentView}`;
    }

    const handleHashChange = () => {
      const newView = parseViewFromHash();
      setCurrentViewInternal(newView);
    };

    window.addEventListener('hashchange', handleHashChange);
    window.addEventListener('popstate', handleHashChange);

    return () => {
      window.removeEventListener('hashchange', handleHashChange);
      window.removeEventListener('popstate', handleHashChange);
    };
  }, [currentView]);

  return {
    currentView,
    navigateTo,
    validViews: VALID_VIEWS,
  };
}
