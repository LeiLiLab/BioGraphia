// src/config/api.ts
export const SERVER_HOST = import.meta.env.VITE_SERVER_HOST
export const BACKEND_PORT = import.meta.env.VITE_BACKEND_PORT
export const FRONTEND_PORT = import.meta.env.VITE_FRONTEND_PORT

// Use relative URL for API requests that will work with the proxy
export const BACKEND_URL = '' // Empty string to make all api requests relative
export const FRONTEND_URL = `http://${SERVER_HOST}:${FRONTEND_PORT}`