// src/config/api.ts
export const SERVER_HOST = import.meta.env.VITE_SERVER_HOST
export const BACKEND_PORT = import.meta.env.VITE_BACKEND_PORT
export const FRONTEND_PORT = import.meta.env.VITE_FRONTEND_PORT

export const BACKEND_URL = `http://${SERVER_HOST}:${BACKEND_PORT}`
export const FRONTEND_URL = `http://${SERVER_HOST}:${FRONTEND_PORT}`