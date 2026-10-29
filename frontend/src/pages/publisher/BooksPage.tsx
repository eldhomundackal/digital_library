import { useState } from 'react'
import { Link } from 'react-router-dom'
import { usePublisherBooks, useDeleteBook } from '@/hooks/useBooks'
import { BookGrid } from '@/components/books/BookGrid'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'

export default function PublisherBooksPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = usePublisherBooks({ page, limit: 12 })
  const deleteBook = useDeleteBook()
  const [confirmId, setConfirmId] = useState<string | null>(null)

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="font-heading text-2xl font-bold text-gray-900">My Books</h1>
        <Link to="/publisher/books/upload">
          <Button>Upload Book</Button>
        </Link>
      </div>

      <BookGrid books={data?.items} isLoading={isLoading} emptyMessage="You haven't uploaded any books yet." />

      {data && data.pages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-3">
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="rounded-btn border px-3 py-1.5 text-sm disabled:opacity-40">Previous</button>
          <span className="text-sm text-gray-600">Page {page} of {data.pages}</span>
          <button disabled={page >= data.pages} onClick={() => setPage(p => p + 1)} className="rounded-btn border px-3 py-1.5 text-sm disabled:opacity-40">Next</button>
        </div>
      )}

      <Modal
        open={!!confirmId}
        onClose={() => setConfirmId(null)}
        title="Delete book"
        size="sm"
      >
        <p className="text-sm text-gray-700">Are you sure you want to delete this book? This cannot be undone.</p>
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setConfirmId(null)}>Cancel</Button>
          <Button
            variant="danger"
            loading={deleteBook.isPending}
            onClick={() => {
              if (confirmId) deleteBook.mutate(confirmId, { onSuccess: () => setConfirmId(null) })
            }}
          >
            Delete
          </Button>
        </div>
      </Modal>
    </div>
  )
}
