/**
 * PhoenixML API Client Service
 * Centralizes REST communication with the FastAPI backend.
 */

const API_PORT = '8000';
const isDevPort = typeof window !== 'undefined' && window.location && (window.location.origin.includes(':3000') || window.location.origin.includes(':5173'));
const API_BASE_URL = isDevPort
  ? `http://${(window.location && window.location.hostname) || 'localhost'}:${API_PORT}/api`
  : '/api';

const TOKEN_KEY = 'phoenixml_access_token';
const REFRESH_TOKEN_KEY = 'phoenixml_refresh_token';
const USER_KEY = 'phoenixml_user';

export const authStorage = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  setToken: (token) => localStorage.setItem(TOKEN_KEY, token),
  getRefreshToken: () => localStorage.getItem(REFRESH_TOKEN_KEY),
  setRefreshToken: (token) => localStorage.setItem(REFRESH_TOKEN_KEY, token),
  clearToken: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
  getUser: () => {
    const raw = localStorage.getItem(USER_KEY);
    try {
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },
  setUser: (user) => localStorage.setItem(USER_KEY, JSON.stringify(user)),
};

async function apiRequest(endpoint, options = {}) {
  const token = authStorage.getToken();
  const headers = {
    'Accept': 'application/json',
    ...(options.headers || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // Handle 401 Unauthorized with token refresh if possible
  if (response.status === 401) {
    // Avoid refresh loops for auth endpoints
    if (!endpoint.startsWith('/auth/')) {
      const refreshToken = authStorage.getRefreshToken();
      if (refreshToken) {
        try {
          const refreshRes = await fetch(`${API_BASE_URL}/auth/refresh`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });

          if (refreshRes.ok) {
            const refreshData = await refreshRes.json();
            if (refreshData.access_token) {
              authStorage.setToken(refreshData.access_token);
              // Retry original request with newly issued access token
              headers['Authorization'] = `Bearer ${refreshData.access_token}`;
              response = await fetch(`${API_BASE_URL}${endpoint}`, {
                ...options,
                headers,
              });
            }
          }
        } catch {
          // Token refresh failed, fall through to clearing session
        }
      }
    }

    if (response.status === 401) {
      authStorage.clearToken();
      window.dispatchEvent(new CustomEvent('phoenixml-unauthorized', {
        detail: { reason: 'session_expired' }
      }));
      throw new Error('Session expired or unauthenticated. Please log in.');
    }
  }

  // Handle 204 No Content (e.g. DELETE) without attempting JSON body parsing
  if (response.status === 204) {
    return null;
  }

  let data = null;
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    data = await response.json();
  }

  if (!response.ok) {
    let errorDetail = `HTTP Error ${response.status}`;
    if (data && data.detail) {
      if (typeof data.detail === 'string') {
        errorDetail = data.detail;
      } else if (Array.isArray(data.detail)) {
        errorDetail = data.detail.map((d) => d.msg || JSON.stringify(d)).join(', ');
      } else {
        errorDetail = JSON.stringify(data.detail);
      }
    }
    const err = new Error(errorDetail);
    err.status = response.status;
    err.data = data;
    throw err;
  }

  return data;
}

export const api = {
  /**
   * Authenticate with username or email and password using OAuth2 Password Request.
   */
  login: async (username, password) => {
    const body = new URLSearchParams();
    body.append('username', username.trim());
    body.append('password', password);

    const data = await apiRequest('/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body.toString(),
    });

    if (data.access_token) {
      authStorage.setToken(data.access_token);
      if (data.refresh_token) {
        authStorage.setRefreshToken(data.refresh_token);
      }
      // Fetch user profile immediately
      const profile = await api.getProfile();
      authStorage.setUser(profile);
      return { token: data.access_token, user: profile };
    }
    throw new Error('Login failed: token not returned.');
  },

  /**
   * Register a new public user account with default VIEWER role.
   */
  register: async ({ username, email, password }) => {
    return apiRequest('/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        full_name: username.trim(),
        username: username.trim(),
        email: email.trim(),
        password: password,
      }),
    });
  },

  /**
   * Fetch authenticated user profile.
   */
  getProfile: async () => {
    return apiRequest('/users/me');
  },

  /**
   * Fetch consolidated dashboard overview metrics.
   */
  getDashboardOverview: async (modelId = null) => {
    const query = modelId ? `?model_id=${encodeURIComponent(modelId)}` : '';
    return apiRequest(`/dashboard${query}`);
  },

  /**
   * Run real reference or shifted model evaluation using the loaded artifact,
   * recording a genuine monitoring observation in PhoenixML.
   */
  evaluateModelTelemetry: async (modelId, payload = { dataset_name: 'reference', use_reference_test_set: true, record_monitoring_observation: true }) => {
    return apiRequest(`/spam-models/${encodeURIComponent(modelId)}/evaluate-telemetry`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
  },

  /**
   * List monitoring observations for a specific spam model with optional pagination.
   */
  listObservations: async (modelId, params = { skip: 0, limit: 100 }) => {
    const searchParams = new URLSearchParams();
    if (params?.skip !== undefined && params?.skip !== null) {
      searchParams.append('skip', String(params.skip));
    }
    if (params?.limit !== undefined && params?.limit !== null) {
      searchParams.append('limit', String(params.limit));
    }
    const query = searchParams.toString();
    return apiRequest(`/spam-models/${encodeURIComponent(modelId)}/monitoring${query ? `?${query}` : ''}`);
  },

  /**
   * Retrieve a specific monitoring observation for a model by UUID.
   */
  getObservation: async (modelId, observationId) => {
    return apiRequest(`/spam-models/${encodeURIComponent(modelId)}/monitoring/${encodeURIComponent(observationId)}`);
  },

  /**
   * Trigger AIMD model evaluation across monitoring observations.
   */
  evaluateModel: async (modelId) => {
    return apiRequest(`/spam-models/${encodeURIComponent(modelId)}/decisions/evaluate`, {
      method: 'POST',
    });
  },

  /**
   * Update human approval status of a decision (PENDING -> APPROVED or REJECTED).
   */
  updateApprovalStatus: async (modelId, decisionId, approvalStatus) => {
    return apiRequest(`/spam-models/${encodeURIComponent(modelId)}/decisions/${encodeURIComponent(decisionId)}/approval`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ approval_status: approvalStatus }),
    });
  },

  /**
   * List registered spam models with optional pagination.
   */
  listModels: async (params = { skip: 0, limit: 100 }) => {
    const searchParams = new URLSearchParams();
    if (params?.skip !== undefined && params?.skip !== null) {
      searchParams.append('skip', String(params.skip));
    }
    if (params?.limit !== undefined && params?.limit !== null) {
      searchParams.append('limit', String(params.limit));
    }
    const query = searchParams.toString();
    return apiRequest(`/spam-models${query ? `?${query}` : ''}`);
  },

  /**
   * Retrieve a single registered model by its UUID.
   */
  getModel: async (modelId) => {
    return apiRequest(`/spam-models/${encodeURIComponent(modelId)}`);
  },

  /**
   * Create and register a new spam model.
   */
  createModel: async (payload) => {
    return apiRequest('/spam-models', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
  },

  /**
   * Update an existing registered model's metadata or status.
   */
  updateModel: async (modelId, payload) => {
    return apiRequest(`/spam-models/${encodeURIComponent(modelId)}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
  },

  /**
   * Delete a registered model by its UUID.
   * Correctly handles 204 No Content without attempting JSON parsing.
   */
  deleteModel: async (modelId) => {
    return apiRequest(`/spam-models/${encodeURIComponent(modelId)}`, {
      method: 'DELETE',
    });
  },

  /**
   * Execute real-time deterministic spam/ham prediction on single or batch SMS messages.
   * Supports payload: { text: "..." } or { texts: ["...", "..."] }, as well as string / array inputs.
   */
  predict: async (modelId, payload) => {
    let bodyObj = payload;
    if (typeof payload === 'string') {
      bodyObj = { text: payload };
    } else if (Array.isArray(payload)) {
      bodyObj = { texts: payload };
    }
    return apiRequest(`/spam-models/${encodeURIComponent(modelId)}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(bodyObj),
    });
  },

  /**
   * Gracefully acknowledge logout and discard local credentials.
   */
  logout: async () => {
    try {
      const token = authStorage.getToken();
      if (token) {
        await fetch(`${API_BASE_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Accept': 'application/json',
          },
        });
      }
    } catch {
      // Ignore network errors on logout
    } finally {
      authStorage.clearToken();
    }
  },
};
