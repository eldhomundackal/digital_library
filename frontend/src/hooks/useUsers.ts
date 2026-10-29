import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { apiClient, getApiError } from '@/api/client'
import type { ReaderProfileResponse, UpdateReaderProfileRequest } from '@/types/user'

export function useMyProfile() {
  return useQuery({
    queryKey: ['my-profile'],
    queryFn: async () => {
      const { data } = await apiClient.get<ReaderProfileResponse>('/users/me/')
      return data
    },
  })
}

export function useUpdateProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: UpdateReaderProfileRequest) => {
      const { data } = await apiClient.patch<ReaderProfileResponse>('/users/me/', payload)
      return data
    },
    onSuccess: () => {
      toast.success('Profile updated.')
      void qc.invalidateQueries({ queryKey: ['my-profile'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useUploadAvatar() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData()
      form.append('avatar', file)
      const { data } = await apiClient.post<ReaderProfileResponse>('/users/me/avatar/', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
    onSuccess: () => {
      toast.success('Avatar updated.')
      void qc.invalidateQueries({ queryKey: ['my-profile'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useChangePassword() {
  return useMutation({
    mutationFn: async (payload: {
      current_password: string
      new_password: string
      confirm_password: string
    }) => {
      await apiClient.post('/users/me/change-password/', payload)
    },
    onSuccess: () => toast.success('Password changed.'),
    onError: (err) => toast.error(getApiError(err)),
  })
}
