import { describe, it, expect } from 'vitest';
import { colors, typography, spacing, radii, shadows, focus } from '../lib/tokens.js';
import {
  cn,
  formatDate,
  formatMetric,
  getHealthClass,
  getApprovalClass,
  getPriorityClass,
  canPerformActions,
  isViewer,
  isAdmin,
} from '../lib/utils.js';

describe('Design Tokens', () => {
  it('defines dark charcoal/slate backgrounds and neutral surfaces', () => {
    expect(colors.background.canvas).toBe('#0b0f17');
    expect(colors.background.primary).toBe('#0f172a');
    expect(colors.background.secondary).toBe('#1e293b');
    expect(colors.surface.card).toBe('#1e293b');
  });

  it('defines semantic brand cobalt, emerald healthy, amber warning, and rose critical', () => {
    expect(colors.primary[600]).toBe('#2563eb');
    expect(colors.healthy.base).toBe('#10b981');
    expect(colors.warning.base).toBe('#f59e0b');
    expect(colors.critical.base).toBe('#f43f5e');
  });

  it('defines high-contrast text palette', () => {
    expect(colors.text.primary).toBe('#f8fafc');
    expect(colors.text.secondary).toBe('#cbd5e1');
    expect(colors.text.muted).toBe('#94a3b8');
  });

  it('defines typography, spacing, and border radius scales', () => {
    expect(typography.fontSize.xs).toBe('0.75rem');
    expect(typography.fontSize.base).toBe('1rem');
    expect(spacing[4]).toBe('1rem');
    expect(radii.lg).toBe('8px');
    expect(radii.full).toBe('9999px');
  });

  it('defines focus ring tokens', () => {
    expect(focus.ring).toContain('#3b82f6');
  });
});

describe('Utils and Helpers', () => {
  it('cn combines and merges classes cleanly', () => {
    expect(cn('p-4', 'text-white')).toBe('p-4 text-white');
    expect(cn('p-2', 'p-4')).toBe('p-4');
  });

  it('formatDate formats valid and invalid dates safely', () => {
    expect(formatDate(null)).toBe('N/A');
    expect(formatDate('invalid-date')).toBe('N/A');
    expect(formatDate('2026-11-06T10:00:00Z')).not.toBe('N/A');
  });

  it('formatMetric formats numbers safely', () => {
    expect(formatMetric(null)).toBe('N/A');
    expect(formatMetric(undefined)).toBe('N/A');
    expect(formatMetric(NaN)).toBe('N/A');
    expect(formatMetric(0.987654, 3)).toBe('0.988');
    expect(formatMetric(100, 1)).toBe('100.0');
  });

  it('maps health status to semantic classes', () => {
    expect(getHealthClass('HEALTHY')).toBe('healthy');
    expect(getHealthClass('WARNING')).toBe('warning');
    expect(getHealthClass('CRITICAL')).toBe('critical');
    expect(getHealthClass('UNKNOWN')).toBe('insufficient');
  });

  it('maps approval status to semantic classes', () => {
    expect(getApprovalClass('APPROVED')).toBe('approved');
    expect(getApprovalClass('REJECTED')).toBe('rejected');
    expect(getApprovalClass('PENDING')).toBe('pending');
  });

  it('evaluates RBAC roles accurately', () => {
    expect(canPerformActions('ADMIN')).toBe(true);
    expect(canPerformActions('ML_ENGINEER')).toBe(true);
    expect(canPerformActions('VIEWER')).toBe(false);
    expect(isViewer('VIEWER')).toBe(true);
    expect(isViewer('ADMIN')).toBe(false);
    expect(isAdmin('ADMIN')).toBe(true);
  });
});
