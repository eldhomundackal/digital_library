import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import type {
  ActivityFeedItem,
  AdminDashboardStats,
  AuditLogItem,
  PendingAction,
} from '@/types/admin'
import type { PaginatedResponse } from '@/types/common'

export function useAdminStats() {
  return useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: async () => {
      const { data } = await apiClient.get<AdminDashboardStats>('/admin/dashboard/stats/')
      return data
    },
  })
}

export function usePendingActions() {
  return useQuery({
    queryKey: ['admin', 'pending-actions'],
    queryFn: async () => {
      const { data } = await apiClient.get<PendingAction[]>('/admin/dashboard/pending-actions/')
      return data
    },
  })
}

export function useActivityFeed(page = 1, limit = 20) {
  return useQuery({
    queryKey: ['admin', 'activity', page],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<ActivityFeedItem>>(
        '/admin/activity/',
        { params: { page, limit } },
      )
      return data
    },
  })
}

export function useAuditLog(page = 1, limit = 20) {
  return useQuery({
    queryKey: ['admin', 'audit', page],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<AuditLogItem>>(
        '/admin/audit/',
        { params: { page, limit } },
      )
      return data
    },
  })
}
