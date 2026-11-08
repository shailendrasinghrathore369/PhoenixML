/**
 * PhoenixML Semantic Design System Tokens
 * Enterprise MLOps Decision-Support Platform
 */

export const colors = {
  // Backgrounds: Deep charcoal / slate
  background: {
    canvas: '#0b0f17',       // Deepest canvas background
    primary: '#0f172a',      // Slate 900 base background
    secondary: '#1e293b',    // Slate 800 elevated container background
    tertiary: '#182234',     // Intermediary neutral shade
  },

  // Surfaces: Layered neutral surfaces
  surface: {
    base: '#0f172a',
    subtle: '#131d2e',
    card: '#1e293b',
    cardHover: '#243247',
    overlay: '#1e293b',
    tableHeader: '#0f172a',
    border: '#334155',
    borderSubtle: '#1e293b',
    borderHover: '#475569',
    muted: '#1e293b',
  },

  // Brand / Primary: Cobalt / Blue
  primary: {
    50: '#eff6ff',
    100: '#dbeafe',
    500: '#3b82f6',
    600: '#2563eb',          // Brand cobalt primary
    700: '#1d4ed8',
    hover: '#1d4ed8',
    active: '#1e40af',
    glow: 'rgba(37, 99, 235, 0.35)',
  },

  // State: Emerald Healthy
  healthy: {
    light: '#ecfdf5',
    base: '#10b981',         // Emerald healthy
    hover: '#059669',
    bg: 'rgba(16, 185, 129, 0.12)',
    border: 'rgba(16, 185, 129, 0.35)',
    glow: 'rgba(16, 185, 129, 0.3)',
  },

  // State: Amber Warning
  warning: {
    light: '#fffbeb',
    base: '#f59e0b',         // Amber warning
    hover: '#d97706',
    bg: 'rgba(245, 158, 11, 0.12)',
    border: 'rgba(245, 158, 11, 0.35)',
    glow: 'rgba(245, 158, 11, 0.3)',
  },

  // State: Rose / Red Critical
  critical: {
    light: '#fff1f2',
    base: '#f43f5e',         // Rose critical
    hover: '#e11d48',
    bg: 'rgba(244, 63, 94, 0.12)',
    border: 'rgba(244, 63, 94, 0.35)',
    glow: 'rgba(244, 63, 94, 0.3)',
  },

  // Text: High-contrast neutral palette (WCAG AAA/AA compliant)
  text: {
    primary: '#f8fafc',      // Slate 50 (highest contrast)
    secondary: '#cbd5e1',    // Slate 300 (contrast >= 4.5:1)
    muted: '#94a3b8',        // Slate 400
    dim: '#64748b',          // Slate 500
    inverse: '#0f172a',      // Dark text on bright backgrounds
  },

  // Status / Decisions
  approval: {
    pending: '#d97706',
    pendingBg: 'rgba(217, 119, 6, 0.14)',
    pendingBorder: 'rgba(217, 119, 6, 0.4)',
    approved: '#059669',
    approvedBg: 'rgba(5, 150, 105, 0.14)',
    approvedBorder: 'rgba(5, 150, 105, 0.4)',
    rejected: '#dc2626',
    rejectedBg: 'rgba(220, 38, 38, 0.14)',
    rejectedBorder: 'rgba(220, 38, 38, 0.4)',
  },
};

/**
 * Light Theme Color Palette (Vercel-inspired high contrast)
 */
export const lightColors = {
  // Backgrounds: Clean, crisp whites and cool slates
  background: {
    canvas: '#f8fafc',       // Slate 50 cool background
    primary: '#ffffff',      // Pure white primary surface
    secondary: '#f1f5f9',    // Slate 100 secondary container
    tertiary: '#e2e8f0',     // Slate 200 elevated container
  },

  // Surfaces: Layered neutral surfaces
  surface: {
    base: '#ffffff',
    subtle: '#f8fafc',
    card: '#ffffff',
    cardHover: '#f8fafc',
    overlay: 'rgba(15, 23, 42, 0.45)',
    tableHeader: '#f1f5f9',
    border: '#e2e8f0',
    borderSubtle: '#f1f5f9',
    borderHover: '#94a3b8',
    muted: '#e2e8f0',
  },

  // Brand / Primary: True Cobalt
  primary: {
    50: '#eff6ff',
    100: '#dbeafe',
    500: '#3b82f6',
    600: '#2563eb',          // Brand cobalt primary
    700: '#1d4ed8',
    hover: '#1d4ed8',
    active: '#1e40af',
    glow: 'rgba(37, 99, 235, 0.15)',
  },

  // State: Emerald Healthy
  healthy: {
    light: '#ecfdf5',
    base: '#059669',         // Emerald healthy (WCAG AA compliant in light)
    hover: '#047857',
    bg: 'rgba(16, 185, 129, 0.10)',
    border: 'rgba(16, 185, 129, 0.30)',
    glow: 'rgba(16, 185, 129, 0.15)',
  },

  // State: Amber Warning
  warning: {
    light: '#fffbeb',
    base: '#d97706',         // Amber warning (WCAG AA compliant in light)
    hover: '#b45309',
    bg: 'rgba(245, 158, 11, 0.10)',
    border: 'rgba(245, 158, 11, 0.30)',
    glow: 'rgba(245, 158, 11, 0.15)',
  },

  // State: Rose / Red Critical
  critical: {
    light: '#fff1f2',
    base: '#e11d48',         // Rose critical (WCAG AA compliant in light)
    hover: '#be123c',
    bg: 'rgba(244, 63, 94, 0.08)',
    border: 'rgba(244, 63, 94, 0.28)',
    glow: 'rgba(244, 63, 94, 0.15)',
  },

  // Text: High-contrast light theme palette (WCAG AAA/AA compliant)
  text: {
    primary: '#0f172a',      // Slate 900
    secondary: '#334155',    // Slate 700
    muted: '#64748b',        // Slate 500
    dim: '#94a3b8',          // Slate 400
    inverse: '#ffffff',      // Light text on dark surfaces
  },

  // Status / Decisions
  approval: {
    pending: '#d97706',
    pendingBg: 'rgba(217, 119, 6, 0.10)',
    pendingBorder: 'rgba(217, 119, 6, 0.35)',
    approved: '#059669',
    approvedBg: 'rgba(5, 150, 105, 0.10)',
    approvedBorder: 'rgba(5, 150, 105, 0.35)',
    rejected: '#dc2626',
    rejectedBg: 'rgba(220, 38, 38, 0.10)',
    rejectedBorder: 'rgba(220, 38, 38, 0.35)',
  },
};

/**
 * Chart Color Palette (Aligned with Section 4.3 in DESIGN.md)
 */
export const chartColors = {
  dark: {
    baseline: '#10b981',       // Emerald
    production: '#3b82f6',     // Cobalt
    shifted: '#f43f5e',        // Rose
    warning: '#f59e0b',        // Amber
    confidence: 'rgba(59, 130, 246, 0.12)',
    grid: 'rgba(255, 255, 255, 0.06)',
  },
  light: {
    baseline: '#059669',
    production: '#2563eb',
    shifted: '#e11d48',
    warning: '#d97706',
    confidence: 'rgba(37, 99, 235, 0.10)',
    grid: '#e2e8f0',
  },
};

/**
 * Theme Definitions
 */
export const themes = {
  dark: {
    id: 'dark',
    name: 'Dark',
    colors,
    charts: chartColors.dark,
  },
  light: {
    id: 'light',
    name: 'Light',
    colors: lightColors,
    charts: chartColors.light,
  },
};

export const typography = {
  fontSans: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif',
  fontMono: 'ui-monospace, SFMono-Regular, "Fira Code", Menlo, Monaco, Consolas, monospace',
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',      // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem',// 30px
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    extrabold: 800,
  },
  lineHeight: {
    none: 1,
    tight: 1.25,
    snug: 1.375,
    normal: 1.5,
    relaxed: 1.625,
  },
};

export const spacing = {
  1: '0.25rem',  // 4px
  2: '0.5rem',   // 8px
  3: '0.75rem',  // 12px
  4: '1rem',     // 16px
  5: '1.25rem',  // 20px
  6: '1.5rem',   // 24px
  8: '2rem',     // 32px
  10: '2.5rem',  // 40px
  12: '3rem',    // 48px
};

export const radii = {
  sm: '4px',
  md: '6px',
  lg: '8px',
  xl: '12px',
  '2xl': '16px',
  full: '9999px',
};

export const shadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -2px rgba(0, 0, 0, 0.4)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -4px rgba(0, 0, 0, 0.5)',
  glowPrimary: '0 0 16px rgba(37, 99, 235, 0.35)',
  glowWarning: '0 0 16px rgba(245, 158, 11, 0.35)',
  glowHealthy: '0 0 16px rgba(16, 185, 129, 0.35)',
  glowCritical: '0 0 16px rgba(244, 63, 94, 0.35)',
};

export const focus = {
  ring: '0 0 0 2px #0f172a, 0 0 0 4px #3b82f6',
  ringHealthy: '0 0 0 2px #0f172a, 0 0 0 4px #10b981',
  ringWarning: '0 0 0 2px #0f172a, 0 0 0 4px #f59e0b',
  ringCritical: '0 0 0 2px #0f172a, 0 0 0 4px #f43f5e',
};
