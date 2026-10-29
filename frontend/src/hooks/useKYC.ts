import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import type { KYCResponse } from '@/types/kyc'

export function usePublisherKYC() {
  return useQuery({
    queryKey: ['kyc', 'publisher'],
    queryFn: async () => {
      const { data } = await apiClient.get<KYCResponse>('/kyc/')
      return data
    },
  })
}

export function useSubmitKYC() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (formData: FormData) => {
      const { data } = await apiClient.post<KYCResponse>('/kyc/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['kyc'] })
    },
  })
}

export function useResubmitKYC() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (formData: FormData) => {
      const { data } = await apiClient.put<KYCResponse>('/kyc/resubmit/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['kyc'] })
    },
  })
}
