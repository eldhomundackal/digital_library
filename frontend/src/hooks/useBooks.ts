import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { apiClient, getApiError } from '@/api/client'
import type { BookDetailResponse, BookFilters, BookListItem, CreateBookPayload } from '@/types/book'
import type { PaginatedResponse } from '@/types/common'

export function useBooks(filters: BookFilters = {}) {
  return useQuery({
    queryKey: ['books', filters],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<BookListItem>>('/books/', {
        params: filters,
      })
      return data
    },
  })
}

export function useBook(bookId: string) {
  return useQuery({
    queryKey: ['book', bookId],
    queryFn: async () => {
      const { data } = await apiClient.get<BookDetailResponse>(`/books/${bookId}/`)
      return data
    },
    enabled: !!bookId,
  })
}

export function useUploadBook() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: CreateBookPayload) => {
      const form = new FormData()
      form.append('title', payload.title)
      form.append('description', payload.description)
      form.append('category_id', String(payload.category_id))
      form.append('language_id', String(payload.language_id))
      form.append('version_label', payload.version_label)
      if (payload.isbn) form.append('isbn', payload.isbn)
      if (payload.page_count) form.append('page_count', String(payload.page_count))
      if (payload.publication_year) form.append('publication_year', String(payload.publication_year))
      form.append('tag_ids', JSON.stringify(payload.tag_ids))
      form.append('new_tags', JSON.stringify(payload.new_tags))
      form.append('authors', JSON.stringify(payload.authors))
      form.append('thumbnail', payload.thumbnail)
      form.append('pdf_file', payload.pdf_file)
      const { data } = await apiClient.post<BookDetailResponse>('/publisher/books/', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: payload.onProgress,
      })
      return data
    },
    onSuccess: () => {
      toast.success('Book uploaded successfully.')
      void qc.invalidateQueries({ queryKey: ['publisher-books'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function usePublisherBooks(filters: BookFilters = {}) {
  return useQuery({
    queryKey: ['publisher-books', filters],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<BookListItem>>('/publisher/books/', {
        params: filters,
      })
      return data
    },
  })
}

export function useDeleteBook() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (bookId: string) => {
      await apiClient.delete(`/publisher/books/${bookId}/`)
    },
    onSuccess: () => {
      toast.success('Book deleted.')
      void qc.invalidateQueries({ queryKey: ['publisher-books'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}
