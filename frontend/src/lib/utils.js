import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Combines conditional class names cleanly with Tailwind merge support.
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

/**
 * Cleanly format ISO date/time strings for enterprise tables and logs.
 */
export function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  try {
    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? 'N/A' : d.toLocaleString();
  } catch {
    return 'N/A';
  }
}

/**
 * Format numeric metric values to fixed precision safely.
 */
export function formatMetric(val, decimals = 4) {
  if (val === null || val === undefined || isNaN(val)) return 'N/A';
  return Number(val).toFixed(decimals);
}

/**
 * Maps system health string to semantic styling token class.
 */
export function getHealthClass(status) {
  if (!status) return 'insufficient';
  const s = String(status).toUpperCase();
  if (s === 'HEALTHY') return 'healthy';
  if (s === 'WARNING') return 'warning';
  if (s === 'CRITICAL') return 'critical';
  return 'insufficient';
}

/**
 * Maps decision approval string to semantic styling token class.
 */
export function getApprovalClass(status) {
  if (!status) return 'pending';
  const s = String(status).toUpperCase();
  if (s === 'APPROVED') return 'approved';
  if (s === 'REJECTED') return 'rejected';
  return 'pending';
}

/**
 * Maps priority string to semantic styling token class.
 */
export function getPriorityClass(priority) {
  if (!priority) return 'neutral';
  const p = String(priority).toUpperCase();
  if (p === 'CRITICAL') return 'critical';
  if (p === 'HIGH') return 'warning';
  if (p === 'MEDIUM') return 'info';
  return 'neutral';
}

/**
 * RBAC Helper: Check if current role has execution permissions (ML_ENGINEER or ADMIN).
 */
export function canPerformActions(role) {
  if (!role) return false;
  const r = String(role).toUpperCase();
  return r === 'ADMIN' || r === 'ML_ENGINEER';
}

/**
 * RBAC Helper: Check if user is an ADMIN.
 */
export function isAdmin(role) {
  return String(role).toUpperCase() === 'ADMIN';
}

/**
 * RBAC Helper: Check if user is restricted to read-only VIEWER.
 */
export function isViewer(role) {
  return String(role).toUpperCase() === 'VIEWER';
}
