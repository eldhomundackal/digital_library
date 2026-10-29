import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { apiClient, getApiError } from '@/api/client'
import type { DownloadHistoryItem, DownloadResponse } from '@/types/download'
import type { PaginatedResponse } from '@/types/common'

export function useDownloadBook() {
  return useMutation({
    mutationFn: async (bookId: string) => {
      const { data } = await apiClient.post<DownloadResponse>(`/books/${bookId}/download/`)
      return data
    },
    onSuccess: (data) => {
      // Open the URL immediately — never store it
      window.open(data.download_url, '_blank', 'noopener,noreferrer')
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useDownloadHistory(page = 1, limit = 20) {
  return useQuery({
    queryKey: ['download-history', page],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<DownloadHistoryItem>>(
        '/users/me/downloads/',
        { params: { page, limit } },
      )
      return data
    },
  })
}

export function useArchiveDownload() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (bookId: string) => {
      await apiClient.post(`/users/me/downloads/${bookId}/archive/`)
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['download-history'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}
