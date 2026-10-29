import { useNotifications, useMarkAllRead, useMarkNotificationRead } from '@/hooks/useNotifications'
import { Skeleton } from '@/components/ui/Skeleton'
import { Button } from '@/components/ui/Button'
import { formatRelativeTime } from '@/utils/formatters'

export default function NotificationsPage() {
  const { data, isLoading } = useNotifications({ page: 1, page_size: 50 })
  const markAll = useMarkAllRead()
  const markOne = useMarkNotificationRead()

  const items = data?.items ?? []
  const unreadCount = data?.unread_count ?? 0

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="font-heading text-2xl font-bold text-gray-900">
          Notifications {unreadCount > 0 && <span className="ml-2 text-base font-normal text-gray-400">({unreadCount} unread)</span>}
        </h1>
        {unreadCount > 0 && (
          <Button variant="ghost" size="sm" onClick={() => markAll.mutate()} loading={markAll.isPending}>
            Mark all read
          </Button>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-16 w-full rounded-card" />)}
        </div>
      ) : items.length === 0 ? (
        <div className="rounded-card border border-gray-200 bg-white p-12 text-center text-gray-400">
          No notifications yet.
        </div>
      ) : (
        <ul className="space-y-2">
          {items.map((n) => (
            <li
              key={n.notification_id}
              className={`rounded-card border p-4 ${!n.is_read ? 'border-primary/20 bg-primary/5' : 'border-gray-200 bg-white'}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{n.title}</p>
                  <p className="mt-0.5 text-sm text-gray-600">{n.message}</p>
                  <p className="mt-1 text-xs text-gray-400">{formatRelativeTime(n.created_at)}</p>
                </div>
                {!n.is_read && (
                  <button
                    onClick={() => markOne.mutate(n.notification_id)}
                    className="shrink-0 text-xs text-primary hover:underline"
                  >
                    Mark read
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
