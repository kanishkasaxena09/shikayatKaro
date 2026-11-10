import axios from 'axios';

const rawBaseUrl = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? '' : 'https://shikayatkaro-backend.onrender.com');
const API_BASE_URL = rawBaseUrl.endsWith('/') ? rawBaseUrl.slice(0, -1) : rawBaseUrl;

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor to attach JWT Token
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
client.interceptors.response.use(
  (response) => response,
  (error) => {
    // Standardize error message extraction
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred';
    
    // Attach user-friendly parsed message
    error.userMessage = typeof message === 'string' ? message : JSON.stringify(message);
    return Promise.reject(error);
  }
);

export const api = {
  // Auth endpoints
  auth: {
    login: (credentials) => client.post('/api/auth/login', credentials),
    register: (userData) => client.post('/api/auth/register', userData),
    getMe: () => client.get('/api/auth/me'),
  },

  // Complaints endpoints
  complaints: {
    submit: (payload) => client.post('/api/complaints', payload),
    getMy: () => client.get('/api/complaints/my'),
    getById: (id) => client.get(`/api/complaints/${id}`),
    track: (trackingId, accessCode) => {
      const params = { tracking_id: trackingId };
      if (accessCode) params.access_code = accessCode;
      return client.get('/api/track', { params });
    },
  },

  // Suggestions endpoints
  suggestions: {
    list: (statusFilter = 'pending') =>
      client.get('/api/suggestions', { params: { status_filter: statusFilter } }),
    confirm: (id, payload = {}) => client.post(`/api/suggestions/${id}/confirm`, payload),
    reject: (id) => client.post(`/api/suggestions/${id}/reject`),
    removeComplaint: (id, complaintId) =>
      client.post(`/api/suggestions/${id}/remove-complaint`, { complaint_id: complaintId }),
  },

  // Incidents endpoints
  incidents: {
    list: (params = {}) => client.get('/api/incidents', { params }),
    getById: (id) => client.get(`/api/incidents/${id}`),
    assign: (id, departmentId, remarks) =>
      client.post(`/api/incidents/${id}/assign`, { department_id: departmentId, remarks }),
    updateStatus: (id, status, resolutionNotes, remarks) =>
      client.post(`/api/incidents/${id}/status`, {
        status,
        resolution_notes: resolutionNotes,
        remarks,
      }),
  },

  // Analytics endpoints
  analytics: {
    getHeatmap: (params = {}) => client.get('/api/heatmap', { params }),
    getDashboardSummary: () => client.get('/api/dashboard/summary'),
  },

  // Notifications endpoints
  notifications: {
    getMy: () => client.get('/api/notifications'),
    markRead: (id) => client.post(`/api/notifications/${id}/read`),
  },

  // Demo simulator endpoints
  demo: {
    loadStory: () => client.post('/api/demo/load-story'),
    advanceTime: (hours) => client.post('/api/demo/advance-time', { hours }),
    reset: () => client.post('/api/demo/reset'),
  },

  // System Health
  health: () => client.get('/api/health'),
};

export default client;
