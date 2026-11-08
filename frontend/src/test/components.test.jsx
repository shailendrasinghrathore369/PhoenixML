import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { StatusBadge } from '../components/StatusBadge.jsx';
import { HealthIndicator } from '../components/HealthIndicator.jsx';
import { MetricCard } from '../components/MetricCard.jsx';
import { LoadingState } from '../components/LoadingState.jsx';
import { EmptyState } from '../components/EmptyState.jsx';
import { ErrorState } from '../components/ErrorState.jsx';
import { ConfirmationDialog } from '../components/ConfirmationDialog.jsx';
import { DataTable } from '../components/DataTable.jsx';
import { HITLBanner } from '../components/HITLBanner.jsx';
import { ToastItem } from '../components/Toast.jsx';

describe('StatusBadge', () => {
  it('renders healthy status variant', () => {
    render(<StatusBadge variant="healthy">Healthy Fleet</StatusBadge>);
    expect(screen.getByText('Healthy Fleet')).toBeInTheDocument();
  });

  it('renders warning and critical variants', () => {
    const { rerender } = render(<StatusBadge variant="warning">Warning</StatusBadge>);
    expect(screen.getByText('Warning')).toBeInTheDocument();

    rerender(<StatusBadge variant="critical">Critical</StatusBadge>);
    expect(screen.getByText('Critical')).toBeInTheDocument();
  });

  it('renders user role badges', () => {
    render(<StatusBadge variant="admin">ADMIN</StatusBadge>);
    expect(screen.getByText('ADMIN')).toBeInTheDocument();
  });
});

describe('HealthIndicator', () => {
  it('renders progressbar with score value', () => {
    render(<HealthIndicator score={85.4} status="HEALTHY" />);
    const bar = screen.getByRole('progressbar');
    expect(bar).toBeInTheDocument();
    expect(bar).toHaveAttribute('aria-valuenow', '85.4');
    expect(screen.getByText('85.4 / 100')).toBeInTheDocument();
  });

  it('handles null score safely', () => {
    render(<HealthIndicator score={null} />);
    expect(screen.getByText('NO_DATA')).toBeInTheDocument();
  });
});

describe('MetricCard', () => {
  it('renders title, value, and subtitle', () => {
    render(
      <MetricCard
        title="Active Models"
        value={12}
        subtext="10 active · 2 archived"
      />
    );
    expect(screen.getByText('Active Models')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('10 active · 2 archived')).toBeInTheDocument();
  });

  it('applies pending highlight state', () => {
    const { container } = render(
      <MetricCard
        title="Pending Approvals"
        value={3}
        highlight={true}
      />
    );
    expect(container.firstChild.className).toContain('border-amber-500');
  });
});

describe('LoadingState & EmptyState & ErrorState', () => {
  it('renders accessible loading message', () => {
    render(<LoadingState message="Fetching models..." />);
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText('Fetching models...')).toBeInTheDocument();
  });

  it('renders empty state with title and description', () => {
    render(
      <EmptyState
        title="No Models Found"
        description="Please register a model to get started."
      />
    );
    expect(screen.getByText('No Models Found')).toBeInTheDocument();
    expect(screen.getByText('Please register a model to get started.')).toBeInTheDocument();
  });

  it('renders error state with retry button', () => {
    const handleRetry = vi.fn();
    render(
      <ErrorState
        title="Network Error"
        message="Unable to reach API server"
        onRetry={handleRetry}
      />
    );
    expect(screen.getByText('Network Error')).toBeInTheDocument();
    const retryBtn = screen.getByRole('button', { name: /retry/i });
    fireEvent.click(retryBtn);
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });
});

describe('ConfirmationDialog', () => {
  it('renders dialog when isOpen is true and triggers confirm/close', () => {
    const handleClose = vi.fn();
    const handleConfirm = vi.fn();

    render(
      <ConfirmationDialog
        isOpen={true}
        onClose={handleClose}
        onConfirm={handleConfirm}
        title="Authorize Action"
        description="Proceed with retraining recommendation?"
      />
    );

    expect(screen.getByText('Authorize Action')).toBeInTheDocument();
    expect(screen.getByText('Proceed with retraining recommendation?')).toBeInTheDocument();

    const confirmBtn = screen.getByRole('button', { name: /confirm/i });
    fireEvent.click(confirmBtn);
    expect(handleConfirm).toHaveBeenCalledTimes(1);

    const cancelBtn = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('does not render when isOpen is false', () => {
    const { container } = render(
      <ConfirmationDialog
        isOpen={false}
        onClose={() => {}}
        onConfirm={() => {}}
        title="Hidden Dialog"
      />
    );
    expect(container).toBeEmptyDOMElement();
  });
});

describe('DataTable', () => {
  it('renders table headers and rows cleanly', () => {
    const columns = [
      { key: 'name', header: 'Model Name' },
      { key: 'version', header: 'Version' },
    ];
    const data = [
      { id: '1', name: 'SpamClassifier', version: '1.0.0' },
      { id: '2', name: 'BertSpam', version: '2.1.0' },
    ];

    render(<DataTable columns={columns} data={data} keyField="id" />);
    expect(screen.getByText('Model Name')).toBeInTheDocument();
    expect(screen.getByText('SpamClassifier')).toBeInTheDocument();
    expect(screen.getByText('BertSpam')).toBeInTheDocument();
  });
});

describe('HITLBanner', () => {
  it('renders human-in-the-loop advisory text and pill', () => {
    render(<HITLBanner />);
    expect(screen.getByText('Human-In-The-Loop Advisory')).toBeInTheDocument();
    expect(screen.getByText(/Autonomous retraining, rollback, deployment, or maintenance execution is strictly prohibited/i)).toBeInTheDocument();
  });
});

describe('ToastItem', () => {
  it('renders toast with message and dismiss action', () => {
    const handleDismiss = vi.fn();
    render(
      <ToastItem
        toast={{ id: 1, type: 'success', title: 'Evaluation Done', message: 'Observation recorded.' }}
        onDismiss={handleDismiss}
      />
    );
    expect(screen.getByText('Evaluation Done')).toBeInTheDocument();
    expect(screen.getByText('Observation recorded.')).toBeInTheDocument();

    const closeBtn = screen.getByTitle('Dismiss notification');
    fireEvent.click(closeBtn);
    expect(handleDismiss).toHaveBeenCalledWith(1);
  });
});
