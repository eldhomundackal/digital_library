import { Link } from 'react-router-dom'
import { usePublisherBooks } from '@/hooks/useBooks'
import { usePublisherProfile } from '@/hooks/usePublisher'
import { usePublisherKYC } from '@/hooks/useKYC'
import { KYCStatusBadge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { Button } from '@/components/ui/Button'
import { formatDate } from '@/utils/formatters'

export default function PublisherDashboardPage() {
  const { data: profile, isLoading: loadingProfile } = usePublisherProfile()
  const { data: books, isLoading: loadingBooks } = usePublisherBooks({ limit: 5 })
  const { data: kyc } = usePublisherKYC()

  if (loadingProfile) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 w-full rounded-card" />
        <Skeleton className="h-64 w-full rounded-card" />
      </div>
    )
  }

  const p = profile?.profile

  return (
    <div className="space-y-6">
      {/* KYC alert */}
      {kyc && kyc.status !== 'APPROVED' && (
        <div className="rounded-card border border-amber-200 bg-amber-50 p-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="font-medium text-amber-900">KYC Verification Required</p>
              <p className="text-sm text-amber-700 mt-0.5">
                Status: <KYCStatusBadge status={kyc.status} />
                {kyc.status === 'REJECTED' && kyc.rejection_reason && (
                  <span className="ml-2">— {kyc.rejection_reason}</span>
                )}
              </p>
            </div>
            <Link to="/publisher/kyc">
              <Button size="sm" variant="secondary">Manage KYC</Button>
            </Link>
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        {[
          { label: 'Total Books', value: p?.total_books ?? 0 },
          { label: 'KYC Status', value: <KYCStatusBadge status={kyc?.status ?? 'INCOMPLETE'} /> },
          { label: 'Verified', value: p?.is_verified ? 'Yes' : 'No' },
        ].map((stat) => (
          <div key={stat.label} className="rounded-card border border-gray-200 bg-white p-4">
            <p className="text-sm text-gray-500">{stat.label}</p>
            <p className="mt-1 text-xl font-bold text-gray-900">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Recent books */}
      <div className="rounded-card border border-gray-200 bg-white">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h2 className="font-heading text-lg font-semibold text-gray-900">Recent Books</h2>
          <Link to="/publisher/books" className="text-sm text-primary hover:underline">View all</Link>
        </div>
        {loadingBooks ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
          </div>
        ) : !books?.items.length ? (
          <div className="p-8 text-center text-gray-400">
            <p>No books yet.</p>
            <Link to="/publisher/books/upload" className="mt-2 inline-block text-sm text-primary hover:underline">Upload your first book →</Link>
          </div>
        ) : (
          <ul className="divide-y">
            {books.items.map((book) => (
              <li key={book.book_id} className="flex items-center justify-between gap-4 px-5 py-3">
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium text-gray-900">{book.title}</p>
                </div>
                <span className="text-xs text-gray-400">{formatDate(book.created_at)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
