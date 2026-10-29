import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useDownloadHistory, useDownloadBook, useArchiveDownload } from '@/hooks/useDownloads'
import { Skeleton } from '@/components/ui/Skeleton'
import { Button } from '@/components/ui/Button'
import { formatRelativeTime } from '@/utils/formatters'

export default function LibraryPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useDownloadHistory(page)
  const download = useDownloadBook()
  const archive = useArchiveDownload()

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
      <h1 className="mb-6 font-heading text-2xl font-bold text-gray-900">My Library</h1>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full rounded-card" />
          ))}
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="rounded-card border border-gray-200 bg-white p-12 text-center text-gray-400">
          <p className="text-lg">Your library is empty.</p>
          <Link to="/books" className="mt-3 inline-block text-sm text-primary hover:underline">
            Browse books to download →
          </Link>
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {data.items.map((item) => (
              <div
                key={item.book_id}
                className={`flex items-center gap-4 rounded-card border bg-white p-4 ${item.is_archived ? 'opacity-60' : ''}`}
              >
                {item.thumbnail ? (
                  <img src={item.thumbnail} alt={item.title} className="h-14 w-10 rounded object-cover" />
                ) : (
                  <div className="flex h-14 w-10 items-center justify-center rounded bg-primary/10">
                    <svg className="h-5 w-5 text-primary/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253" />
                    </svg>
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <Link to={`/books/${item.book_id}`} className="font-medium text-gray-900 hover:text-primary line-clamp-1">
                    {item.title}
                  </Link>
                  <p className="text-xs text-gray-400">Downloaded {formatRelativeTime(item.downloaded_at)}</p>
                </div>
                <div className="flex shrink-0 gap-2">
                  {!item.is_archived && (
                    <Button
                      size="sm"
                      onClick={() => download.mutate(item.book_id)}
                      loading={download.isPending}
                    >
                      Re-download
                    </Button>
                  )}
                  {!item.is_archived && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => archive.mutate(item.book_id)}
                    >
                      Archive
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>

          {data.pages > 1 && (
            <div className="mt-6 flex items-center justify-center gap-3">
              <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="rounded-btn border px-3 py-1.5 text-sm disabled:opacity-40">Previous</button>
              <span className="text-sm text-gray-600">Page {page} of {data.pages}</span>
              <button disabled={page >= data.pages} onClick={() => setPage(p => p + 1)} className="rounded-btn border px-3 py-1.5 text-sm disabled:opacity-40">Next</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
