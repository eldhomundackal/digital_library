import { BookCard } from './BookCard'
import { BookCardSkeleton } from '@/components/ui/Skeleton'
import type { BookListItem } from '@/types/book'

interface BookGridProps {
  books?: BookListItem[]
  isLoading?: boolean
  skeletonCount?: number
  emptyMessage?: string
}

export function BookGrid({
  books,
  isLoading,
  skeletonCount = 8,
  emptyMessage = 'No books found.',
}: BookGridProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
        {Array.from({ length: skeletonCount }).map((_, i) => (
          <BookCardSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (!books || books.length === 0) {
    return (
      <div className="flex min-h-40 items-center justify-center text-gray-400">
        {emptyMessage}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
      {books.map((book) => (
        <BookCard key={book.book_id} book={book} />
      ))}
    </div>
  )
}
