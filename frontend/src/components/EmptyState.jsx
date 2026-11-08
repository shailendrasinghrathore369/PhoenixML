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
    <div
      className={cn(
        'state-container flex flex-col items-center justify-center p-8 md:p-12 text-center rounded-xl border border-dashed border-slate-800 bg-slate-900/30',
        className
      )}
    >
      <div className="p-3.5 rounded-full bg-slate-800/80 border border-slate-700/60 text-slate-400 mb-4 shadow-inner">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="empty-title text-base font-semibold text-slate-200 mb-1.5">
        {title}
      </h3>
      <p className="empty-desc text-xs text-slate-400 max-w-sm mb-4 leading-relaxed">
        {description}
      </p>
      {action && <div>{action}</div>}
    </div>
  );
}
