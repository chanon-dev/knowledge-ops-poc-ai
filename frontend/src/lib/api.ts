import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { getSession } from "next-auth/react";

const api = axios.create({
  baseURL: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 30000,
});

// Cache session to avoid calling /api/auth/session on every request
let cachedToken: string | null = null;
let tokenFetchPromise: Promise<string | null> | null = null;

async function getToken(): Promise<string | null> {
  if (cachedToken) return cachedToken;
  if (tokenFetchPromise) return tokenFetchPromise;
  tokenFetchPromise = getSession().then((session) => {
    cachedToken = session?.accessToken || null;
    tokenFetchPromise = null;
    return cachedToken;
  });
  return tokenFetchPromise;
}

export function clearTokenCache() {
  cachedToken = null;
  tokenFetchPromise = null;
}

// Request interceptor to attach auth token
api.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const token = await getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // Let axios set the correct Content-Type (with boundary) for FormData
    if (config.data instanceof FormData) {
      delete config.headers["Content-Type"];
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const status = error.response?.status;

    if (status === 401) {
      clearTokenCache();
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }

    if (status === 403) {
      console.error("Access forbidden:", error.response?.data);
    }

    if (status === 500) {
      console.error("Server error:", error.response?.data);
    }

    return Promise.reject(error);
  }
);

export { api };
export default api;

// Typed API helpers
export async function apiGet<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const response = await api.get<T>(url, { params });
  return response.data;
}

export async function apiPost<T>(url: string, data?: unknown): Promise<T> {
  const response = await api.post<T>(url, data);
  return response.data;
}

export async function apiPut<T>(url: string, data?: unknown): Promise<T> {
  const response = await api.put<T>(url, data);
  return response.data;
}

export async function apiDelete<T>(url: string): Promise<T> {
  const response = await api.delete<T>(url);
  return response.data;
}
