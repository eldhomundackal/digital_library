import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api, apiClient, getApiError } from '@/api/client'
import type { AdminUserItem } from '@/types/admin'
import type { PaginatedResponse } from '@/types/common'

interface AdminUsersParams {
  page?: number
  limit?: number
  search?: string
  role?: string
  is_active?: boolean
}

export function useAdminUsers(params: AdminUsersParams = {}) {
  return useQuery({
    queryKey: ['admin', 'users', params],
    queryFn: () => api.get<PaginatedResponse<AdminUserItem>>('/admin/users/', { params }),
  })
}

export function useAdminUser(userId: string) {
  return useQuery({
    queryKey: ['admin', 'user', userId],
    queryFn: () => api.get<AdminUserItem>(`/admin/users/${userId}/`),
    enabled: !!userId,
  })
}

export function useDeactivateUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (userId: string) => {
      await apiClient.post(`/admin/users/${userId}/deactivate/`)
    },
    onSuccess: () => {
      toast.success('User deactivated.')
      void qc.invalidateQueries({ queryKey: ['admin', 'users'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useReactivateUser() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (userId: string) => {
      await apiClient.post(`/admin/users/${userId}/reactivate/`)
    },
    onSuccess: () => {
      toast.success('User reactivated.')
      void qc.invalidateQueries({ queryKey: ['admin', 'users'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useChangeUserRole() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ userId, role }: { userId: string; role: string }) => {
      await apiClient.patch(`/admin/users/${userId}/role/`, { role })
    },
    onSuccess: () => {
      toast.success('Role updated.')
      void qc.invalidateQueries({ queryKey: ['admin', 'users'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}
