import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../hooks/useTheme.js';
import { cn } from '../lib/utils.js';

/**
 * Accessible PhoenixML Theme Toggle Component
 *
 * Supports keyboard navigation, screen reader announcements,
 * and clear visual state indication.
 */
export function ThemeToggle({ className, showLabel = false, size = 'sm' }) {
  const { theme, isDark, toggleTheme } = useTheme();

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggleTheme();
    }
  };

  const nextThemeLabel = isDark ? 'light' : 'dark';
  const currentThemeLabel = isDark ? 'Dark' : 'Light';
  const labelText = `Switch to ${nextThemeLabel} theme (currently ${currentThemeLabel})`;

  return (
    <button
      type="button"
      onClick={toggleTheme}
      onKeyDown={handleKeyDown}
      className={cn(
        'theme-toggle-btn btn btn-outline',
        size === 'sm' && 'btn-sm',
        'relative inline-flex items-center gap-2 transition-colors duration-200 select-none',
        className
      )}
      aria-label={labelText}
      title={labelText}
      data-testid="theme-toggle"
      data-current-theme={theme}
    >
      <span className="theme-toggle-icon-wrap flex items-center justify-center" aria-hidden="true">
        {isDark ? (
          <Sun className="icon-sm text-amber-400 transition-transform duration-200 hover:rotate-45" />
        ) : (
          <Moon className="icon-sm text-blue-600 transition-transform duration-200 hover:-rotate-12" />
        )}
      </span>

      {showLabel && (
        <span className="theme-toggle-label text-xs font-medium">
          {currentThemeLabel}
        </span>
      )}

      {/* Accessible active theme pill */}
      <span className="theme-indicator-dot" aria-hidden="true" />
    </button>
  );
}

export default ThemeToggle;
