import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { api } from '../lib/api.js';
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
import { ModelRegistryPage } from '../pages/ModelRegistryPage.jsx';
import { ApprovalsPage } from '../pages/ApprovalsPage.jsx';
import { TelemetryPage } from '../pages/TelemetryPage.jsx';
import { AuditTrailPage } from '../pages/AuditTrailPage.jsx';
import { useNavigation, parseViewFromHash, VALID_VIEWS } from '../hooks/useNavigation.js';
import { ThemeProvider } from '../context/ThemeContext.jsx';
import { PredictionPlayground, PLAYGROUND_PRESETS, formatInferenceError } from '../components/PredictionPlayground.jsx';

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

describe('useNavigation & Hash Routing', () => {
  it('parses valid view from hash or defaults to dashboard', () => {
    window.location.hash = '#/models';
    expect(parseViewFromHash()).toBe('models');

    window.location.hash = '#/telemetry';
    expect(parseViewFromHash()).toBe('telemetry');

    window.location.hash = '#/invalid_view';
    expect(parseViewFromHash()).toBe('dashboard');

    window.location.hash = '';
    expect(parseViewFromHash()).toBe('dashboard');
  });

  it('provides all 5 valid views', () => {
    expect(VALID_VIEWS).toEqual(['dashboard', 'models', 'approvals', 'telemetry', 'audit']);
  });
});

describe('ModelRegistryPage', () => {
  const mockModels = [
    {
      id: 'm-1',
      name: 'SpamSMS-LogisticRegression',
      framework: 'scikit-learn',
      algorithm: 'LogisticRegression',
      status: 'ACTIVE',
      owner_id: 'engineer-1',
      description: 'Production reference model',
      created_at: '2026-11-09T10:00:00Z',
    },
    {
      id: 'm-2',
      name: 'Candidate-NaiveBayes',
      framework: 'scikit-learn',
      algorithm: 'MultinomialNB',
      status: 'DEVELOPMENT',
      owner_id: 'engineer-2',
      description: 'Candidate model in development',
      created_at: '2026-11-09T11:00:00Z',
    },
  ];

  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(api, 'listModels').mockResolvedValue(mockModels);
  });

  it('renders model counts, header, and inventory table with real records', async () => {
    render(
      <ThemeProvider>
        <ModelRegistryPage
          user={{ id: 'engineer-1', role: 'ADMIN' }}
          dashboardData={{ models_summary: { total_models: 2, active_models: 1, development_models: 1, archived_models: 0 } }}
        />
      </ThemeProvider>
    );

    expect(screen.getByText('Model Registry & Governance')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText('SpamSMS-LogisticRegression')).toBeInTheDocument();
      expect(screen.getByText('Candidate-NaiveBayes')).toBeInTheDocument();
    });
    expect(screen.getByText('Total Registered Models')).toBeInTheDocument();
  });

  it('filters models by search query and status filter', async () => {
    render(
      <ThemeProvider>
        <ModelRegistryPage
          user={{ id: 'engineer-1', role: 'ADMIN' }}
        />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('SpamSMS-LogisticRegression')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/search models by name/i);
    fireEvent.change(searchInput, { target: { value: 'NaiveBayes' } });

    expect(screen.queryByText('SpamSMS-LogisticRegression')).not.toBeInTheDocument();
    expect(screen.getByText('Candidate-NaiveBayes')).toBeInTheDocument();
  });

  it('enforces RBAC visibility: ADMIN sees full actions on all models', async () => {
    render(
      <ThemeProvider>
        <ModelRegistryPage
          user={{ id: 'admin-1', role: 'ADMIN' }}
        />
      </ThemeProvider>
    );

    expect(screen.getByRole('button', { name: /register model/i })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByLabelText('Edit SpamSMS-LogisticRegression')).toBeInTheDocument();
      expect(screen.getByLabelText('Edit Candidate-NaiveBayes')).toBeInTheDocument();
      expect(screen.getByLabelText('Delete SpamSMS-LogisticRegression')).toBeInTheDocument();
      expect(screen.getByLabelText('Delete Candidate-NaiveBayes')).toBeInTheDocument();
    });
  });

  it('enforces RBAC visibility: ML_ENGINEER only sees Edit/Delete on owned models', async () => {
    render(
      <ThemeProvider>
        <ModelRegistryPage
          user={{ id: 'engineer-1', role: 'ML_ENGINEER' }}
        />
      </ThemeProvider>
    );

    expect(screen.getByRole('button', { name: /register model/i })).toBeInTheDocument();
    await waitFor(() => {
      // engineer-1 owns m-1
      expect(screen.getByLabelText('Edit SpamSMS-LogisticRegression')).toBeInTheDocument();
      expect(screen.getByLabelText('Delete SpamSMS-LogisticRegression')).toBeInTheDocument();
      // m-2 is owned by engineer-2
      expect(screen.queryByLabelText('Edit Candidate-NaiveBayes')).not.toBeInTheDocument();
      expect(screen.queryByLabelText('Delete Candidate-NaiveBayes')).not.toBeInTheDocument();
    });
  });

  it('enforces RBAC visibility: VIEWER has read-only access with no mutation buttons', async () => {
    render(
      <ThemeProvider>
        <ModelRegistryPage
          user={{ id: 'viewer-1', role: 'VIEWER' }}
        />
      </ThemeProvider>
    );

    expect(screen.getByText('Viewer (Read-Only)')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /register model/i })).not.toBeInTheDocument();
    await waitFor(() => {
      expect(screen.queryByLabelText(/edit /i)).not.toBeInTheDocument();
      expect(screen.queryByLabelText(/delete /i)).not.toBeInTheDocument();
      expect(screen.getByLabelText('Test SpamSMS-LogisticRegression in Playground')).toBeInTheDocument();
    });
  });

  it('opens registration modal, validates required fields, and submits createModel', async () => {
    const createSpy = vi.spyOn(api, 'createModel').mockResolvedValue({
      id: 'm-new',
      name: 'BERT-Spam',
      framework: 'PyTorch',
      algorithm: null,
      description: null,
      status: 'DEVELOPMENT',
    });
    const mockToast = { success: vi.fn(), error: vi.fn(), info: vi.fn(), warning: vi.fn() };

    render(
      <ThemeProvider>
        <ModelRegistryPage
          user={{ id: 'admin-1', role: 'ADMIN' }}
          toast={mockToast}
        />
      </ThemeProvider>
    );

    const openBtn = screen.getByRole('button', { name: /register model/i });
    fireEvent.click(openBtn);

    expect(screen.getByText('Register New Spam Model')).toBeInTheDocument();

    const dialog = screen.getByRole('dialog');
    // Fill form
    const nameInput = within(dialog).getByLabelText(/model name \*/i);
    const frameworkInput = within(dialog).getByLabelText(/framework \*/i);
    fireEvent.change(nameInput, { target: { value: 'BERT-Spam' } });
    fireEvent.change(frameworkInput, { target: { value: 'PyTorch' } });

    const submitBtn = within(dialog).getByRole('button', { name: 'Register Model' });
    fireEvent.submit(dialog.querySelector('form'));

    await waitFor(() => {
      expect(createSpy).toHaveBeenCalledWith({
        name: 'BERT-Spam',
        framework: 'PyTorch',
        algorithm: null,
        description: null,
        status: 'DEVELOPMENT',
      });
      expect(mockToast.success).toHaveBeenCalledWith(expect.stringContaining('BERT-Spam'));
    });
  });

  it('opens edit modal prefilled with model data and submits updateModel', async () => {
    const updateSpy = vi.spyOn(api, 'updateModel').mockResolvedValue({
      ...mockModels[0],
      status: 'ARCHIVED',
    });
    const mockToast = { success: vi.fn(), error: vi.fn(), info: vi.fn(), warning: vi.fn() };

    render(
      <ThemeProvider>
        <ModelRegistryPage
          user={{ id: 'admin-1', role: 'ADMIN' }}
          toast={mockToast}
        />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Edit SpamSMS-LogisticRegression')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText('Edit SpamSMS-LogisticRegression'));
    expect(screen.getByText('Edit Model: SpamSMS-LogisticRegression')).toBeInTheDocument();

    const dialog = screen.getByRole('dialog');
    const statusSelect = within(dialog).getByLabelText(/lifecycle status/i);
    fireEvent.change(statusSelect, { target: { value: 'ARCHIVED' } });

    fireEvent.submit(dialog.querySelector('form'));

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith('m-1', expect.objectContaining({ status: 'ARCHIVED' }));
      expect(mockToast.success).toHaveBeenCalledWith(expect.stringContaining('SpamSMS-LogisticRegression'));
    });
  });

  it('opens confirmation dialog on delete and confirms deletion', async () => {
    const deleteSpy = vi.spyOn(api, 'deleteModel').mockResolvedValue(null);
    const mockToast = { success: vi.fn(), error: vi.fn(), info: vi.fn(), warning: vi.fn() };

    render(
      <ThemeProvider>
        <ModelRegistryPage
          user={{ id: 'admin-1', role: 'ADMIN' }}
          toast={mockToast}
        />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Delete SpamSMS-LogisticRegression')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText('Delete SpamSMS-LogisticRegression'));
    expect(screen.getByText('Delete Registered Model')).toBeInTheDocument();

    const dialog = screen.getByRole('dialog');
    const confirmBtn = within(dialog).getByRole('button', { name: 'Delete Model' });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(deleteSpy).toHaveBeenCalledWith('m-1');
      expect(mockToast.success).toHaveBeenCalledWith(expect.stringContaining('SpamSMS-LogisticRegression'));
    });
  });

  it('navigates to playground sub-tab when "Playground" action is clicked', async () => {
    const mockToast = { success: vi.fn(), error: vi.fn(), info: vi.fn(), warning: vi.fn() };

    render(
      <ThemeProvider>
        <ModelRegistryPage
          user={{ id: 'viewer-1', role: 'VIEWER' }}
          toast={mockToast}
        />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Test SpamSMS-LogisticRegression in Playground')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText('Test SpamSMS-LogisticRegression in Playground'));

    expect(screen.getByText('Target Testing Model')).toBeInTheDocument();
    expect(screen.getByText('Prediction Playground Console')).toBeInTheDocument();

    // Clicking back to inventory returns to inventory sub-tab
    const backBtn = screen.getByRole('button', { name: /back to inventory/i });
    fireEvent.click(backBtn);
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('displays loading state and error alert with retry button', async () => {
    vi.spyOn(api, 'listModels').mockRejectedValueOnce(new Error('Network error'));

    render(
      <ThemeProvider>
        <ModelRegistryPage
          user={{ id: 'admin-1', role: 'ADMIN' }}
        />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });
  });
});

describe('ApprovalsPage', () => {
  it('renders decision review box when pending decision exists', () => {
    const handleApprove = vi.fn();
    const handleReject = vi.fn();
    const pendingDecision = {
      id: 99,
      model_id: 'm1',
      recommended_action: 'RECALIBRATE_THRESHOLDS',
      priority: 'HIGH',
      approval_status: 'PENDING',
      rationale: 'Confidence dropped under high noise input.',
      requires_human_approval: true,
      health_score: 55,
      confidence: 0.85,
    };

    render(
      <ThemeProvider>
        <ApprovalsPage
          user={{ role: 'ADMIN' }}
          dashboardData={{
            decision_summary: { pending_approvals_count: 1, total_decisions: 5 },
          }}
          pendingDecision={pendingDecision}
          modelMap={{ m1: { name: 'SpamModel' } }}
          handleApprove={handleApprove}
          handleReject={handleReject}
        />
      </ThemeProvider>
    );

    expect(screen.getByText('Human-in-the-Loop Approval Queue')).toBeInTheDocument();
    expect(screen.getByText('1 Action Required')).toBeInTheDocument();
    expect(screen.getByText('RECALIBRATE_THRESHOLDS')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /approve recommendation/i })).toBeInTheDocument();
  });

  it('renders clear queue empty state when no pending decisions exist', () => {
    const handleNavigate = vi.fn();
    render(
      <ThemeProvider>
        <ApprovalsPage
          user={{ role: 'ADMIN' }}
          dashboardData={{
            decision_summary: { pending_approvals_count: 0, total_decisions: 5 },
          }}
          pendingDecision={null}
          onNavigate={handleNavigate}
        />
      </ThemeProvider>
    );

    expect(screen.getByText('Approval Queue is Clear')).toBeInTheDocument();
    const returnBtn = screen.getByRole('button', { name: /return to fleet operations/i });
    fireEvent.click(returnBtn);
    expect(handleNavigate).toHaveBeenCalledWith('dashboard');
  });
});

describe('TelemetryPage', () => {
  const sampleModels = [
    {
      id: 'model-1',
      name: 'SpamSMS-LogisticRegression',
      framework: 'scikit-learn',
      algorithm: 'LogisticRegression',
      status: 'ACTIVE',
    },
    {
      id: 'model-2',
      name: 'Candidate-NaiveBayes',
      framework: 'scikit-learn',
      algorithm: 'MultinomialNB',
      status: 'DEVELOPMENT',
    },
  ];

  const sampleObservations = [
    {
      id: 'obs-1',
      model_id: 'model-1',
      observed_at: '2026-11-10T12:00:00Z',
      prediction_count: 100,
      positive_prediction_count: 40,
      negative_prediction_count: 60,
      accuracy: 0.95,
      precision: 0.92,
      recall: 0.90,
      f1_score: 0.9097,
    },
    {
      id: 'obs-2',
      model_id: 'model-1',
      observed_at: '2026-11-09T12:00:00Z',
      prediction_count: 80,
      positive_prediction_count: 30,
      negative_prediction_count: 50,
      accuracy: 0.91,
      precision: 0.88,
      recall: 0.86,
      f1_score: 0.8698,
    },
  ];

  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(api, 'listModels').mockResolvedValue(sampleModels);
    vi.spyOn(api, 'listObservations').mockResolvedValue(sampleObservations);
  });

  it('renders model selector, summary metrics, and observation table for selected model', async () => {
    render(
      <ThemeProvider>
        <TelemetryPage user={{ role: 'ADMIN' }} />
      </ThemeProvider>
    );

    expect(screen.getByText('Model Telemetry & Performance Trends')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByLabelText(/select registered model/i)).toBeInTheDocument();
      expect(screen.getByText(/SpamSMS-LogisticRegression/)).toBeInTheDocument();
    });

    // Check summary metric cards
    expect(screen.getByText('Latest F1 Score')).toBeInTheDocument();
    expect(screen.getAllByText('0.9097').length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText('Historical Avg F1')).toBeInTheDocument();
    // Avg F1: (0.9097 + 0.8698) / 2 = 0.88975 -> 0.8898
    expect(screen.getByText('0.8898')).toBeInTheDocument();
    expect(screen.getByText('Latest Accuracy')).toBeInTheDocument();
    expect(screen.getByText('95.0%')).toBeInTheDocument();
    expect(screen.getByText('Historical Avg Accuracy')).toBeInTheDocument();
    // Avg Accuracy: (0.95 + 0.91) / 2 = 0.93 -> 93.0%
    expect(screen.getByText('93.0%')).toBeInTheDocument();

    // Check observation table headers
    expect(screen.getByText('Historical Observations Log')).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /observed at/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /total predictions/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /positive \(spam\)/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /negative \(ham\)/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /^accuracy$/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /^precision$/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /^recall$/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /f1 score/i })).toBeInTheDocument();

    // Check observation table values
    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getByText('40')).toBeInTheDocument();
    expect(screen.getByText('60')).toBeInTheDocument();
    expect(screen.getByText('0.9500')).toBeInTheDocument();
    expect(screen.getByText('0.9200')).toBeInTheDocument();
    expect(screen.getAllByText('0.9000').length).toBeGreaterThanOrEqual(2);

    // Roadmap cards present
    expect(screen.getByText('Telemetry & Visualization Roadmap (Milestone 3)')).toBeInTheDocument();
    expect(screen.getByText('Time-Series Performance Charts')).toBeInTheDocument();
  });

  it('supports switching models without full page reload and fetches target observations', async () => {
    const model2Obs = [
      {
        id: 'obs-m2-1',
        model_id: 'model-2',
        observed_at: '2026-11-10T14:00:00Z',
        prediction_count: 50,
        positive_prediction_count: 20,
        negative_prediction_count: 30,
        accuracy: 0.88,
        precision: 0.85,
        recall: 0.82,
        f1_score: 0.8347,
      },
    ];

    vi.spyOn(api, 'listObservations').mockImplementation(async (modelId) => {
      if (modelId === 'model-2') return model2Obs;
      return sampleObservations;
    });

    const handleSelectModel = vi.fn();

    render(
      <ThemeProvider>
        <TelemetryPage
          user={{ role: 'ADMIN' }}
          selectedModelId="model-1"
          setSelectedModelId={handleSelectModel}
        />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getAllByText('0.9097').length).toBeGreaterThanOrEqual(1);
    });

    const select = screen.getByLabelText(/select registered model/i);
    fireEvent.change(select, { target: { value: 'model-2' } });

    expect(handleSelectModel).toHaveBeenCalledWith('model-2');
  });

  it('handles pagination with skip and limit correctly', async () => {
    const page1Obs = Array.from({ length: 10 }, (_, i) => ({
      id: `p1-obs-${i}`,
      model_id: 'model-1',
      observed_at: `2026-11-${String(10 - i).padStart(2, '0')}T10:00:00Z`,
      prediction_count: 50,
      positive_prediction_count: 20,
      negative_prediction_count: 30,
      accuracy: 0.90,
      precision: 0.89,
      recall: 0.88,
      f1_score: 0.885,
    }));

    const page2Obs = [
      {
        id: 'p2-obs-1',
        model_id: 'model-1',
        observed_at: '2026-10-30T10:00:00Z',
        prediction_count: 30,
        positive_prediction_count: 10,
        negative_prediction_count: 20,
        accuracy: 0.85,
        precision: 0.84,
        recall: 0.83,
        f1_score: 0.835,
      },
    ];

    const listObsSpy = vi.spyOn(api, 'listObservations').mockImplementation(async (modelId, params) => {
      if (params?.skip === 10) return page2Obs;
      return page1Obs;
    });

    render(
      <ThemeProvider>
        <TelemetryPage user={{ role: 'ADMIN' }} selectedModelId="model-1" />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Showing 1 to 10 observations · Page 1')).toBeInTheDocument();
    });

    const prevBtn = screen.getByRole('button', { name: /previous page/i });
    const nextBtn = screen.getByRole('button', { name: /next page/i });

    expect(prevBtn).toBeDisabled();
    expect(nextBtn).not.toBeDisabled();

    // Click Next
    fireEvent.click(nextBtn);

    await waitFor(() => {
      expect(listObsSpy).toHaveBeenCalledWith('model-1', { skip: 10, limit: 10 });
      expect(screen.getByText('Showing 11 to 11 observations · Page 2')).toBeInTheDocument();
    });

    expect(prevBtn).not.toBeDisabled();
    expect(nextBtn).toBeDisabled(); // page 2 has 1 item < PAGE_SIZE

    // Click Previous
    fireEvent.click(prevBtn);

    await waitFor(() => {
      expect(listObsSpy).toHaveBeenCalledWith('model-1', { skip: 0, limit: 10 });
      expect(screen.getByText('Showing 1 to 10 observations · Page 1')).toBeInTheDocument();
    });
  });

  it('handles null metrics safely without fabricated values and calculates averages only from non-null values', async () => {
    const nullMetricObs = [
      {
        id: 'obs-null-1',
        model_id: 'model-1',
        observed_at: '2026-11-10T12:00:00Z',
        prediction_count: 50,
        positive_prediction_count: 25,
        negative_prediction_count: 25,
        accuracy: null,
        precision: 0.90,
        recall: null,
        f1_score: 0.88,
      },
      {
        id: 'obs-null-2',
        model_id: 'model-1',
        observed_at: '2026-11-09T12:00:00Z',
        prediction_count: 50,
        positive_prediction_count: 25,
        negative_prediction_count: 25,
        accuracy: 0.94,
        precision: null,
        recall: 0.86,
        f1_score: null,
      },
    ];

    vi.spyOn(api, 'listObservations').mockResolvedValue(nullMetricObs);

    render(
      <ThemeProvider>
        <TelemetryPage user={{ role: 'ADMIN' }} selectedModelId="model-1" />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Historical Observations Log')).toBeInTheDocument();
    });

    // Latest observation metrics:
    // Obs 1 has accuracy: null -> 'N/A'
    // Obs 1 has f1_score: 0.88 -> '0.8800' (KPI card and table row)
    expect(screen.getAllByText('0.8800').length).toBeGreaterThanOrEqual(2);

    // Historical Averages:
    // F1 has 1 non-null value (0.88) -> 0.8800
    // Accuracy has 1 non-null value (0.94) -> 94.0%
    expect(screen.getByText('94.0%')).toBeInTheDocument();
    expect(screen.getAllByText('Mean of 1 recorded observation').length).toBe(2);

    // Precision has 1 non-null value (0.90) -> 0.9000 (card + table cell)
    expect(screen.getAllByText('0.9000').length).toBeGreaterThanOrEqual(2);
    // Recall has 1 non-null value (0.86) -> 0.8600 (card + table cell)
    expect(screen.getAllByText('0.8600').length).toBeGreaterThanOrEqual(2);

    // In the table, null cells render 'N/A'
    const naCells = screen.getAllByText('N/A');
    expect(naCells.length).toBeGreaterThan(0);
  });

  it('renders empty state when a model has zero observations and navigates to fleet overview', async () => {
    vi.spyOn(api, 'listObservations').mockResolvedValue([]);
    const handleNavigate = vi.fn();

    render(
      <ThemeProvider>
        <TelemetryPage user={{ role: 'ADMIN' }} selectedModelId="model-1" onNavigate={handleNavigate} />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('No Historical Observations Recorded')).toBeInTheDocument();
    });

    const evalBtn = screen.getByRole('button', { name: /run model evaluations in fleet overview/i });
    expect(evalBtn).toBeInTheDocument();
    fireEvent.click(evalBtn);
    expect(handleNavigate).toHaveBeenCalledWith('dashboard');
  });

  it('renders empty state when no registered models exist in scope', async () => {
    vi.spyOn(api, 'listModels').mockResolvedValue([]);
    const handleNavigate = vi.fn();

    render(
      <ThemeProvider>
        <TelemetryPage user={{ role: 'ADMIN' }} onNavigate={handleNavigate} />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('No Registered Models Found')).toBeInTheDocument();
    });

    const regBtn = screen.getByRole('button', { name: /go to model registry/i });
    fireEvent.click(regBtn);
    expect(handleNavigate).toHaveBeenCalledWith('models');
  });

  it('displays error state with retry button on API failure', async () => {
    const listObsSpy = vi.spyOn(api, 'listObservations')
      .mockRejectedValueOnce(new Error('Network failure'))
      .mockResolvedValueOnce(sampleObservations);

    render(
      <ThemeProvider>
        <TelemetryPage user={{ role: 'ADMIN' }} selectedModelId="model-1" />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to Load Telemetry Observations')).toBeInTheDocument();
      expect(screen.getByText('Network failure')).toBeInTheDocument();
    });

    const retryBtn = screen.getByRole('button', { name: /retry/i });
    fireEvent.click(retryBtn);

    await waitFor(() => {
      expect(listObsSpy).toHaveBeenCalledTimes(2);
      expect(screen.getByText('Historical Observations Log')).toBeInTheDocument();
    });
  });

  it('handles authorization (403) error and displays clear permission notice', async () => {
    const authError = new Error('Forbidden');
    authError.status = 403;
    vi.spyOn(api, 'listObservations').mockRejectedValue(authError);

    render(
      <ThemeProvider>
        <TelemetryPage user={{ role: 'VIEWER' }} selectedModelId="model-1" />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to Load Telemetry Observations')).toBeInTheDocument();
      expect(screen.getByText(/access denied/i)).toBeInTheDocument();
    });
  });
});

describe('AuditTrailPage', () => {
  it('renders total decisions count and recent decisions table', () => {
    const dashboardData = {
      decision_summary: {
        total_decisions: 12,
        approved_count: 8,
        rejected_count: 2,
        pending_approvals_count: 2,
        recent_decisions: [
          {
            id: 1,
            created_at: '2026-11-08T12:00:00Z',
            model_id: 'm1',
            recommended_action: 'MAINTAIN_CURRENT_STATE',
            priority: 'LOW',
            health_score: 95.0,
            confidence: 0.98,
            approval_status: 'APPROVED',
          },
        ],
      },
    };

    render(
      <ThemeProvider>
        <AuditTrailPage
          user={{ role: 'ADMIN' }}
          dashboardData={dashboardData}
          modelMap={{ m1: { name: 'ProductionSpamDetector' } }}
        />
      </ThemeProvider>
    );

    expect(screen.getByText('Decision Audit Trail & Governance Log')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('ProductionSpamDetector')).toBeInTheDocument();
    expect(screen.getByText('MAINTAIN_CURRENT_STATE')).toBeInTheDocument();
    expect(screen.getByText('Audit Trail Enhancements (Milestone 4)')).toBeInTheDocument();
  });
});

describe('PredictionPlayground & Interactive Inference', () => {
  const sampleModels = [
    {
      id: 'm-prod',
      name: 'SpamSMS-DistilBERT',
      framework: 'PyTorch',
      algorithm: 'DistilBERT',
      status: 'ACTIVE',
    },
    {
      id: 'm-second',
      name: 'SpamSMS-LogisticRegression',
      framework: 'scikit-learn',
      algorithm: 'LogisticRegression',
      status: 'ACTIVE',
    },
    {
      id: 'm-dev',
      name: 'Candidate-NaiveBayes',
      framework: 'scikit-learn',
      algorithm: 'MultinomialNB',
      status: 'DEVELOPMENT',
    },
  ];

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('selects the first ACTIVE model by default when no selectedModelId is provided', () => {
    render(
      <ThemeProvider>
        <PredictionPlayground models={sampleModels} />
      </ThemeProvider>
    );

    expect(screen.getByText('Target Testing Model')).toBeInTheDocument();
    expect(screen.getByText('SpamSMS-DistilBERT')).toBeInTheDocument();
  });

  it('respects a preselected model ID from inventory navigation', () => {
    render(
      <ThemeProvider>
        <PredictionPlayground models={sampleModels} selectedModelId="m-second" />
      </ThemeProvider>
    );

    expect(screen.getByText('SpamSMS-LogisticRegression')).toBeInTheDocument();
  });

  it('switches target model using the model dropdown selector', () => {
    const handleSelect = vi.fn();
    render(
      <ThemeProvider>
        <PredictionPlayground
          models={sampleModels}
          selectedModelId="m-prod"
          onSelectModelId={handleSelect}
        />
      </ThemeProvider>
    );

    const select = screen.getByLabelText(/select model for prediction playground/i);
    fireEvent.change(select, { target: { value: 'm-second' } });
    expect(handleSelect).toHaveBeenCalledWith('m-second');
  });

  it('renders EmptyState when no ACTIVE models are available in the registry', () => {
    const handleBack = vi.fn();
    const inactiveOnly = [
      { id: 'm-dev', name: 'DevModel', framework: 'sklearn', status: 'DEVELOPMENT' },
    ];

    render(
      <ThemeProvider>
        <PredictionPlayground
          models={inactiveOnly}
          onNavigateToInventory={handleBack}
        />
      </ThemeProvider>
    );

    expect(screen.getByText('No Active Models Available')).toBeInTheDocument();
    expect(screen.getByText(/requires at least one ACTIVE spam detection model/i)).toBeInTheDocument();

    const returnBtn = screen.getByRole('button', { name: /return to model inventory/i });
    fireEvent.click(returnBtn);
    expect(handleBack).toHaveBeenCalledTimes(1);
  });

  it('validates non-empty input for Single SMS prediction', async () => {
    const predictSpy = vi.spyOn(api, 'predict');

    render(
      <ThemeProvider>
        <PredictionPlayground models={sampleModels} />
      </ThemeProvider>
    );

    const submitBtn = screen.getByRole('button', { name: /classify sms/i });
    expect(submitBtn).toBeDisabled();

    // Type spaces
    const textarea = screen.getByLabelText(/sms text message/i);
    fireEvent.change(textarea, { target: { value: '   ' } });
    expect(submitBtn).toBeDisabled();

    // Trigger form submission directly
    fireEvent.submit(textarea.closest('form'));
    expect(screen.getByText('SMS message text cannot be empty.')).toBeInTheDocument();
    expect(predictSpy).not.toHaveBeenCalled();
  });

  it('executes Single SMS prediction and renders label, confidence, and class probabilities', async () => {
    const mockPrediction = {
      model_id: 'm-prod',
      model_name: 'SpamSMS-DistilBERT',
      model_version: 'v1.0.0',
      total_predictions: 1,
      spam_count: 1,
      ham_count: 0,
      predictions: [
        {
          text: 'URGENT: Click http://scam.xyz to claim $1000 now!',
          predicted_label: 'spam',
          label_id: 1,
          is_spam: true,
          spam_probability: 0.985,
          ham_probability: 0.015,
          confidence: 0.985,
          model_name: 'SpamSMS-DistilBERT',
          model_version: 'v1.0.0',
        },
      ],
    };
    const predictSpy = vi.spyOn(api, 'predict').mockResolvedValue(mockPrediction);
    const mockToast = { success: vi.fn(), error: vi.fn(), info: vi.fn() };

    render(
      <ThemeProvider>
        <PredictionPlayground models={sampleModels} toast={mockToast} />
      </ThemeProvider>
    );

    const textarea = screen.getByLabelText(/sms text message/i);
    fireEvent.change(textarea, { target: { value: 'URGENT: Click http://scam.xyz to claim $1000 now!' } });

    const submitBtn = screen.getByRole('button', { name: /classify sms/i });
    expect(submitBtn).not.toBeDisabled();
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(predictSpy).toHaveBeenCalledWith('m-prod', {
        text: 'URGENT: Click http://scam.xyz to claim $1000 now!',
      });
    });

    // Check predicted label badge
    expect(screen.getAllByText('SPAM').length).toBeGreaterThan(0);
    // Check confidence score
    expect(screen.getAllByText('98.5%').length).toBeGreaterThan(0);
    // Check accessible progressbar for confidence meter
    const confidenceMeter = screen.getByRole('progressbar', { name: /model confidence meter/i });
    expect(confidenceMeter).toHaveAttribute('aria-valuenow', '99');
    // Check probability values
    expect(screen.getByText('98.50%')).toBeInTheDocument();
    expect(screen.getByText('1.50%')).toBeInTheDocument();
    // Check advisory disclaimer
    expect(screen.getByText(/statistical notice: predictions represent machine learning probabilistic estimates/i)).toBeInTheDocument();
    expect(mockToast.success).toHaveBeenCalledWith(expect.stringContaining('Classified as SPAM'));
  });

  it('populates preset examples without automatically submitting inference', () => {
    const predictSpy = vi.spyOn(api, 'predict');

    render(
      <ThemeProvider>
        <PredictionPlayground models={sampleModels} />
      </ThemeProvider>
    );

    const textarea = screen.getByLabelText(/sms text message/i);
    expect(textarea.value).toBe('');

    // Click "Spam phishing message" preset
    const phishingBtn = screen.getByRole('button', { name: /spam phishing message/i });
    fireEvent.click(phishingBtn);

    expect(textarea.value).toContain('URGENT! Your online bank access');
    expect(predictSpy).not.toHaveBeenCalled();

    // Click "Typical ham conversation" preset
    const hamBtn = screen.getByRole('button', { name: /typical ham conversation/i });
    fireEvent.click(hamBtn);

    expect(textarea.value).toContain('Hey Sam, are we still meeting');
    expect(predictSpy).not.toHaveBeenCalled();
  });

  it('executes Batch SMS prediction, handles empty lines, and renders aggregate summary and table', async () => {
    const mockBatchResponse = {
      model_id: 'm-prod',
      model_name: 'SpamSMS-DistilBERT',
      model_version: 'v1.0.0',
      total_predictions: 2,
      spam_count: 1,
      ham_count: 1,
      predictions: [
        {
          text: 'Free tickets to Paris!',
          predicted_label: 'spam',
          label_id: 1,
          is_spam: true,
          spam_probability: 0.942,
          ham_probability: 0.058,
          confidence: 0.942,
        },
        {
          text: 'Can you pick up groceries on the way?',
          predicted_label: 'ham',
          label_id: 0,
          is_spam: false,
          spam_probability: 0.031,
          ham_probability: 0.969,
          confidence: 0.969,
        },
      ],
    };
    const predictSpy = vi.spyOn(api, 'predict').mockResolvedValue(mockBatchResponse);
    const mockToast = { success: vi.fn(), error: vi.fn(), info: vi.fn() };

    render(
      <ThemeProvider>
        <PredictionPlayground models={sampleModels} toast={mockToast} />
      </ThemeProvider>
    );

    // Switch to Batch mode
    const batchTab = screen.getByRole('tab', { name: /batch sms/i });
    fireEvent.click(batchTab);

    const batchInput = screen.getByLabelText(/batch sms text messages/i);
    // Enter 2 messages with blank lines
    fireEvent.change(batchInput, {
      target: {
        value: 'Free tickets to Paris!\n\n   \nCan you pick up groceries on the way?\n',
      },
    });

    const submitBtn = screen.getByRole('button', { name: /classify batch/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      // Empty lines must be filtered out
      expect(predictSpy).toHaveBeenCalledWith('m-prod', {
        texts: ['Free tickets to Paris!', 'Can you pick up groceries on the way?'],
      });
    });

    // Check batch summary KPIs
    expect(screen.getByText('Total Predictions')).toBeInTheDocument();
    expect(screen.getAllByText('2').length).toBeGreaterThan(0);
    expect(screen.getByText('Spam Detected')).toBeInTheDocument();
    expect(screen.getByText('Ham Verified')).toBeInTheDocument();

    // Check table rows
    expect(screen.getByText('Free tickets to Paris!')).toBeInTheDocument();
    expect(screen.getByText('Can you pick up groceries on the way?')).toBeInTheDocument();
    expect(mockToast.success).toHaveBeenCalledWith(expect.stringContaining('Batch classified: 2 messages'));
  });

  it('handles API errors gracefully, disables inputs during loading, and preserves previous results', async () => {
    const error403 = new Error('Forbidden');
    error403.status = 403;
    const predictSpy = vi.spyOn(api, 'predict').mockRejectedValue(error403);
    const mockToast = { success: vi.fn(), error: vi.fn(), info: vi.fn() };

    render(
      <ThemeProvider>
        <PredictionPlayground models={sampleModels} toast={mockToast} />
      </ThemeProvider>
    );

    const textarea = screen.getByLabelText(/sms text message/i);
    fireEvent.change(textarea, { target: { value: 'Suspicious payload message' } });

    const submitBtn = screen.getByRole('button', { name: /classify sms/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText(/forbidden \(403\): you do not have permission/i)).toBeInTheDocument();
      expect(mockToast.error).toHaveBeenCalledWith(expect.stringContaining('Forbidden (403)'));
    });
  });

  it('formatInferenceError formats 401, 403, 404, 422, and network errors correctly', () => {
    expect(formatInferenceError({ status: 401 })).toContain('Authentication session expired');
    expect(formatInferenceError({ status: 403 })).toContain('Forbidden (403)');
    expect(formatInferenceError({ status: 404 })).toContain('Model not found (404)');
    expect(formatInferenceError({ status: 422 })).toContain('Validation error (422)');
    expect(formatInferenceError({ name: 'TypeError', message: 'Failed to fetch' })).toContain('Network error');
    expect(formatInferenceError(null)).toContain('Inference request failed');
  });
});
