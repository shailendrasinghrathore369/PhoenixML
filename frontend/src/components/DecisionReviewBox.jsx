import React, { useState } from 'react';
import { AlertCircle, CheckCircle, XCircle, Lock, ShieldCheck, HelpCircle } from 'lucide-react';
import { StatusBadge } from './StatusBadge.jsx';
import { ConfirmationDialog } from './ConfirmationDialog.jsx';
import { cn, formatDate, formatMetric, getApprovalClass, getPriorityClass } from '../lib/utils.js';

export function DecisionReviewBox({
  decision,
  modelName,
  userRole,
  onApprove,
  onReject,
  actionLoading,
  className,
}) {
  const [confirmDialog, setConfirmDialog] = useState(null); // { type: 'approve' | 'reject' } | null

  if (!decision) return null;

  const isPending = decision.approval_status === 'PENDING';
  const isViewer = userRole === 'VIEWER';
  const isLoading = actionLoading === `approval-${decision.id}`;

  const handleOpenApprove = () => {
    setConfirmDialog({ type: 'approve' });
  };

  const handleOpenReject = () => {
    setConfirmDialog({ type: 'reject' });
  };

  const handleConfirmAction = async () => {
    if (!confirmDialog) return;
    if (confirmDialog.type === 'approve') {
      await onApprove(decision);
    } else {
      await onReject(decision);
    }
    setConfirmDialog(null);
  };

  return (
    <div
      className={cn(
        'decision-box p-6 rounded-xl border bg-slate-900/90 text-slate-100 shadow-md transition-all mb-6',
        isPending
          ? 'highlight border-amber-500/40 bg-gradient-to-b from-slate-900 to-amber-950/10 shadow-[0_0_20px_rgba(245,158,11,0.08)]'
          : 'border-slate-800',
        className
      )}
    >
      <div className="decision-header flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2.5 flex-wrap mb-1.5">
            <span className="decision-action-title text-lg font-bold text-slate-100">
              {decision.recommended_action}
            </span>
            <StatusBadge variant={getPriorityClass(decision.priority)} size="sm">
              Priority: {decision.priority}
            </StatusBadge>
            <StatusBadge variant={getApprovalClass(decision.approval_status)} size="sm">
              {decision.approval_status}
            </StatusBadge>
          </div>
          <div className="text-xs text-slate-400 font-mono">
            Model: {modelName || decision.model_id} · Decision ID: {decision.id} · Evaluated: {formatDate(decision.created_at)}
          </div>
        </div>
      </div>

      <div className="decision-rationale text-xs text-slate-300 leading-relaxed bg-slate-950/50 p-3.5 rounded-lg border border-slate-800/80 mb-3">
        <strong className="text-slate-100 font-semibold">Rationale: </strong>
        <span>{decision.rationale || 'No rationale recorded.'}</span>
      </div>

      {decision.explanation && (
        <div className="decision-rationale text-xs text-slate-400 italic bg-slate-950/30 p-3.5 rounded-lg border border-slate-800/50 mb-4">
          <strong className="text-slate-300 font-medium not-italic">Explanation: </strong>
          <span>{decision.explanation}</span>
        </div>
      )}

      <div className="decision-details-grid grid grid-cols-2 md:grid-cols-4 gap-3 p-3.5 rounded-lg bg-slate-950/40 border border-slate-800/60 mb-5 text-xs">
        <div>
          <div className="decision-detail-label text-slate-400 mb-1">Health Score at Decision</div>
          <div className="decision-detail-val font-semibold font-mono text-slate-100">
            {decision.health_score !== null && decision.health_score !== undefined
              ? `${formatMetric(decision.health_score, 1)} (${decision.health_status})`
              : 'N/A'}
          </div>
        </div>
        <div>
          <div className="decision-detail-label text-slate-400 mb-1">Confidence Score</div>
          <div className="decision-detail-val font-semibold font-mono text-slate-100">
            {decision.confidence !== null && decision.confidence !== undefined
              ? `${(decision.confidence * 100).toFixed(1)}%`
              : 'N/A'}
          </div>
        </div>
        <div>
          <div className="decision-detail-label text-slate-400 mb-1">Requires Human Approval</div>
          <div
            className={cn(
              'decision-detail-val font-semibold',
              decision.requires_human_approval ? 'text-amber-400' : 'text-emerald-400'
            )}
          >
            {decision.requires_human_approval ? 'YES (Mandatory)' : 'NO'}
          </div>
        </div>
        <div>
          <div className="decision-detail-label text-slate-400 mb-1">Approval Status</div>
          <div className="decision-detail-val">
            <StatusBadge variant={getApprovalClass(decision.approval_status)} size="sm">
              {decision.approval_status}
            </StatusBadge>
          </div>
        </div>
      </div>

      {/* Action Controls */}
      {isPending && (
        <div className="approval-actions flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
          {isViewer && (
            <div className="flex items-center gap-1.5 text-xs text-slate-400 mr-auto">
              <Lock className="w-3.5 h-3.5 text-slate-400" />
              <span>Viewers have read-only access. ML_ENGINEER or ADMIN required to approve/reject.</span>
            </div>
          )}

          <button
            type="button"
            className="btn btn-danger inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-rose-600/90 hover:bg-rose-600 text-white transition-colors disabled:opacity-50 focus:ring-2 focus:ring-rose-500/50"
            onClick={handleOpenReject}
            disabled={isViewer || isLoading}
            title={isViewer ? 'Viewers cannot reject recommendations' : 'Reject this recommendation'}
          >
            <XCircle className="w-4 h-4" />
            <span>{isLoading ? 'Processing...' : '✕ Reject Recommendation'}</span>
          </button>

          <button
            type="button"
            className="btn btn-success inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-emerald-600/90 hover:bg-emerald-600 text-white transition-colors disabled:opacity-50 focus:ring-2 focus:ring-emerald-500/50"
            onClick={handleOpenApprove}
            disabled={isViewer || isLoading}
            title={isViewer ? 'Viewers cannot approve recommendations' : 'Approve this recommendation'}
          >
            <CheckCircle className="w-4 h-4" />
            <span>{isLoading ? 'Processing...' : '✓ Approve Recommendation'}</span>
          </button>
        </div>
      )}

      {/* Confirmation Modal Dialog */}
      <ConfirmationDialog
        isOpen={!!confirmDialog}
        onClose={() => setConfirmDialog(null)}
        onConfirm={handleConfirmAction}
        loading={isLoading}
        title={confirmDialog?.type === 'approve' ? 'Approve AIMD Recommendation?' : 'Reject AIMD Recommendation?'}
        description={
          confirmDialog?.type === 'approve'
            ? `You are authorizing the automated maintenance recommendation: "${decision.recommended_action}". This action will be logged in the immutable audit trail.`
            : `You are declining the recommendation: "${decision.recommended_action}". This decision will be logged as REJECTED in the audit log.`
        }
        confirmText={confirmDialog?.type === 'approve' ? 'Yes, Authorize Action' : 'Yes, Reject Action'}
        confirmVariant={confirmDialog?.type === 'approve' ? 'success' : 'danger'}
      />
    </div>
  );
}
