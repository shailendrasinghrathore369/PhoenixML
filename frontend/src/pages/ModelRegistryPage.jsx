import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  Cpu,
  PlusCircle,
  Pencil,
  Trash2,
  Play,
  RotateCcw,
  Search,
  AlertCircle,
  X,
  ArrowLeft,
  FlaskConical,
  FileCode,
  Archive,
  ShieldAlert,
} from 'lucide-react';
import { PageHeader } from '../components/PageHeader.jsx';
import { MetricCard } from '../components/MetricCard.jsx';
import { StatusBadge } from '../components/StatusBadge.jsx';
import { DataTable } from '../components/DataTable.jsx';
import { ConfirmationDialog } from '../components/ConfirmationDialog.jsx';
import { LoadingState } from '../components/LoadingState.jsx';
import { EmptyState } from '../components/EmptyState.jsx';
import { PredictionPlayground } from '../components/PredictionPlayground.jsx';
import { api } from '../lib/api.js';
import { cn, formatDate } from '../lib/utils.js';

const DEFAULT_INITIAL_DATA = Object.freeze({});

/**
 * Accessible Modal Dialog for Model Registration & Editing
 */
function ModelFormModal({
  isOpen,
  onClose,
  onSubmit,
  initialData = DEFAULT_INITIAL_DATA,
  title = 'Register New Model',
  confirmText = 'Register Model',
  loading = false,
}) {
  const [formData, setFormData] = useState({
    name: initialData?.name || '',
    framework: initialData?.framework || '',
    algorithm: initialData?.algorithm || '',
    description: initialData?.description || '',
    status: initialData?.status || 'DEVELOPMENT',
  });
  const [errors, setErrors] = useState({});
  const dialogRef = useRef(null);
  const previouslyFocusedElement = useRef(null);

  useEffect(() => {
    if (isOpen) {
      setFormData({
        name: initialData?.name || '',
        framework: initialData?.framework || '',
        algorithm: initialData?.algorithm || '',
        description: initialData?.description || '',
        status: initialData?.status || 'DEVELOPMENT',
      });
      setErrors({});
    }
  }, [
    isOpen,
    initialData?.name,
    initialData?.framework,
    initialData?.algorithm,
    initialData?.description,
    initialData?.status,
  ]);

  // Focus trap, initial focus, escape key handler, and focus return
  useEffect(() => {
    if (!isOpen) return;

    // Save invoking element to restore focus on close
    previouslyFocusedElement.current = document.activeElement;

    // Focus first interactive control after modal mounts
    const timer = setTimeout(() => {
      if (!dialogRef.current) return;
      const focusable = dialogRef.current.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );
      if (focusable.length > 0) {
        focusable[0].focus();
      } else {
        dialogRef.current.focus();
      }
    }, 0);

    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && !loading) {
        e.preventDefault();
        onClose();
        return;
      }

      if (e.key === 'Tab' && dialogRef.current) {
        const focusable = dialogRef.current.querySelectorAll(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        if (focusable.length === 0) return;

        const firstElement = focusable[0];
        const lastElement = focusable[focusable.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      clearTimeout(timer);
      window.removeEventListener('keydown', handleKeyDown);
      if (previouslyFocusedElement.current && typeof previouslyFocusedElement.current.focus === 'function') {
        previouslyFocusedElement.current.focus();
      }
    };
  }, [isOpen, loading, onClose]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    const newErrors = {};
    if (!formData.name.trim()) {
      newErrors.name = 'Model name is required.';
    }
    if (!formData.framework.trim()) {
      newErrors.framework = 'Framework specification is required.';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});
    onSubmit({
      name: formData.name.trim(),
      framework: formData.framework.trim(),
      algorithm: formData.algorithm.trim() || null,
      description: formData.description.trim() || null,
      status: formData.status,
    });
  };

  return (
    <div
      className="dialog-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="model-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget && !loading) onClose();
      }}
    >
      <div ref={dialogRef} className="dialog-card" tabIndex={-1}>
        <div className="dialog-header">
          <div className="dialog-title-group">
            <div className="dialog-icon-box primary">
              <Cpu className="icon-md" aria-hidden="true" />
            </div>
            <h2 id="model-modal-title" className="dialog-title">
              {title}
            </h2>
          </div>
          <button
            type="button"
            className="dialog-close-btn"
            onClick={onClose}
            disabled={loading}
            aria-label="Close dialog"
          >
            <X className="icon-sm" aria-hidden="true" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="dialog-body modal-form-grid">
            <div className="form-group">
              <label className="form-label" htmlFor="model-name">
                Model Name *
              </label>
              <input
                id="model-name"
                type="text"
                className={cn('form-input', errors.name && 'input-error')}
                placeholder="e.g., SpamSMS-DistilBERT"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                disabled={loading}
                autoFocus
                maxLength={255}
              />
              {errors.name && <div className="form-field-error">{errors.name}</div>}
            </div>

            <div className="modal-form-row">
              <div className="form-group">
                <label className="form-label" htmlFor="model-framework">
                  Framework *
                </label>
                <input
                  id="model-framework"
                  type="text"
                  className={cn('form-input', errors.framework && 'input-error')}
                  placeholder="e.g., scikit-learn, PyTorch"
                  value={formData.framework}
                  onChange={(e) => setFormData({ ...formData, framework: e.target.value })}
                  disabled={loading}
                  maxLength={50}
                />
                {errors.framework && <div className="form-field-error">{errors.framework}</div>}
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="model-algorithm">
                  Algorithm
                </label>
                <input
                  id="model-algorithm"
                  type="text"
                  className="form-input"
                  placeholder="e.g., LogisticRegression"
                  value={formData.algorithm}
                  onChange={(e) => setFormData({ ...formData, algorithm: e.target.value })}
                  disabled={loading}
                  maxLength={100}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="model-status">
                Lifecycle Status
              </label>
              <select
                id="model-status"
                className="form-input"
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                disabled={loading}
              >
                <option value="DEVELOPMENT">DEVELOPMENT (Candidate / In-Training)</option>
                <option value="ACTIVE">ACTIVE (Production Inference)</option>
                <option value="ARCHIVED">ARCHIVED (Retired)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="model-description">
                Description & Provenance
              </label>
              <textarea
                id="model-description"
                className="form-input form-textarea"
                placeholder="Describe model architecture, serialization artifact path, or training dataset..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                disabled={loading}
                maxLength={1000}
                rows={3}
              />
            </div>
          </div>

          <div className="dialog-actions">
            <button
              type="button"
              className="btn btn-outline"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading && <span className="dialog-btn-spinner" aria-hidden="true" />}
              <span>{loading ? 'Saving...' : confirmText}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/**
 * Functional PhoenixML Model Registry Console
 */
export function ModelRegistryPage({
  user,
  dashboardData,
  loading: initialLoading = false,
  onNavigate,
  onRefresh,
  toast,
}) {
  const [models, setModels] = useState([]);
  const [loadingModels, setLoadingModels] = useState(true);
  const [fetchError, setFetchError] = useState(null);
  const [activeTab, setActiveTab] = useState('inventory'); // 'inventory' | 'playground'
  const [selectedModelId, setSelectedModelId] = useState(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Modals & Action States
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [editingModel, setEditingModel] = useState(null);
  const [deletingModel, setDeletingModel] = useState(null);
  const [actionLoading, setActionLoading] = useState(null);

  // Safe toast notifier
  const notify = useMemo(() => {
    return {
      success: (msg) => toast?.success?.(msg),
      error: (msg) => toast?.error?.(msg),
      info: (msg) => toast?.info?.(msg),
      warning: (msg) => toast?.warning?.(msg),
    };
  }, [toast]);

  // RBAC permissions based on authenticated user
  const isAdmin = user?.role === 'ADMIN';
  const isMLEngineer = user?.role === 'ML_ENGINEER';
  const isViewer = user?.role === 'VIEWER';
  const canCreate = isAdmin || isMLEngineer;

  const canEditModel = useCallback((model) => {
    if (!model) return false;
    if (isAdmin) return true;
    if (isMLEngineer && model.owner_id === user?.id) return true;
    return false;
  }, [isAdmin, isMLEngineer, user?.id]);

  const canDeleteModel = useCallback((model) => {
    if (!model) return false;
    if (isAdmin) return true;
    if (isMLEngineer && model.owner_id === user?.id) return true;
    return false;
  }, [isAdmin, isMLEngineer, user?.id]);

  // Fetch model inventory
  const fetchModels = useCallback(async () => {
    setLoadingModels(true);
    setFetchError(null);
    try {
      const data = await api.listModels({ skip: 0, limit: 100 });
      setModels(Array.isArray(data) ? data : []);
    } catch (err) {
      setFetchError(err.message || 'Failed to load model registry inventory.');
      notify.error(err.message || 'Failed to fetch registered models.');
    } finally {
      setLoadingModels(false);
    }
  }, [notify]);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  // Calculate inventory metrics
  const metrics = useMemo(() => {
    if (models.length > 0) {
      return {
        total: models.length,
        active: models.filter((m) => m.status === 'ACTIVE').length,
        development: models.filter((m) => m.status === 'DEVELOPMENT').length,
        archived: models.filter((m) => m.status === 'ARCHIVED').length,
      };
    }
    const summary = dashboardData?.models_summary || {};
    return {
      total: summary.total_models || 0,
      active: summary.active_models || 0,
      development: summary.development_models || 0,
      archived: summary.archived_models || 0,
    };
  }, [models, dashboardData]);

  // Filter models
  const filteredModels = useMemo(() => {
    return models.filter((m) => {
      const matchesStatus = statusFilter === 'ALL' || m.status === statusFilter;
      const q = searchQuery.trim().toLowerCase();
      const matchesSearch =
        !q ||
        m.name?.toLowerCase().includes(q) ||
        m.framework?.toLowerCase().includes(q) ||
        m.algorithm?.toLowerCase().includes(q) ||
        m.description?.toLowerCase().includes(q);
      return matchesStatus && matchesSearch;
    });
  }, [models, statusFilter, searchQuery]);

  // Handle register model submit
  const handleRegisterSubmit = async (payload) => {
    setActionLoading('create');
    try {
      const created = await api.createModel(payload);
      notify.success(`Model "${created.name}" registered successfully.`);
      setIsRegisterOpen(false);
      await fetchModels();
      onRefresh?.();
    } catch (err) {
      notify.error(`Failed to register model: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Handle edit model submit
  const handleEditSubmit = async (payload) => {
    if (!editingModel) return;
    setActionLoading('update');
    try {
      const updated = await api.updateModel(editingModel.id, payload);
      notify.success(`Model "${updated.name}" updated successfully.`);
      setEditingModel(null);
      await fetchModels();
      onRefresh?.();
    } catch (err) {
      notify.error(`Failed to update model: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Handle delete model confirm
  const handleDeleteConfirm = async () => {
    if (!deletingModel) return;
    setActionLoading('delete');
    try {
      await api.deleteModel(deletingModel.id);
      notify.success(`Model "${deletingModel.name}" deleted successfully.`);
      setDeletingModel(null);
      await fetchModels();
      onRefresh?.();
    } catch (err) {
      notify.error(`Failed to delete model: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Handle Playground navigation
  const handleTestInPlayground = (model) => {
    setSelectedModelId(model.id);
    setActiveTab('playground');
    notify.info(`Selected "${model.name}" for Prediction Playground.`);
  };

  // Selected model object for Playground tab
  const selectedModel = useMemo(() => {
    if (!selectedModelId) return models[0] || null;
    return models.find((m) => m.id === selectedModelId) || models[0] || null;
  }, [models, selectedModelId]);

  // DataTable columns definition
  const columns = useMemo(() => [
    {
      key: 'name',
      header: 'Model Name',
      render: (val, row) => (
        <div className="model-name-cell">
          <span className="model-name-title">{row.name}</span>
          {row.description && (
            <span className="model-desc-subtext" title={row.description}>
              {row.description}
            </span>
          )}
        </div>
      ),
    },
    {
      key: 'framework',
      header: 'Framework',
      render: (val) => val || 'scikit-learn',
    },
    {
      key: 'algorithm',
      header: 'Algorithm',
      render: (val) => val || 'N/A',
    },
    {
      key: 'status',
      header: 'Status',
      render: (val) => {
        const variant = val === 'ACTIVE' ? 'healthy' : val === 'DEVELOPMENT' ? 'info' : 'neutral';
        return (
          <StatusBadge variant={variant} size="sm">
            {val}
          </StatusBadge>
        );
      },
    },
    {
      key: 'created_at',
      header: 'Created Date',
      render: (val) => formatDate(val),
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right',
      render: (_, row) => (
        <div className="table-actions-cell">
          <button
            type="button"
            className="table-action-btn primary"
            onClick={() => handleTestInPlayground(row)}
            title="Test model in Prediction Playground"
            aria-label={`Test ${row.name} in Playground`}
          >
            <Play className="icon-xs" aria-hidden="true" />
            <span>Playground</span>
          </button>
          {canEditModel(row) && (
            <button
              type="button"
              className="table-action-btn"
              onClick={() => setEditingModel(row)}
              title="Edit model metadata"
              aria-label={`Edit ${row.name}`}
            >
              <Pencil className="icon-xs" aria-hidden="true" />
              <span>Edit</span>
            </button>
          )}
          {canDeleteModel(row) && (
            <button
              type="button"
              className="table-action-btn danger"
              onClick={() => setDeletingModel(row)}
              title="Delete model"
              aria-label={`Delete ${row.name}`}
            >
              <Trash2 className="icon-xs" aria-hidden="true" />
              <span>Delete</span>
            </button>
          )}
        </div>
      ),
    },
  ], [canEditModel, canDeleteModel]);

  return (
    <div className="dashboard-content">
      {/* Page Header */}
      <PageHeader
        icon={Cpu}
        title="Model Registry & Governance"
        subtitle="Centralized inventory for registering, versioning, inspecting, and archiving PhoenixML spam detection models."
        badge={
          isViewer ? (
            <StatusBadge variant="viewer" size="sm">
              Viewer (Read-Only)
            </StatusBadge>
          ) : null
        }
        actions={
          canCreate ? (
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => setIsRegisterOpen(true)}
              aria-label="Register Model"
            >
              <PlusCircle className="icon-xs" aria-hidden="true" />
              <span>Register Model</span>
            </button>
          ) : null
        }
      />

      {/* Model Inventory Summary Metrics */}
      <div className="kpi-grid">
        <MetricCard
          icon={Cpu}
          title="Total Registered Models"
          value={metrics.total}
          subtext="Configured in database"
          badge={
            <StatusBadge variant="healthy" size="sm">
              {metrics.active} Active
            </StatusBadge>
          }
        />
        <MetricCard
          icon={FileCode}
          title="In Development"
          value={metrics.development}
          subtext="Candidate models undergoing training"
        />
        <MetricCard
          icon={Archive}
          title="Archived Models"
          value={metrics.archived}
          subtext="Retired from production serving"
        />
        <MetricCard
          icon={ShieldAlert}
          title="Access Policy"
          value={user?.role || 'VIEWER'}
          subtext={
            isAdmin
              ? 'Unrestricted Fleet Access'
              : isMLEngineer
              ? 'Owned Models Access'
              : 'Read-Only Access'
          }
          badge={
            <StatusBadge
              variant={isAdmin ? 'admin' : isMLEngineer ? 'ml-engineer' : 'viewer'}
              size="sm"
            >
              {user?.role || 'VIEWER'}
            </StatusBadge>
          }
        />
      </div>

      {/* Sub-Tab Navigation Bar */}
      <div className="tab-nav" role="tablist" aria-label="Model Registry Views">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'inventory'}
          className={cn('tab-nav-item', activeTab === 'inventory' && 'active')}
          onClick={() => setActiveTab('inventory')}
        >
          <Cpu className="icon-xs" aria-hidden="true" />
          <span>Model Inventory</span>
          <span className="tab-badge">{models.length}</span>
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'playground'}
          className={cn('tab-nav-item', activeTab === 'playground' && 'active')}
          onClick={() => setActiveTab('playground')}
        >
          <FlaskConical className="icon-xs" aria-hidden="true" />
          <span>Prediction Playground</span>
        </button>
      </div>

      {/* Tab View 1: Model Inventory */}
      {activeTab === 'inventory' && (
        <section className="section" aria-label="Model Inventory Section">
          {/* Filter and Search Bar */}
          <div className="registry-filter-bar">
            <div className="registry-search-wrap">
              <Search className="icon-xs text-muted" aria-hidden="true" />
              <input
                type="search"
                className="form-input"
                placeholder="Search models by name, framework, or algorithm..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                aria-label="Search models"
              />
            </div>

            <div className="registry-filter-actions">
              <select
                className="form-input"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                aria-label="Filter models by status"
              >
                <option value="ALL">All Statuses ({models.length})</option>
                <option value="ACTIVE">Active ({metrics.active})</option>
                <option value="DEVELOPMENT">Development ({metrics.development})</option>
                <option value="ARCHIVED">Archived ({metrics.archived})</option>
              </select>

              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={fetchModels}
                disabled={loadingModels}
                title="Refresh model inventory"
                aria-label="Refresh model inventory"
              >
                <RotateCcw className={cn('icon-xs', loadingModels && 'spin')} aria-hidden="true" />
                <span>Refresh</span>
              </button>
            </div>
          </div>

          {/* Fetch Error Alert */}
          {fetchError && models.length === 0 && (
            <div className="alert alert-error mb-4" role="alert">
              <AlertCircle className="icon-sm" aria-hidden="true" />
              <span>{fetchError}</span>
              <button
                type="button"
                className="btn btn-outline btn-sm ml-auto"
                onClick={fetchModels}
              >
                Retry
              </button>
            </div>
          )}

          {/* Inventory Table Card */}
          <div className="table-card">
            {loadingModels && models.length === 0 ? (
              <LoadingState message="Loading registered models inventory..." />
            ) : filteredModels.length === 0 && searchQuery ? (
              <EmptyState
                icon={Search}
                title="No Matching Models"
                description={`No models found matching "${searchQuery}". Clear your search or filter to see registered models.`}
                action={
                  <button
                    type="button"
                    className="btn btn-outline btn-sm"
                    onClick={() => {
                      setSearchQuery('');
                      setStatusFilter('ALL');
                    }}
                  >
                    Reset Filters
                  </button>
                }
              />
            ) : (
              <DataTable
                columns={columns}
                data={filteredModels}
                keyField="id"
                emptyTitle="No Registered Models"
                emptyDescription="No spam classification models have been configured in the database yet. Use '+ Register Model' above to configure your first pipeline."
              />
            )}
          </div>
        </section>
      )}

      {/* Tab View 2: Prediction Playground */}
      {activeTab === 'playground' && (
        <section className="section" aria-label="Prediction Playground Section">
          <PredictionPlayground
            models={models}
            selectedModelId={selectedModelId}
            onSelectModelId={setSelectedModelId}
            onNavigateToInventory={() => setActiveTab('inventory')}
            toast={notify}
          />
        </section>
      )}

      {/* Register Model Modal */}
      <ModelFormModal
        isOpen={isRegisterOpen}
        onClose={() => setIsRegisterOpen(false)}
        onSubmit={handleRegisterSubmit}
        title="Register New Spam Model"
        confirmText="Register Model"
        loading={actionLoading === 'create'}
      />

      {/* Edit Model Modal */}
      {editingModel && (
        <ModelFormModal
          isOpen={!!editingModel}
          onClose={() => setEditingModel(null)}
          onSubmit={handleEditSubmit}
          initialData={editingModel}
          title={`Edit Model: ${editingModel.name}`}
          confirmText="Save Changes"
          loading={actionLoading === 'update'}
        />
      )}

      {/* Delete Model Confirmation Dialog */}
      <ConfirmationDialog
        isOpen={!!deletingModel}
        onClose={() => setDeletingModel(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Registered Model"
        description={`Are you sure you want to permanently delete "${deletingModel?.name}"? All associated monitoring observations and decision governance history will be removed.`}
        confirmText="Delete Model"
        confirmVariant="danger"
        loading={actionLoading === 'delete'}
      />
    </div>
  );
}

export default ModelRegistryPage;
