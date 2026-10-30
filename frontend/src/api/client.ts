import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let isRefreshing = false
let refreshQueue: Array<(token: string) => void> = []

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true

      if (isRefreshing) {
        return new Promise((resolve) => {
          refreshQueue.push((token) => {
            original.headers.Authorization = `Bearer ${token}`
            resolve(apiClient(original))
          })
        })
      }

      isRefreshing = true

      try {
        const { data } = await apiClient.post('/auth/refresh')
        const newToken = data.data.access_token
        useAuthStore.getState().setAccessToken(newToken)

        refreshQueue.forEach((cb) => cb(newToken))
        refreshQueue = []

        original.headers.Authorization = `Bearer ${newToken}`
        return apiClient(original)
      } catch {
        useAuthStore.getState().logout()
        window.location.href = '/login'
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

// Typed wrappers that unwrap the backend's { data: T, message: string } envelope.
// Use these in every hook instead of apiClient directly.
export const api = {
  get: async <T>(url: string, config?: Parameters<typeof apiClient.get>[1]): Promise<T> => {
    const { data } = await apiClient.get<{ data: T }>(url, config)
    return data.data
  },
  post: async <T>(url: string, body?: unknown, config?: Parameters<typeof apiClient.post>[2]): Promise<T> => {
    const { data } = await apiClient.post<{ data: T }>(url, body, config)
    return data.data
  },
  patch: async <T>(url: string, body?: unknown, config?: Parameters<typeof apiClient.patch>[2]): Promise<T> => {
    const { data } = await apiClient.patch<{ data: T }>(url, body, config)
    return data.data
  },
  delete: async <T = void>(url: string, config?: Parameters<typeof apiClient.delete>[1]): Promise<T> => {
    const { data } = await apiClient.delete<{ data: T }>(url, config)
    return data.data
  },
}

export function getApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.message ?? 'Something went wrong.'
  }
  return 'Something went wrong.'
}

export function getFieldErrors(error: unknown): Record<string, string> {
  if (axios.isAxiosError(error)) {
    const errors = error.response?.data?.errors
    if (errors && typeof errors === 'object') {
      return Object.fromEntries(
        Object.entries(errors).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v])
      )
    }
  }
  return {}
}
