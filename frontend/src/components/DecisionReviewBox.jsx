import React, { useState } from 'react';
import { CheckCircle, XCircle, Lock } from 'lucide-react';
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
      className={cn('decision-box', isPending && 'highlight', className)}
    >
      <div className="decision-header">
        <div>
          <div className="decision-title-group">
            <span className="decision-action-title">
              {decision.recommended_action}
            </span>
            <StatusBadge variant={getPriorityClass(decision.priority)} size="sm">
              Priority: {decision.priority}
            </StatusBadge>
            <StatusBadge variant={getApprovalClass(decision.approval_status)} size="sm">
              {decision.approval_status}
            </StatusBadge>
          </div>
          <div className="decision-meta">
            Model: {modelName || decision.model_id} · Decision ID: {decision.id} · Evaluated: {formatDate(decision.created_at)}
          </div>
        </div>
      </div>

      <div className="decision-rationale-box">
        <strong className="decision-rationale-heading">Rationale: </strong>
        <span>{decision.rationale || 'No rationale recorded.'}</span>
      </div>

      {decision.explanation && (
        <div className="decision-explanation-box">
          <strong className="decision-explanation-heading">Explanation: </strong>
          <span>{decision.explanation}</span>
        </div>
      )}

      <div className="decision-details-grid">
        <div className="decision-detail-item">
          <div className="decision-detail-label">Health Score at Decision</div>
          <div className="decision-detail-val">
            {decision.health_score !== null && decision.health_score !== undefined
              ? `${formatMetric(decision.health_score, 1)} (${decision.health_status})`
              : 'N/A'}
          </div>
        </div>
        <div className="decision-detail-item">
          <div className="decision-detail-label">Confidence Score</div>
          <div className="decision-detail-val">
            {decision.confidence !== null && decision.confidence !== undefined
              ? `${(decision.confidence * 100).toFixed(1)}%`
              : 'N/A'}
          </div>
        </div>
        <div className="decision-detail-item">
          <div className="decision-detail-label">Requires Human Approval</div>
          <div
            className={cn(
              'decision-detail-val',
              decision.requires_human_approval ? 'text-warning' : 'text-healthy'
            )}
          >
            {decision.requires_human_approval ? 'YES (Mandatory)' : 'NO'}
          </div>
        </div>
        <div className="decision-detail-item">
          <div className="decision-detail-label">Approval Status</div>
          <div className="decision-detail-val">
            <StatusBadge variant={getApprovalClass(decision.approval_status)} size="sm">
              {decision.approval_status}
            </StatusBadge>
          </div>
        </div>
      </div>

      {/* Action Controls */}
      {isPending && (
        <div className="approval-actions">
          {isViewer && (
            <div className="approval-viewer-notice">
              <Lock className="icon-sm" />
              <span>Viewers have read-only access. ML_ENGINEER or ADMIN required to approve/reject.</span>
            </div>
          )}

          <button
            type="button"
            className="btn btn-danger"
            onClick={handleOpenReject}
            disabled={isViewer || isLoading}
            title={isViewer ? 'Viewers cannot reject recommendations' : 'Reject this recommendation'}
            aria-label="Reject recommendation"
          >
            <XCircle className="icon-sm" />
            <span>{isLoading ? 'Processing...' : '✕ Reject Recommendation'}</span>
          </button>

          <button
            type="button"
            className="btn btn-success"
            onClick={handleOpenApprove}
            disabled={isViewer || isLoading}
            title={isViewer ? 'Viewers cannot approve recommendations' : 'Approve this recommendation'}
            aria-label="Approve recommendation"
          >
            <CheckCircle className="icon-sm" />
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
