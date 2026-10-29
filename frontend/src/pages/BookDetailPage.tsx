import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useBook } from '@/hooks/useBooks'
import { useBookReviews, useSubmitReview } from '@/hooks/useReviews'
import { useDownloadBook } from '@/hooks/useDownloads'
import { useAuthStore } from '@/store/authStore'
import { Skeleton } from '@/components/ui/Skeleton'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { StarRating } from '@/components/ui/StarRating'
import { ReviewCard } from '@/components/reviews/ReviewCard'
import { formatDate } from '@/utils/formatters'

export default function BookDetailPage() {
  const { bookId } = useParams<{ bookId: string }>()
  const { data: book, isLoading } = useBook(bookId ?? '')
  const { data: reviews } = useBookReviews(bookId ?? '')
  const { isAuthenticated } = useAuthStore()
  const download = useDownloadBook()
  const submitReview = useSubmitReview(bookId ?? '')
  const [rating, setRating] = useState(0)
  const [comment, setComment] = useState('')

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <div className="flex gap-8">
          <Skeleton className="h-64 w-48 shrink-0 rounded-card" />
          <div className="flex-1">
            <Skeleton className="mb-3 h-8 w-2/3" />
            <Skeleton className="mb-2 h-5 w-1/3" />
            <Skeleton className="mb-4 h-4 w-1/4" />
            <Skeleton className="h-24 w-full" />
          </div>
        </div>
      </div>
    )
  }

  if (!book) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-gray-400">
        Book not found.
      </div>
    )
  }

  function handleSubmitReview(e: React.FormEvent) {
    e.preventDefault()
    if (!rating) return
    submitReview.mutate({ rating, comment: comment || undefined }, {
      onSuccess: () => { setRating(0); setComment('') },
    })
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      {/* Book header */}
      <div className="flex flex-col gap-8 md:flex-row">
        <div className="shrink-0">
          {book.thumbnail ? (
            <img
              src={book.thumbnail}
              alt={book.title}
              className="h-72 w-52 rounded-card object-cover shadow-md"
            />
          ) : (
            <div className="flex h-72 w-52 items-center justify-center rounded-card bg-gradient-to-br from-primary/20 to-primary/5">
              <svg className="h-16 w-16 text-primary/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
          )}
        </div>

        <div className="flex-1">
          <h1 className="font-heading text-3xl font-bold text-gray-900">{book.title}</h1>

          {book.authors.length > 0 && (
            <p className="mt-2 text-gray-600">
              by{' '}
              {book.authors.map((a, i) => (
                <span key={a.author_id}>
                  {i > 0 && ', '}
                  <Link to={`/authors/${a.author_id}`} className="font-medium text-primary hover:underline">
                    {a.name}
                  </Link>
                </span>
              ))}
            </p>
          )}

          <div className="mt-3 flex items-center gap-3">
            <StarRating value={book.average_rating} readOnly />
            <span className="text-sm text-gray-500">({book.review_count} reviews)</span>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <Badge variant="muted">{book.category.name}</Badge>
            <Badge variant="info">{book.language.name}</Badge>
            {book.tags.map((t) => (
              <Badge key={t.id} variant="default">{t.name}</Badge>
            ))}
          </div>

          <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
            {book.publication_year && (
              <>
                <dt className="text-gray-500">Published</dt>
                <dd className="text-gray-800">{book.publication_year}</dd>
              </>
            )}
            {book.page_count && (
              <>
                <dt className="text-gray-500">Pages</dt>
                <dd className="text-gray-800">{book.page_count}</dd>
              </>
            )}
            {book.isbn && (
              <>
                <dt className="text-gray-500">ISBN</dt>
                <dd className="text-gray-800">{book.isbn}</dd>
              </>
            )}
            <dt className="text-gray-500">Downloads</dt>
            <dd className="text-gray-800">{book.download_count}</dd>
          </dl>

          <div className="mt-6">
            {isAuthenticated ? (
              <Button
                onClick={() => download.mutate(book.book_id)}
                loading={download.isPending}
                size="lg"
              >
                Download PDF
              </Button>
            ) : (
              <Link to="/login">
                <Button size="lg">Sign in to Download</Button>
              </Link>
            )}
          </div>

          <p className="mt-2 text-xs text-gray-400">
            Published by{' '}
            <Link to={`/publishers/${book.publisher.user_id}`} className="text-primary hover:underline">
              {book.publisher.display_name}
            </Link>
            {' · '}Added {formatDate(book.created_at)}
          </p>
        </div>
      </div>

      {/* Description */}
      <section className="mt-10">
        <h2 className="mb-3 font-heading text-xl font-bold text-gray-900">About this book</h2>
        <p className="whitespace-pre-wrap text-gray-700 leading-relaxed">{book.description}</p>
      </section>

      {/* Reviews */}
      <section className="mt-10">
        <h2 className="mb-4 font-heading text-xl font-bold text-gray-900">
          Reviews ({book.review_count})
        </h2>

        {isAuthenticated && (
          <form onSubmit={handleSubmitReview} className="mb-6 rounded-card border border-gray-200 bg-white p-4">
            <p className="mb-2 text-sm font-medium text-gray-700">Leave a review</p>
            <StarRating value={rating} onChange={setRating} size="lg" className="mb-3" />
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Share your thoughts (optional)…"
              className="w-full rounded-btn border border-gray-300 px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              rows={3}
            />
            <div className="mt-3 flex justify-end">
              <Button type="submit" loading={submitReview.isPending} disabled={!rating}>
                Submit Review
              </Button>
            </div>
          </form>
        )}

        {reviews?.reviews && reviews.reviews.length > 0 ? (
          <div className="space-y-4">
            {reviews.reviews.map((r) => (
              <ReviewCard key={r.review_id} review={r} />
            ))}
          </div>
        ) : (
          <p className="text-gray-400">No reviews yet. Be the first!</p>
        )}
      </section>
    </div>
  )
}
