/**
 * PhoenixML API Client Service
 * Centralizes REST communication with the FastAPI backend.
 */

const API_BASE_URL = window.location.origin.includes(':3000') || window.location.origin.includes(':5173')
  ? 'http://localhost:8000/api'
  : '/api';

const TOKEN_KEY = 'phoenixml_access_token';
const USER_KEY = 'phoenixml_user';

export const authStorage = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  setToken: (token) => localStorage.setItem(TOKEN_KEY, token),
  clearToken: () => {
    localStorage.removeItem(TOKEN_KEY);
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

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    authStorage.clearToken();
    window.dispatchEvent(new CustomEvent('phoenixml-unauthorized'));
    throw new Error('Session expired or unauthenticated. Please log in.');
  }

  let data = null;
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    data = await response.json();
  }

  if (!response.ok) {
    const errorDetail = (data && data.detail) ? data.detail : `HTTP Error ${response.status}`;
    const err = new Error(errorDetail);
    err.status = response.status;
    err.data = data;
    throw err;
  }

  return data;
}

export const api = {
  /**
   * Authenticate with username and password using OAuth2 Password Request.
   */
  login: async (username, password) => {
    const body = new URLSearchParams();
    body.append('username', username);
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
      // Fetch user profile immediately
      const profile = await api.getProfile();
      authStorage.setUser(profile);
      return { token: data.access_token, user: profile };
    }
    throw new Error('Login failed: token not returned.');
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

  logout: () => {
    authStorage.clearToken();
  },
};
