import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { apiClient, getApiError } from '@/api/client'
import type { BookReviewsResponse, SubmitReviewRequest } from '@/types/review'

export function useBookReviews(bookId: string, page = 1, limit = 10) {
  return useQuery({
    queryKey: ['reviews', bookId, page],
    queryFn: async () => {
      const { data } = await apiClient.get<BookReviewsResponse>(`/books/${bookId}/reviews/`, {
        params: { page, limit },
      })
      return data
    },
    enabled: !!bookId,
  })
}

export function useSubmitReview(bookId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: SubmitReviewRequest) => {
      await apiClient.post(`/books/${bookId}/reviews/`, payload)
    },
    onSuccess: () => {
      toast.success('Review submitted.')
      void qc.invalidateQueries({ queryKey: ['reviews', bookId] })
      void qc.invalidateQueries({ queryKey: ['book', bookId] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useReplyToReview(bookId: string, reviewId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (comment: string) => {
      await apiClient.post(`/books/${bookId}/reviews/${reviewId}/reply/`, { comment })
    },
    onSuccess: () => {
      toast.success('Reply posted.')
      void qc.invalidateQueries({ queryKey: ['reviews', bookId] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useDeleteReview(bookId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (reviewId: string) => {
      await apiClient.delete(`/books/${bookId}/reviews/${reviewId}/`)
    },
    onSuccess: () => {
      toast.success('Review deleted.')
      void qc.invalidateQueries({ queryKey: ['reviews', bookId] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}
