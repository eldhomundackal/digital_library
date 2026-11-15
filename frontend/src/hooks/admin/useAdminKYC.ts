import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api, apiClient, getApiError } from '@/api/client'
import type { KYCResponse } from '@/types/kyc'
import type { PaginatedResponse } from '@/types/common'

interface KYCListParams {
  page?: number
  limit?: number
  status?: string
}

export function useAdminKYCList(params: KYCListParams = {}) {
  return useQuery({
    queryKey: ['admin', 'kyc', params],
    queryFn: () => api.get<PaginatedResponse<KYCResponse>>('/admin/kyc/', { params }),
  })
}

export function useAdminKYCDetail(kycId: string) {
  return useQuery({
    queryKey: ['admin', 'kyc', kycId],
    queryFn: () => api.get<KYCResponse>(`/admin/kyc/${kycId}/`),
    enabled: !!kycId,
  })
}

export function useApproveKYC() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (kycId: string) => {
      await apiClient.post(`/admin/kyc/${kycId}/approve/`)
    },
    onSuccess: () => {
      toast.success('KYC approved.')
      void qc.invalidateQueries({ queryKey: ['admin', 'kyc'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useRejectKYC() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ kycId, reason }: { kycId: string; reason: string }) => {
      await apiClient.post(`/admin/kyc/${kycId}/reject/`, { reason })
    },
    onSuccess: () => {
      toast.success('KYC rejected.')
      void qc.invalidateQueries({ queryKey: ['admin', 'kyc'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}
