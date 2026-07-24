// API base URL. Set VITE_API_BASE in frontend/.env to point a build at a
// deployed API; falls back to the local dev server.
export const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:5000";
