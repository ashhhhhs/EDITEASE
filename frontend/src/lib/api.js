import axios from 'axios';
import { API_BASE } from '../config';

/**
 * Shared Axios instance for all EditEase API calls.
 * - Automatically attaches Bearer token from localStorage
 * - Errors are formatted and re-thrown; toast surfaces them globally via the hook
 */
const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// Attach auth token on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Normalize error messages — actual toasting is done in components or the interceptor below
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.error
      || error.response?.data?.message
      || error.message
      || 'An unexpected error occurred';
    // Attach the clean message to the error so callers can access it
    error.friendlyMessage = message;
    return Promise.reject(error);
  }
);

export default api;
