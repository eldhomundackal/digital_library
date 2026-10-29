import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { apiClient, getApiError } from '@/api/client'
import type { PublisherProfileResponse } from '@/types/user'

export function usePublisherProfile() {
  return useQuery({
    queryKey: ['publisher-profile'],
    queryFn: async () => {
      const { data } = await apiClient.get<PublisherProfileResponse>('/publisher/profile/')
      return data
    },
  })
}

export function usePublicPublisherProfile(userId: string) {
  return useQuery({
    queryKey: ['publisher', userId],
    queryFn: async () => {
      const { data } = await apiClient.get<PublisherProfileResponse>(`/publishers/${userId}/`)
      return data
    },
    enabled: !!userId,
  })
}

interface UpdatePublisherProfilePayload {
  display_name?: string
  bio?: string
  website?: string
  social_links?: {
    twitter?: string
    linkedin?: string
    facebook?: string
    instagram?: string
  }
}

export function useUpdatePublisherProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: UpdatePublisherProfilePayload) => {
      const { data } = await apiClient.patch<PublisherProfileResponse>(
        '/publisher/profile/',
        payload,
      )
      return data
    },
    onSuccess: () => {
      toast.success('Profile updated.')
      void qc.invalidateQueries({ queryKey: ['publisher-profile'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useUploadPublisherLogo() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData()
      form.append('logo', file)
      const { data } = await apiClient.post<PublisherProfileResponse>(
        '/publisher/profile/logo/',
        form,
        { headers: { 'Content-Type': 'multipart/form-data' } },
      )
      return data
    },
    onSuccess: () => {
      toast.success('Logo updated.')
      void qc.invalidateQueries({ queryKey: ['publisher-profile'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}
