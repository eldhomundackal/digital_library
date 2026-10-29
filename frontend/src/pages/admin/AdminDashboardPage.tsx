import { Link } from 'react-router-dom'
import { useAdminStats, usePendingActions } from '@/hooks/admin/useAdminDashboard'
import { Skeleton } from '@/components/ui/Skeleton'
import { Button } from '@/components/ui/Button'
import { formatRelativeTime } from '@/utils/formatters'

export default function AdminDashboardPage() {
  const { data: stats, isLoading: loadingStats } = useAdminStats()
  const { data: pending, isLoading: loadingPending } = usePendingActions()

  const statCards = stats ? [
    { label: 'Total Users', value: stats.total_users, to: '/admin/users' },
    { label: 'Total Books', value: stats.total_books, to: '/admin/books' },
    { label: 'Total Downloads', value: stats.total_downloads, to: null },
    { label: 'Active Publishers', value: stats.active_publishers, to: '/admin/users?role=publisher' },
    { label: 'Pending KYC', value: stats.pending_kyc, to: '/admin/kyc' },
    { label: 'Pending Books', value: stats.pending_books, to: '/admin/books?status=PENDING' },
  ] : []

  return (
    <div className="space-y-6">
      <h1 className="font-heading text-2xl font-bold text-gray-900">Dashboard</h1>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        {loadingStats
          ? Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-24 rounded-card" />)
          : statCards.map((s) => (
              <div
                key={s.label}
                className={`rounded-card border border-gray-200 bg-white p-4 ${s.to ? 'cursor-pointer hover:border-primary/40' : ''}`}
                onClick={() => s.to && (window.location.href = s.to)}
              >
                <p className="text-sm text-gray-500">{s.label}</p>
                <p className="mt-1 text-2xl font-bold text-gray-900">{s.value.toLocaleString()}</p>
              </div>
            ))}
      </div>

      {/* Pending actions */}
      <div className="rounded-card border border-gray-200 bg-white">
        <div className="border-b px-5 py-4">
          <h2 className="font-heading text-lg font-semibold text-gray-900">Pending Actions</h2>
        </div>
        {loadingPending ? (
          <div className="p-4 space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}</div>
        ) : !pending?.length ? (
          <p className="p-6 text-center text-gray-400">Nothing pending — all caught up!</p>
        ) : (
          <ul className="divide-y">
            {pending.map((action) => (
              <li key={action.id} className="flex items-center justify-between gap-4 px-5 py-3">
                <div>
                  <p className="font-medium text-gray-900 text-sm">{action.title}</p>
                  <p className="text-xs text-gray-400">
                    {action.type === 'kyc' ? 'KYC' : 'Book'} · by {action.submitted_by} · {formatRelativeTime(action.submitted_at)}
                  </p>
                </div>
                <Link to={action.type === 'kyc' ? `/admin/kyc` : `/admin/books`}>
                  <Button size="sm" variant="outline">Review</Button>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
