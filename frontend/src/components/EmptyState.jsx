import React from 'react';
import { cn } from '../lib/utils.js';
import { Inbox } from 'lucide-react';

export function EmptyState({
  icon: Icon = Inbox,
  title = 'No Data Available',
  description = 'There are no records found for this section.',
  action,
  className,
}) {
  return (
    <div className={cn('state-container empty-state', className)}>
      <div className="empty-icon-box" aria-hidden="true">
        <Icon className="icon-md" />
      </div>
      <h3 className="empty-title">
        {title}
      </h3>
      <p className="empty-desc">
        {description}
      </p>
      {action && <div className="empty-action">{action}</div>}
    </div>
  );
}
