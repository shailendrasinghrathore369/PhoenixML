import React from 'react';
import { ShieldAlert } from 'lucide-react';
import { cn } from '../lib/utils.js';

export function HITLBanner({ className }) {
  return (
    <div
      role="region"
      aria-label="Human-In-The-Loop Advisory"
      className={cn('hitl-banner', className)}
    >
      <div className="hitl-banner-icon-box" aria-hidden="true">
        <ShieldAlert className="icon-md" />
      </div>
      <div className="hitl-banner-text">
        <span className="hitl-pill">
          Human-In-The-Loop Advisory
        </span>
        <span className="hitl-banner-desc">
          PhoenixML AIMD generates deterministic maintenance recommendations only. Autonomous retraining, rollback, deployment, or maintenance execution is strictly prohibited. Human operator review and authorization is mandatory.
        </span>
      </div>
    </div>
  );
}
