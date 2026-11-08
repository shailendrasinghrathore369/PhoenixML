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
import { ToastItem, ToastContainer } from '../components/Toast.jsx';
import { ModelCard } from '../components/ModelCard.jsx';
import { DecisionReviewBox } from '../components/DecisionReviewBox.jsx';
import { RecentDecisionsTable } from '../components/RecentDecisionsTable.jsx';
import { LoginPage } from '../pages/LoginPage.jsx';
import { SignupPage } from '../pages/SignupPage.jsx';
import { DashboardPage } from '../pages/DashboardPage.jsx';
import { ThemeProvider } from '../context/ThemeContext.jsx';

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

  it('uses role="status" for non-error notifications and role="alert" for error', () => {
    const { rerender } = render(
      <ToastItem
        toast={{ id: 1, type: 'success', title: 'Done', message: 'Success' }}
        onDismiss={() => {}}
      />
    );
    expect(screen.getByRole('status')).toBeInTheDocument();

    rerender(
      <ToastItem
        toast={{ id: 2, type: 'error', title: 'Fail', message: 'Error' }}
        onDismiss={() => {}}
      />
    );
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });
});

describe('ModelCard', () => {
  it('renders model information, health score, and actions', () => {
    const model = {
      model_id: 'm1234567-89ab',
      name: 'TestModel',
      framework: 'scikit-learn',
      status: 'ACTIVE',
      latest_health_score: 91.2,
      latest_health_status: 'HEALTHY',
      observation_count: 50,
      latest_f1_score: 0.92,
    };
    render(
      <ModelCard
        model={model}
        isSelected={false}
        onSelect={() => {}}
        onEvaluate={() => {}}
        onRealEvaluate={() => {}}
      />
    );
    expect(screen.getByText('TestModel')).toBeInTheDocument();
    expect(screen.getByText(/scikit-learn/i)).toBeInTheDocument();
    expect(screen.getByText('ACTIVE')).toBeInTheDocument();
    expect(screen.getByText('50')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /inspect model/i })).toBeInTheDocument();
  });
});

describe('DecisionReviewBox', () => {
  it('renders AIMD decision details and human approval mandatory notice', () => {
    const decision = {
      id: 42,
      model_id: 'm123',
      recommended_action: 'RETRAIN_MODEL',
      priority: 'HIGH',
      approval_status: 'PENDING',
      rationale: 'Concept drift detected in incoming data.',
      requires_human_approval: true,
      health_score: 65.4,
      health_status: 'WARNING',
      confidence: 0.88,
    };
    render(
      <DecisionReviewBox
        decision={decision}
        modelName="TestModel"
        userRole="ML_ENGINEER"
        onApprove={() => {}}
        onReject={() => {}}
      />
    );
    expect(screen.getByText('RETRAIN_MODEL')).toBeInTheDocument();
    expect(screen.getByText(/Concept drift detected/i)).toBeInTheDocument();
    expect(screen.getByText('YES (Mandatory)')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /approve recommendation/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /reject recommendation/i })).toBeInTheDocument();
  });
});

describe('RecentDecisionsTable', () => {
  it('renders table headers with scope="col" and decision items', () => {
    const decisions = [
      {
        id: 1,
        created_at: '2026-11-08T12:00:00Z',
        model_id: 'm123',
        recommended_action: 'RECALIBRATE_THRESHOLDS',
        priority: 'MEDIUM',
        health_score: 75.0,
        confidence: 0.92,
        approval_status: 'APPROVED',
      },
    ];
    render(<RecentDecisionsTable decisions={decisions} modelMap={{ m123: { name: 'FraudDetector' } }} />);
    expect(screen.getByText('FraudDetector')).toBeInTheDocument();
    expect(screen.getByText('RECALIBRATE_THRESHOLDS')).toBeInTheDocument();
    const ths = screen.getAllByRole('columnheader');
    expect(ths.length).toBeGreaterThan(0);
    ths.forEach((th) => {
      expect(th).toHaveAttribute('scope', 'col');
    });
  });
});

describe('LoginPage', () => {
  it('renders login form, fields, and handles input', async () => {
    const handleLogin = vi.fn();
    const handleSwitch = vi.fn();

    render(
      <ThemeProvider>
        <LoginPage onLogin={handleLogin} onSwitchToSignup={handleSwitch} />
      </ThemeProvider>
    );

    expect(screen.getByText('PhoenixML')).toBeInTheDocument();
    expect(screen.getByLabelText(/email or username/i)).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/email or username/i), {
      target: { value: 'admin' },
    });
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'Secret123!' },
    });
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    expect(handleLogin).toHaveBeenCalledWith('admin', 'Secret123!');
  });

  it('toggles password visibility', () => {
    render(
      <ThemeProvider>
        <LoginPage onLogin={() => {}} onSwitchToSignup={() => {}} />
      </ThemeProvider>
    );

    const passwordInput = screen.getByLabelText('Password');
    expect(passwordInput).toHaveAttribute('type', 'password');

    const toggleBtn = screen.getByRole('button', { name: /show password/i });
    fireEvent.click(toggleBtn);
    expect(passwordInput).toHaveAttribute('type', 'text');

    fireEvent.click(toggleBtn);
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  it('displays session expired warning and switch link', () => {
    const handleSwitch = vi.fn();
    render(
      <ThemeProvider>
        <LoginPage
          onLogin={() => {}}
          onSwitchToSignup={handleSwitch}
          sessionExpired={true}
        />
      </ThemeProvider>
    );

    expect(screen.getByText(/your session has expired/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /register here/i }));
    expect(handleSwitch).toHaveBeenCalled();
  });
});

describe('SignupPage', () => {
  it('renders registration form and validates password match', async () => {
    const handleSignup = vi.fn();
    render(
      <ThemeProvider>
        <SignupPage onSignup={handleSignup} onSwitchToLogin={() => {}} />
      </ThemeProvider>
    );

    expect(screen.getByRole('heading', { name: /create account/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/^username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/^username/i), { target: { value: 'operator1' } });
    fireEvent.change(screen.getByLabelText(/email address/i), { target: { value: 'op@example.com' } });
    fireEvent.change(screen.getByLabelText(/^password/i), { target: { value: 'password123' } });
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'mismatch321' } });

    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    expect(handleSignup).not.toHaveBeenCalled();

    // Now fix confirmation password
    fireEvent.change(screen.getByLabelText(/confirm password/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    expect(handleSignup).toHaveBeenCalledWith({
      username: 'operator1',
      email: 'op@example.com',
      password: 'password123',
    });
  });

  it('switches to login page on click', () => {
    const handleSwitch = vi.fn();
    render(
      <ThemeProvider>
        <SignupPage onSignup={() => {}} onSwitchToLogin={handleSwitch} />
      </ThemeProvider>
    );

    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
    expect(handleSwitch).toHaveBeenCalled();
  });
});

describe('DashboardPage', () => {
  it('renders dashboard with model list, KPIs, and allows filtering', () => {
    const setSelectedModelId = vi.fn();
    const dashboardData = {
      model_cards: [
        {
          model_id: 'm1',
          name: 'SpamClassifier',
          framework: 'scikit-learn',
          status: 'ACTIVE',
          latest_health_score: 95,
          latest_health_status: 'HEALTHY',
          observation_count: 120,
          latest_f1_score: 0.94,
        },
      ],
      decision_summary: {
        total_decisions: 15,
        recent_decisions: [],
      },
    };

    render(
      <ThemeProvider>
        <DashboardPage
          user={{ role: 'ADMIN' }}
          dashboardData={dashboardData}
          selectedModelId=""
          setSelectedModelId={setSelectedModelId}
          loading={false}
          evalResults={{}}
          modelMap={{ m1: dashboardData.model_cards[0] }}
          handleEvaluate={() => {}}
          handleRealEvaluate={() => {}}
          handleApprove={() => {}}
          handleReject={() => {}}
        />
      </ThemeProvider>
    );

    expect(screen.getByText('Fleet Operations & Decision Support')).toBeInTheDocument();
    expect(screen.getByText('Scope / Model Filter:')).toBeInTheDocument();
    expect(screen.getByText('SpamClassifier')).toBeInTheDocument();
    expect(screen.getByText('1 model displayed')).toBeInTheDocument();
    expect(screen.getByText('Total Recorded: 15')).toBeInTheDocument();

    const select = screen.getByLabelText(/filter by registered model/i);
    fireEvent.change(select, { target: { value: 'm1' } });
    expect(setSelectedModelId).toHaveBeenCalledWith('m1');
  });
});
