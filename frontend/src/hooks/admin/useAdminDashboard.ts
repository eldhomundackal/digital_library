import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
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
    queryFn: () => api.get<AdminDashboardStats>('/admin/dashboard/stats/'),
  })
}

export function usePendingActions() {
  return useQuery({
    queryKey: ['admin', 'pending-actions'],
    queryFn: () => api.get<PendingAction[]>('/admin/dashboard/pending-actions/'),
  })
}

export function useActivityFeed(page = 1, limit = 20) {
  return useQuery({
    queryKey: ['admin', 'activity', page],
    queryFn: () => api.get<PaginatedResponse<ActivityFeedItem>>('/admin/activity/', { params: { page, limit } }),
  })
}

export function useAuditLog(page = 1, limit = 20) {
  return useQuery({
    queryKey: ['admin', 'audit', page],
    queryFn: () => api.get<PaginatedResponse<AuditLogItem>>('/admin/audit/', { params: { page, limit } }),
  })
}
