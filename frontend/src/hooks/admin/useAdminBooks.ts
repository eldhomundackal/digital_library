import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { apiClient, getApiError } from '@/api/client'
import type { BookDetailResponse, BookListItem } from '@/types/book'
import type { PaginatedResponse } from '@/types/common'

interface AdminBooksParams {
  page?: number
  limit?: number
  search?: string
  status?: string
  category_id?: number
}

export function useAdminBooks(params: AdminBooksParams = {}) {
  return useQuery({
    queryKey: ['admin', 'books', params],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<BookListItem>>(
        '/admin/books/',
        { params },
      )
      return data
    },
  })
}

export function useAdminBookDetail(bookId: string) {
  return useQuery({
    queryKey: ['admin', 'book', bookId],
    queryFn: async () => {
      const { data } = await apiClient.get<BookDetailResponse>(`/admin/books/${bookId}/`)
      return data
    },
    enabled: !!bookId,
  })
}

export function useApproveBook() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (bookId: string) => {
      await apiClient.post(`/admin/books/${bookId}/approve/`)
    },
    onSuccess: () => {
      toast.success('Book approved.')
      void qc.invalidateQueries({ queryKey: ['admin', 'books'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useRejectBook() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ bookId, reason }: { bookId: string; reason: string }) => {
      await apiClient.post(`/admin/books/${bookId}/reject/`, { reason })
    },
    onSuccess: () => {
      toast.success('Book rejected.')
      void qc.invalidateQueries({ queryKey: ['admin', 'books'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useAdminDeleteBook() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (bookId: string) => {
      await apiClient.delete(`/admin/books/${bookId}/`)
    },
    onSuccess: () => {
      toast.success('Book deleted.')
      void qc.invalidateQueries({ queryKey: ['admin', 'books'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}
