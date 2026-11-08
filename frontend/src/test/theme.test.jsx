import React from 'react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, renderHook, act } from '@testing-library/react';
import {
  ThemeProvider,
  useTheme,
  THEME_STORAGE_KEY,
  DEFAULT_THEME,
  validateTheme,
  getInitialTheme,
  applyThemeToDom,
} from '../context/ThemeContext.jsx';
import { ThemeToggle } from '../components/ThemeToggle.jsx';
import { lightColors, chartColors, themes } from '../lib/tokens.js';

describe('Theme Validation & Persistence Helpers', () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
    document.documentElement.style.colorScheme = '';
  });

  afterEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  it('validateTheme validates valid themes accurately', () => {
    expect(validateTheme('dark')).toBe('dark');
    expect(validateTheme('light')).toBe('light');
    expect(validateTheme('DARK')).toBe('dark');
    expect(validateTheme('Light ')).toBe('light');
  });

  it('validateTheme falls back safely to DEFAULT_THEME for invalid inputs', () => {
    expect(validateTheme(null)).toBe(DEFAULT_THEME);
    expect(validateTheme(undefined)).toBe(DEFAULT_THEME);
    expect(validateTheme('')).toBe(DEFAULT_THEME);
    expect(validateTheme('system')).toBe(DEFAULT_THEME);
    expect(validateTheme('blue')).toBe(DEFAULT_THEME);
    expect(validateTheme(123)).toBe(DEFAULT_THEME);
  });

  it('getInitialTheme retrieves stored theme or defaults to dark', () => {
    expect(getInitialTheme()).toBe('dark');

    window.localStorage.setItem(THEME_STORAGE_KEY, 'light');
    expect(getInitialTheme()).toBe('light');

    window.localStorage.setItem(THEME_STORAGE_KEY, 'corrupted_theme');
    expect(getInitialTheme()).toBe('dark');
  });

  it('getInitialTheme handles localStorage access exceptions gracefully', () => {
    vi.spyOn(window.localStorage, 'getItem').mockImplementation(() => {
      throw new Error('SecurityError: Access Denied');
    });
    expect(getInitialTheme()).toBe(DEFAULT_THEME);
  });

  it('applyThemeToDom sets data-theme attribute and colorScheme', () => {
    applyThemeToDom('light');
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    expect(document.documentElement.style.colorScheme).toBe('light');

    applyThemeToDom('dark');
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    expect(document.documentElement.style.colorScheme).toBe('dark');

    applyThemeToDom('invalid');
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });
});

describe('ThemeProvider & useTheme Hook', () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
    document.documentElement.style.colorScheme = '';
  });

  afterEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  it('initializes to dark theme by default and sets document data-theme', () => {
    const wrapper = ({ children }) => <ThemeProvider>{children}</ThemeProvider>;
    const { result } = renderHook(() => useTheme(), { wrapper });

    expect(result.current.theme).toBe('dark');
    expect(result.current.isDark).toBe(true);
    expect(result.current.isLight).toBe(false);
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });

  it('respects valid pre-existing localStorage theme', () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, 'light');
    const wrapper = ({ children }) => <ThemeProvider>{children}</ThemeProvider>;
    const { result } = renderHook(() => useTheme(), { wrapper });

    expect(result.current.theme).toBe('light');
    expect(result.current.isLight).toBe(true);
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  it('switches theme and persists to localStorage on toggleTheme', () => {
    const wrapper = ({ children }) => <ThemeProvider>{children}</ThemeProvider>;
    const { result } = renderHook(() => useTheme(), { wrapper });

    expect(result.current.theme).toBe('dark');

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.theme).toBe('light');
    expect(result.current.isLight).toBe(true);
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('light');
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');

    act(() => {
      result.current.toggleTheme();
    });

    expect(result.current.theme).toBe('dark');
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark');
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });

  it('setTheme validates and applies theme', () => {
    const wrapper = ({ children }) => <ThemeProvider>{children}</ThemeProvider>;
    const { result } = renderHook(() => useTheme(), { wrapper });

    act(() => {
      result.current.setTheme('light');
    });
    expect(result.current.theme).toBe('light');

    // Setting invalid theme falls back to default 'dark'
    act(() => {
      result.current.setTheme('neon-pink');
    });
    expect(result.current.theme).toBe('dark');
  });

  it('throws an error if useTheme is used outside of ThemeProvider', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => renderHook(() => useTheme())).toThrow('useTheme must be used within a <ThemeProvider>');
    consoleError.mockRestore();
  });
});

describe('ThemeToggle Component', () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
  });

  afterEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  it('renders accessible theme toggle with correct initial aria attributes', () => {
    render(
      <ThemeProvider initialTheme="dark">
        <ThemeToggle />
      </ThemeProvider>
    );

    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute('data-current-theme', 'dark');
    expect(button).toHaveAttribute('aria-label', expect.stringContaining('Switch to light theme'));
    expect(button).toHaveAttribute('title', expect.stringContaining('Switch to light theme'));
  });

  it('toggles theme when clicked', () => {
    render(
      <ThemeProvider initialTheme="dark">
        <ThemeToggle />
      </ThemeProvider>
    );

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('data-current-theme', 'dark');

    fireEvent.click(button);

    expect(button).toHaveAttribute('data-current-theme', 'light');
    expect(button).toHaveAttribute('aria-label', expect.stringContaining('Switch to dark theme'));
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('light');
  });

  it('toggles theme via keyboard Enter and Space keys', () => {
    render(
      <ThemeProvider initialTheme="dark">
        <ThemeToggle />
      </ThemeProvider>
    );

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('data-current-theme', 'dark');

    // Press Enter
    fireEvent.keyDown(button, { key: 'Enter' });
    expect(button).toHaveAttribute('data-current-theme', 'light');

    // Press Space
    fireEvent.keyDown(button, { key: ' ' });
    expect(button).toHaveAttribute('data-current-theme', 'dark');
  });

  it('renders visible label when showLabel is true', () => {
    render(
      <ThemeProvider initialTheme="dark">
        <ThemeToggle showLabel={true} />
      </ThemeProvider>
    );

    expect(screen.getByText('Dark')).toBeInTheDocument();
  });
});

describe('Dual-Theme Tokens & Design System Alignment', () => {
  it('defines light theme semantic backgrounds and surfaces', () => {
    expect(lightColors.background.canvas).toBe('#f8fafc');
    expect(lightColors.background.primary).toBe('#ffffff');
    expect(lightColors.background.secondary).toBe('#f1f5f9');
    expect(lightColors.surface.card).toBe('#ffffff');
    expect(lightColors.text.primary).toBe('#0f172a');
  });

  it('defines light theme status colors with required contrast', () => {
    expect(lightColors.healthy.base).toBe('#059669');
    expect(lightColors.warning.base).toBe('#d97706');
    expect(lightColors.critical.base).toBe('#e11d48');
    expect(lightColors.primary[600]).toBe('#2563eb');
  });

  it('defines chart color palettes for dark and light themes', () => {
    expect(chartColors.dark.baseline).toBe('#10b981');
    expect(chartColors.dark.shifted).toBe('#f43f5e');
    expect(chartColors.light.baseline).toBe('#059669');
    expect(chartColors.light.shifted).toBe('#e11d48');
  });

  it('exports valid themes map', () => {
    expect(themes.dark.id).toBe('dark');
    expect(themes.light.id).toBe('light');
  });
});
