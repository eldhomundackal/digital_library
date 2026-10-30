import axios from 'axios'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Toaster } from 'react-hot-toast'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { getApiError } from '@/api/client'
import App from './App.tsx'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      throwOnError: false,
      retry: (failureCount, error) => {
        if (axios.isAxiosError(error)) {
          const status = error.response?.status
          if (status === 401 || status === 403 || status === 404) return false
        }
        return failureCount < 2
      },
    },
    mutations: {
      onError: (error) => {
        console.error(getApiError(error))
      },
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <Toaster position="top-right" />
    </QueryClientProvider>
  </StrictMode>,
)
