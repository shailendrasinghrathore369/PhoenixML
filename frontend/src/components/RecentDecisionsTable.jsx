import React from 'react';
import { DataTable } from './DataTable.jsx';
import { StatusBadge } from './StatusBadge.jsx';
import { formatDate, formatMetric, getApprovalClass, getPriorityClass } from '../lib/utils.js';
import { History } from 'lucide-react';

export function RecentDecisionsTable({ decisions = [], modelMap = {}, className }) {
  const columns = [
    {
      key: 'created_at',
      header: 'Date & Time',
      render: (val) => (
        <span className="font-mono text-xs text-slate-300 whitespace-nowrap">
          {formatDate(val)}
        </span>
      ),
    },
    {
      key: 'model_id',
      header: 'Model',
      render: (val) => {
        const modelName = modelMap[val]?.name || `${String(val).substring(0, 8)}...`;
        return (
          <span className="font-semibold text-slate-200">
            {modelName}
          </span>
        );
      },
    },
    {
      key: 'recommended_action',
      header: 'Recommended Action',
      render: (val) => (
        <span className="font-semibold text-slate-100">
          {val}
        </span>
      ),
    },
    {
      key: 'priority',
      header: 'Priority',
      render: (val) => (
        <StatusBadge variant={getPriorityClass(val)} size="sm">
          {val}
        </StatusBadge>
      ),
    },
    {
      key: 'health_score',
      header: 'Health Score',
      align: 'right',
      render: (val) => (
        <span className="font-mono text-xs text-slate-300">
          {val !== null && val !== undefined ? `${formatMetric(val, 1)}` : 'N/A'}
        </span>
      ),
    },
    {
      key: 'confidence',
      header: 'Confidence',
      align: 'right',
      render: (val) => (
        <span className="font-mono text-xs text-slate-300">
          {val !== null && val !== undefined ? `${(val * 100).toFixed(1)}%` : 'N/A'}
        </span>
      ),
    },
    {
      key: 'approval_status',
      header: 'Approval Status',
      render: (val) => (
        <StatusBadge variant={getApprovalClass(val)} size="sm">
          {val}
        </StatusBadge>
      ),
    },
  ];

  return (
    <div className={className}>
      <DataTable
        columns={columns}
        data={decisions}
        keyField="id"
        emptyTitle="No Decisions Recorded"
        emptyDescription="Trigger an AIMD evaluation on any model with monitoring observations to generate maintenance recommendations."
      />
    </div>
  );
}
