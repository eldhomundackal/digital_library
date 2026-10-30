import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import { useAuthStore } from '@/store/authStore'
import type { NotificationListResponse } from '@/types/notification'

interface NotificationParams {
  page?: number
  page_size?: number
  unread_only?: boolean
}

const ADMIN_ROLES = ['staff', 'admin', 'superadmin']

function notificationBase(role: string | undefined): string {
  return ADMIN_ROLES.includes(role ?? '') ? '/admin/notifications' : '/users/me/notifications'
}

export function useNotifications(params: NotificationParams = {}) {
  const user = useAuthStore((s) => s.user)
  const base = notificationBase(user?.role)
  return useQuery({
    queryKey: ['notifications', user?.role, params],
    queryFn: () => api.get<NotificationListResponse>(base, { params }),
    enabled: !!user,
    retry: false,
    throwOnError: false,
  })
}

export function useMarkAllRead() {
  const qc = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const base = notificationBase(user?.role)
  return useMutation({
    mutationFn: () => api.post(`${base}/read-all`),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['notifications'] })
    },
  })
}

export function useMarkNotificationRead() {
  const qc = useQueryClient()
  const user = useAuthStore((s) => s.user)
  const base = notificationBase(user?.role)
  return useMutation({
    mutationFn: (notificationId: string) => api.patch(`${base}/${notificationId}/read`),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ['notifications'] })
    },
  })
}
