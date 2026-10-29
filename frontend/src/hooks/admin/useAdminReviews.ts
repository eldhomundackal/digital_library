import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { apiClient, getApiError } from '@/api/client'
import type { ReviewResponse } from '@/types/review'
import type { PaginatedResponse } from '@/types/common'

interface AdminReviewsParams {
  page?: number
  limit?: number
  book_id?: string
}

export function useAdminReviews(params: AdminReviewsParams = {}) {
  return useQuery({
    queryKey: ['admin', 'reviews', params],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<ReviewResponse>>(
        '/admin/reviews/',
        { params },
      )
      return data
    },
  })
}

export function useAdminDeleteReview() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (reviewId: string) => {
      await apiClient.delete(`/admin/reviews/${reviewId}/`)
    },
    onSuccess: () => {
      toast.success('Review removed.')
      void qc.invalidateQueries({ queryKey: ['admin', 'reviews'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}
