import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';

export const THEME_STORAGE_KEY = 'phoenixml-theme';
export const VALID_THEMES = ['dark', 'light'];
export const DEFAULT_THEME = 'dark';

/**
 * Validates a theme string safely, returning DEFAULT_THEME ('dark') if invalid.
 *
 * @param {string | null | undefined} val
 * @returns {'dark' | 'light'}
 */
export function validateTheme(val) {
  if (val && typeof val === 'string') {
    const normalized = val.toLowerCase().trim();
    if (VALID_THEMES.includes(normalized)) {
      return normalized;
    }
  }
  return DEFAULT_THEME;
}

/**
 * Retrieves the initial theme from localStorage with safe fallback to DEFAULT_THEME.
 *
 * @returns {'dark' | 'light'}
 */
export function getInitialTheme() {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      const stored = window.localStorage.getItem(THEME_STORAGE_KEY);
      return validateTheme(stored);
    }
  } catch (err) {
    // Graceful fallback on storage access restrictions
    console.warn('[PhoenixML Theme] Failed to access localStorage:', err);
  }
  return DEFAULT_THEME;
}

/**
 * Applies the given theme to the document root element.
 *
 * @param {'dark' | 'light'} theme
 */
export function applyThemeToDom(theme) {
  if (typeof document !== 'undefined' && document.documentElement) {
    const validTheme = validateTheme(theme);
    document.documentElement.setAttribute('data-theme', validTheme);
    document.documentElement.style.colorScheme = validTheme;
  }
}

const ThemeContext = createContext(null);

export function ThemeProvider({ children, initialTheme }) {
  const [theme, setThemeState] = useState(() => {
    if (initialTheme !== undefined) {
      return validateTheme(initialTheme);
    }
    return getInitialTheme();
  });

  // Apply theme to DOM on mount and when theme changes
  useEffect(() => {
    applyThemeToDom(theme);
  }, [theme]);

  // Set theme safely with validation and persistence
  const setTheme = useCallback((newTheme) => {
    const valid = validateTheme(newTheme);
    setThemeState(valid);
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        window.localStorage.setItem(THEME_STORAGE_KEY, valid);
      }
    } catch (err) {
      console.warn('[PhoenixML Theme] Failed to persist theme to localStorage:', err);
    }
    applyThemeToDom(valid);
  }, []);

  // Toggle between dark and light
  const toggleTheme = useCallback(() => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  }, [theme, setTheme]);

  const value = useMemo(() => ({
    theme,
    isDark: theme === 'dark',
    isLight: theme === 'light',
    toggleTheme,
    setTheme,
    themes: VALID_THEMES,
  }), [theme, toggleTheme, setTheme]);

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

/**
 * Hook to consume PhoenixML theme context.
 *
 * @returns {{
 *   theme: 'dark' | 'light',
 *   isDark: boolean,
 *   isLight: boolean,
 *   toggleTheme: () => void,
 *   setTheme: (t: string) => void,
 *   themes: string[]
 * }}
 */
export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error('useTheme must be used within a <ThemeProvider>');
  }
  return ctx;
}

export default ThemeContext;
