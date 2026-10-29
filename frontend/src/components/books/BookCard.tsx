import { Link } from 'react-router-dom'
import { StarRating } from '@/components/ui/StarRating'
import { Badge } from '@/components/ui/Badge'
import type { BookListItem } from '@/types/book'

interface BookCardProps {
  book: BookListItem
}

export function BookCard({ book }: BookCardProps) {
  return (
    <Link
      to={`/books/${book.book_id}`}
      className="group flex flex-col overflow-hidden rounded-card bg-white shadow-sm transition-shadow hover:shadow-md"
    >
      <div className="relative overflow-hidden bg-gray-100">
        {book.thumbnail ? (
          <img
            src={book.thumbnail}
            alt={book.title}
            className="h-48 w-full object-cover transition-transform duration-300 group-hover:scale-105"
            loading="lazy"
          />
        ) : (
          <div className="flex h-48 items-center justify-center bg-gradient-to-br from-primary/20 to-primary/5">
            <svg className="h-12 w-12 text-primary/40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
        )}
      </div>
      <div className="flex flex-1 flex-col p-4">
        <h3 className="line-clamp-2 font-heading text-sm font-semibold text-gray-900 group-hover:text-primary">
          {book.title}
        </h3>
        {book.authors && book.authors.length > 0 && (
          <p className="mt-1 text-xs text-gray-500">
            {book.authors.map((a) => a.name).join(', ')}
          </p>
        )}
        <div className="mt-2 flex items-center gap-2">
          <StarRating value={book.average_rating} readOnly size="sm" />
          <span className="text-xs text-gray-400">({book.review_count})</span>
        </div>
        <div className="mt-3 flex flex-wrap gap-1">
          {book.category && (
            <Badge variant="muted">{book.category.name}</Badge>
          )}
          {book.language && (
            <Badge variant="info">{book.language.name}</Badge>
          )}
        </div>
        <p className="mt-2 text-xs text-gray-400">{book.download_count} downloads</p>
      </div>
    </Link>
  )
}
