import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useNotifications, useMarkAllRead } from '@/hooks/useNotifications'
import { formatRelativeTime } from '@/utils/formatters'

export function NotificationBell() {
  const [open, setOpen] = useState(false)
  const { data, isLoading } = useNotifications({ page: 1, page_size: 10, unread_only: false })
  const markAll = useMarkAllRead()

  const items = data?.items ?? []
  const unreadCount = items.filter((n) => !n.is_read).length

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative rounded-full p-2 text-gray-600 hover:bg-gray-100"
        aria-label="Notifications"
      >
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 rounded-card border border-gray-200 bg-white shadow-lg">
          <div className="flex items-center justify-between border-b px-4 py-3">
            <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
            {unreadCount > 0 && (
              <button
                onClick={() => markAll.mutate()}
                className="text-xs text-primary hover:underline"
              >
                Mark all read
              </button>
            )}
          </div>
          <ul className="max-h-80 overflow-y-auto">
            {isLoading ? (
              <li className="px-4 py-6 text-center text-sm text-gray-400">Loading…</li>
            ) : items.length === 0 ? (
              <li className="px-4 py-6 text-center text-sm text-gray-400">No notifications</li>
            ) : (
              items.map((n) => (
                <li
                  key={n.notification_id}
                  className={`border-b px-4 py-3 text-sm last:border-b-0 ${!n.is_read ? 'bg-primary/5' : ''}`}
                >
                  <p className="font-medium text-gray-800">{n.title}</p>
                  <p className="mt-0.5 text-gray-500">{n.message}</p>
                  <p className="mt-1 text-xs text-gray-400">{formatRelativeTime(n.created_at)}</p>
                </li>
              ))
            )}
          </ul>
          <div className="border-t px-4 py-2">
            <Link
              to="/reader/notifications"
              className="text-xs text-primary hover:underline"
              onClick={() => setOpen(false)}
            >
              View all notifications →
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
