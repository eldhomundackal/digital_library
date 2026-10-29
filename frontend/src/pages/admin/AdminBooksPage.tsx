import { useState } from 'react'
import { useAdminBooks, useApproveBook, useRejectBook, useAdminDeleteBook } from '@/hooks/admin/useAdminBooks'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatDate } from '@/utils/formatters'

export default function AdminBooksPage() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)
  const { data, isLoading } = useAdminBooks({ search, status: statusFilter || undefined, page, limit: 20 })
  const approve = useApproveBook()
  const reject = useRejectBook()
  const del = useAdminDeleteBook()
  const [rejectModal, setRejectModal] = useState<{ bookId: string } | null>(null)
  const [reason, setReason] = useState('')

  return (
    <div>
      <h1 className="mb-6 font-heading text-2xl font-bold text-gray-900">Books</h1>

      <div className="mb-4 flex flex-wrap gap-3">
        <Input placeholder="Search…" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1) }} className="w-48" />
        <div className="flex gap-2">
          {['', 'PENDING', 'APPROVED', 'REJECTED', 'DRAFT'].map((s) => (
            <button
              key={s}
              onClick={() => { setStatusFilter(s); setPage(1) }}
              className={`rounded-pill px-3 py-1 text-sm font-medium transition-colors ${statusFilter === s ? 'bg-primary text-white' : 'bg-white border border-gray-300 text-gray-600 hover:border-primary'}`}
            >
              {s || 'All'}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-2">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-14 w-full rounded-card" />)}</div>
      ) : (
        <div className="overflow-hidden rounded-card border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                {['Title', 'Added', 'Actions'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data?.items.map((book) => (
                <tr key={book.book_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900 max-w-xs truncate">{book.title}</td>
                  <td className="px-4 py-3 text-gray-500 whitespace-nowrap">{formatDate(book.created_at)}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <Button size="sm" variant="secondary" loading={approve.isPending} onClick={() => approve.mutate(book.book_id)}>Approve</Button>
                      <Button size="sm" variant="outline" onClick={() => { setRejectModal({ bookId: book.book_id }); setReason('') }}>Reject</Button>
                      <Button size="sm" variant="danger" loading={del.isPending} onClick={() => del.mutate(book.book_id)}>Delete</Button>
                    </div>
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

      <Modal open={!!rejectModal} onClose={() => setRejectModal(null)} title="Reject book" size="sm">
        <Input label="Rejection reason" value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Why is this book rejected?" />
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setRejectModal(null)}>Cancel</Button>
          <Button variant="danger" disabled={!reason} loading={reject.isPending}
            onClick={() => {
              if (rejectModal) reject.mutate({ bookId: rejectModal.bookId, reason }, { onSuccess: () => setRejectModal(null) })
            }}
          >Reject</Button>
        </div>
      </Modal>
    </div>
  )
}
