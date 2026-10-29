import { useState } from 'react'
import { useAdminReviews, useAdminDeleteReview } from '@/hooks/admin/useAdminReviews'
import { StarRating } from '@/components/ui/StarRating'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatDate } from '@/utils/formatters'

export default function AdminReviewsPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useAdminReviews({ page, limit: 20 })
  const del = useAdminDeleteReview()

  return (
    <div>
      <h1 className="mb-6 font-heading text-2xl font-bold text-gray-900">Reviews</h1>

      {isLoading ? (
        <div className="space-y-2">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-14 w-full rounded-card" />)}</div>
      ) : (
        <div className="overflow-hidden rounded-card border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                {['User', 'Rating', 'Comment', 'Date', 'Actions'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data?.items.map((r) => (
                <tr key={r.review_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-700">{r.user.name}</td>
                  <td className="px-4 py-3">
                    {r.rating != null ? <StarRating value={r.rating} readOnly size="sm" /> : '—'}
                  </td>
                  <td className="px-4 py-3 max-w-xs truncate text-gray-600">{r.comment ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-500 whitespace-nowrap">{formatDate(r.created_at)}</td>
                  <td className="px-4 py-3">
                    <Button size="sm" variant="danger" loading={del.isPending} onClick={() => del.mutate(r.review_id)}>Delete</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data && data.pages > 1 && (
            <div className="flex items-center justify-between border-t px-4 py-3">
              <span className="text-xs text-gray-500">{data.total} total</span>
              <div className="flex gap-2">
                <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="rounded border px-2 py-1 text-xs disabled:opacity-40">Prev</button>
                <span className="text-xs text-gray-600">{page}/{data.pages}</span>
                <button disabled={page >= data.pages} onClick={() => setPage(p => p + 1)} className="rounded border px-2 py-1 text-xs disabled:opacity-40">Next</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
