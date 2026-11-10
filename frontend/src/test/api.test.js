import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { api, authStorage } from '../api.js';

describe('PhoenixML Frontend API Client (api.js)', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    localStorage.clear();
  });

  describe('authStorage', () => {
    it('manages access token, refresh token, and user profile in localStorage', () => {
      expect(authStorage.getToken()).toBeNull();
      expect(authStorage.getRefreshToken()).toBeNull();
      expect(authStorage.getUser()).toBeNull();

      authStorage.setToken('test-access-token');
      authStorage.setRefreshToken('test-refresh-token');
      authStorage.setUser({ id: 'u1', username: 'admin', role: 'ADMIN' });

      expect(authStorage.getToken()).toBe('test-access-token');
      expect(authStorage.getRefreshToken()).toBe('test-refresh-token');
      expect(authStorage.getUser()).toEqual({ id: 'u1', username: 'admin', role: 'ADMIN' });

      authStorage.clearToken();
      expect(authStorage.getToken()).toBeNull();
      expect(authStorage.getRefreshToken()).toBeNull();
      expect(authStorage.getUser()).toBeNull();
    });

    it('handles malformed JSON in localStorage gracefully', () => {
      localStorage.setItem('phoenixml_user', '{bad-json');
      expect(authStorage.getUser()).toBeNull();
    });
  });

  describe('api.listModels', () => {
    it('sends GET /api/spam-models with default pagination query params', async () => {
      const mockModels = [
        { id: 'm1', name: 'SpamSMS-LogisticRegression', framework: 'scikit-learn', status: 'ACTIVE' },
        { id: 'm2', name: 'Candidate-NB', framework: 'scikit-learn', status: 'DEVELOPMENT' },
      ];

      authStorage.setToken('auth-token-123');

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockModels,
      });

      const result = await api.listModels();

      expect(global.fetch).toHaveBeenCalledTimes(1);
      const [url, options] = global.fetch.mock.calls[0];
      expect(url).toContain('/api/spam-models?skip=0&limit=100');
      expect(options.headers['Authorization']).toBe('Bearer auth-token-123');
      expect(result).toEqual(mockModels);
    });

    it('sends custom skip and limit pagination parameters', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => [],
      });

      await api.listModels({ skip: 20, limit: 10 });
      const [url] = global.fetch.mock.calls[0];
      expect(url).toContain('/api/spam-models?skip=20&limit=10');
    });

    it('handles HTTP error responses and preserves backend error detail', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'Database connection failure' }),
      });

      await expect(api.listModels()).rejects.toThrow('Database connection failure');
    });
  });

  describe('api.getModel', () => {
    it('sends GET /api/spam-models/{modelId} and returns model details', async () => {
      const mockModel = {
        id: '6b29fc40-c112-4f36-9b57-6e9f1a23c890',
        name: 'SpamSMS-LogisticRegression',
        framework: 'scikit-learn',
        algorithm: 'LogisticRegression',
        status: 'ACTIVE',
        owner_id: 'user-1',
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockModel,
      });

      const result = await api.getModel('6b29fc40-c112-4f36-9b57-6e9f1a23c890');
      const [url] = global.fetch.mock.calls[0];
      expect(url).toContain('/api/spam-models/6b29fc40-c112-4f36-9b57-6e9f1a23c890');
      expect(result).toEqual(mockModel);
    });

    it('throws error with 404 status when model is not found', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'Model not found' }),
      });

      await expect(api.getModel('non-existent-id')).rejects.toThrow('Model not found');
    });
  });

  describe('api.listObservations', () => {
    it('sends GET /api/spam-models/{modelId}/monitoring with default pagination query params', async () => {
      const mockObservations = [
        {
          id: 'obs-1',
          model_id: 'model-123',
          observed_at: '2026-11-09T10:00:00Z',
          prediction_count: 100,
          positive_prediction_count: 15,
          negative_prediction_count: 85,
          accuracy: 0.98,
          precision: 0.95,
          recall: 0.92,
          f1_score: 0.935,
        },
      ];

      authStorage.setToken('auth-token-123');

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockObservations,
      });

      const result = await api.listObservations('model-123');

      expect(global.fetch).toHaveBeenCalledTimes(1);
      const [url, options] = global.fetch.mock.calls[0];
      expect(url).toContain('/api/spam-models/model-123/monitoring?skip=0&limit=100');
      expect(options.headers['Authorization']).toBe('Bearer auth-token-123');
      expect(result).toEqual(mockObservations);
    });

    it('sends custom skip and limit pagination parameters and properly encodes modelId', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => [],
      });

      await api.listObservations('model/with-slash', { skip: 25, limit: 50 });
      const [url] = global.fetch.mock.calls[0];
      expect(url).toContain('/api/spam-models/model%2Fwith-slash/monitoring?skip=25&limit=50');
    });

    it('handles HTTP error responses and preserves backend error detail', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'Model not found' }),
      });

      await expect(api.listObservations('missing-model')).rejects.toThrow('Model not found');
    });
  });

  describe('api.getObservation', () => {
    it('sends GET /api/spam-models/{modelId}/monitoring/{observationId} and returns observation details', async () => {
      const mockObservation = {
        id: 'obs-uuid-456',
        model_id: 'model-123',
        observed_at: '2026-11-09T10:00:00Z',
        prediction_count: 50,
        accuracy: 0.97,
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockObservation,
      });

      const result = await api.getObservation('model-123', 'obs-uuid-456');
      const [url] = global.fetch.mock.calls[0];
      expect(url).toContain('/api/spam-models/model-123/monitoring/obs-uuid-456');
      expect(result).toEqual(mockObservation);
    });

    it('throws error with 404 status when observation is not found', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'Observation not found' }),
      });

      await expect(api.getObservation('model-123', 'non-existent-obs')).rejects.toThrow('Observation not found');
    });
  });

  describe('api.createModel', () => {
    it('sends POST /api/spam-models with JSON payload and returns created model', async () => {
      const newModelPayload = {
        name: 'Production-BERT',
        description: 'Deep NLP spam filter',
        framework: 'PyTorch',
        algorithm: 'Transformer',
        status: 'DEVELOPMENT',
      };

      const createdModelResponse = {
        id: 'new-model-uuid-1234',
        ...newModelPayload,
        owner_id: 'admin-user-id',
        created_at: '2026-11-09T12:00:00Z',
        updated_at: '2026-11-09T12:00:00Z',
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 201,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => createdModelResponse,
      });

      const result = await api.createModel(newModelPayload);
      const [url, options] = global.fetch.mock.calls[0];

      expect(url).toContain('/api/spam-models');
      expect(options.method).toBe('POST');
      expect(options.headers['Content-Type']).toBe('application/json');
      expect(JSON.parse(options.body)).toEqual(newModelPayload);
      expect(result).toEqual(createdModelResponse);
    });

    it('handles 422 Unprocessable Entity with validation details array', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({
          detail: [
            { loc: ['body', 'name'], msg: 'Field required', type: 'missing' },
            { loc: ['body', 'framework'], msg: 'Field required', type: 'missing' },
          ],
        }),
      });

      await expect(api.createModel({})).rejects.toThrow('Field required, Field required');
    });

    it('handles 403 Forbidden when user role lacks creation privileges', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 403,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'Not authorized to create models' }),
      });

      await expect(api.createModel({ name: 'Test', framework: 'scikit-learn' })).rejects.toThrow(
        'Not authorized to create models'
      );
    });
  });

  describe('api.updateModel', () => {
    it('sends PUT /api/spam-models/{modelId} with partial update payload', async () => {
      const updatePayload = {
        status: 'ACTIVE',
        description: 'Promoted to active serving',
      };

      const updatedModelResponse = {
        id: 'model-123',
        name: 'SpamSMS-LogisticRegression',
        framework: 'scikit-learn',
        status: 'ACTIVE',
        description: 'Promoted to active serving',
        updated_at: '2026-11-09T13:00:00Z',
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => updatedModelResponse,
      });

      const result = await api.updateModel('model-123', updatePayload);
      const [url, options] = global.fetch.mock.calls[0];

      expect(url).toContain('/api/spam-models/model-123');
      expect(options.method).toBe('PUT');
      expect(options.headers['Content-Type']).toBe('application/json');
      expect(JSON.parse(options.body)).toEqual(updatePayload);
      expect(result).toEqual(updatedModelResponse);
    });

    it('handles 404 when updating a nonexistent model', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'Model not found' }),
      });

      await expect(api.updateModel('unknown-id', { status: 'ARCHIVED' })).rejects.toThrow('Model not found');
    });
  });

  describe('api.deleteModel', () => {
    it('sends DELETE /api/spam-models/{modelId} and returns null on 204 No Content without body parsing', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 204,
        headers: new Headers(), // No Content-Type
        json: vi.fn(), // Should NOT be called
      });

      const result = await api.deleteModel('model-to-delete-123');
      const [url, options] = global.fetch.mock.calls[0];

      expect(url).toContain('/api/spam-models/model-to-delete-123');
      expect(options.method).toBe('DELETE');
      expect(result).toBeNull();
    });

    it('handles 403 Forbidden error on model deletion', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 403,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'Viewers cannot delete models' }),
      });

      await expect(api.deleteModel('model-123')).rejects.toThrow('Viewers cannot delete models');
    });
  });

  describe('api.predict', () => {
    const mockPredictionResponse = {
      model_id: 'model-123',
      model_name: 'SpamSMS-LogisticRegression',
      model_version: '1.0.0',
      total_predictions: 1,
      spam_count: 1,
      ham_count: 0,
      predictions: [
        {
          text: 'WINNER! Claim your free gift now!',
          predicted_label: 'spam',
          label_id: 1,
          is_spam: true,
          spam_probability: 0.985,
          ham_probability: 0.015,
          confidence: 0.985,
          model_name: 'SpamSMS-LogisticRegression',
          model_version: '1.0.0',
        },
      ],
    };

    it('sends single prediction with object payload { text: "..." }', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockPredictionResponse,
      });

      const result = await api.predict('model-123', { text: 'WINNER! Claim your free gift now!' });
      const [url, options] = global.fetch.mock.calls[0];

      expect(url).toContain('/api/spam-models/model-123/predict');
      expect(options.method).toBe('POST');
      expect(options.headers['Content-Type']).toBe('application/json');
      expect(JSON.parse(options.body)).toEqual({ text: 'WINNER! Claim your free gift now!' });
      expect(result).toEqual(mockPredictionResponse);
    });

    it('automatically normalizes string payload into { text: "..." }', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => mockPredictionResponse,
      });

      await api.predict('model-123', 'WINNER! Claim your free gift now!');
      const [, options] = global.fetch.mock.calls[0];

      expect(JSON.parse(options.body)).toEqual({ text: 'WINNER! Claim your free gift now!' });
    });

    it('sends batch prediction with object payload { texts: [...] }', async () => {
      const batchResponse = {
        model_id: 'model-123',
        model_name: 'SpamSMS-LogisticRegression',
        model_version: '1.0.0',
        total_predictions: 2,
        spam_count: 1,
        ham_count: 1,
        predictions: [
          { text: 'Hi mom', predicted_label: 'ham', is_spam: false, confidence: 0.99 },
          { text: 'Win $1000', predicted_label: 'spam', is_spam: true, confidence: 0.95 },
        ],
      };

      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => batchResponse,
      });

      const result = await api.predict('model-123', { texts: ['Hi mom', 'Win $1000'] });
      const [url, options] = global.fetch.mock.calls[0];

      expect(url).toContain('/api/spam-models/model-123/predict');
      expect(options.method).toBe('POST');
      expect(JSON.parse(options.body)).toEqual({ texts: ['Hi mom', 'Win $1000'] });
      expect(result.total_predictions).toBe(2);
      expect(result.spam_count).toBe(1);
    });

    it('automatically normalizes array payload into { texts: [...] }', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ total_predictions: 2, predictions: [] }),
      });

      await api.predict('model-123', ['Msg 1', 'Msg 2']);
      const [, options] = global.fetch.mock.calls[0];

      expect(JSON.parse(options.body)).toEqual({ texts: ['Msg 1', 'Msg 2'] });
    });

    it('handles prediction errors (e.g. 404 model not found, 422 invalid text)', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'Model not found' }),
      });

      await expect(api.predict('missing-model', 'Sample text')).rejects.toThrow('Model not found');
    });
  });

  describe('Session Expiration & Unauthorized Handling', () => {
    it('dispatches phoenixml-unauthorized event and clears storage on unresolvable 401', async () => {
      const listener = vi.fn();
      window.addEventListener('phoenixml-unauthorized', listener);

      authStorage.setToken('expired-token');
      // No refresh token available

      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'Signature has expired' }),
      });

      await expect(api.getModel('m1')).rejects.toThrow('Session expired or unauthenticated. Please log in.');
      expect(listener).toHaveBeenCalledTimes(1);
      expect(authStorage.getToken()).toBeNull();

      window.removeEventListener('phoenixml-unauthorized', listener);
    });
  });
});
