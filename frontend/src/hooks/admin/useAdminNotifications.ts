import { useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { apiClient, getApiError } from '@/api/client'

interface BroadcastPayload {
  title: string
  message: string
  type: string
  target_role?: string
}

export function useBroadcastNotification() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (payload: BroadcastPayload) => {
      await apiClient.post('/admin/notifications/broadcast/', payload)
    },
    onSuccess: () => {
      toast.success('Notification broadcasted.')
      void qc.invalidateQueries({ queryKey: ['notifications'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}
