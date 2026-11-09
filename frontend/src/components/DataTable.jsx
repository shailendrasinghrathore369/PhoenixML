import React from 'react';
import { cn } from '../lib/utils.js';
import { EmptyState } from './EmptyState.jsx';
import { Inbox } from 'lucide-react';

export function DataTable({
  columns = [],
  data = [],
  keyField = 'id',
  emptyTitle = 'No Records Found',
  emptyDescription = 'There are no items to display at this time.',
  onRowClick,
  className,
}) {
  if (!data || data.length === 0) {
    return (
      <EmptyState
        icon={Inbox}
        title={emptyTitle}
        description={emptyDescription}
      />
    );
  }

  return (
    <div className={cn('table-responsive', className)}>
      <table>
        <thead>
          <tr>
            {columns.map((col, idx) => (
              <th
                key={col.key || idx}
                scope="col"
                className={cn(
                  col.align === 'right' && 'text-right',
                  col.align === 'center' && 'text-center',
                  col.headerClassName
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIdx) => (
            <tr
              key={row[keyField] || rowIdx}
              onClick={() => onRowClick?.(row)}
              style={onRowClick ? { cursor: 'pointer' } : undefined}
            >
              {columns.map((col, colIdx) => (
                <td
                  key={col.key || colIdx}
                  className={cn(
                    col.align === 'right' && 'text-right',
                    col.align === 'center' && 'text-center',
                    col.className
                  )}
                >
                  {col.render ? col.render(row[col.key], row, rowIdx) : row[col.key] ?? 'N/A'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
