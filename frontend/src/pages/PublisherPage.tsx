import { useParams } from 'react-router-dom'
import { usePublicPublisherProfile } from '@/hooks/usePublisher'
import { useBooks } from '@/hooks/useBooks'
import { Avatar } from '@/components/ui/Avatar'
import { Badge } from '@/components/ui/Badge'
import { BookGrid } from '@/components/books/BookGrid'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatDate } from '@/utils/formatters'

export default function PublisherPage() {
  const { userId } = useParams<{ userId: string }>()
  const { data: publisher, isLoading } = usePublicPublisherProfile(userId ?? '')
  const { data: books, isLoading: loadingBooks } = useBooks({ limit: 12 })

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-20 w-20 rounded-full" />
          <div><Skeleton className="mb-2 h-6 w-40" /><Skeleton className="h-4 w-24" /></div>
        </div>
      </div>
    )
  }

  if (!publisher) {
    return <div className="flex min-h-[60vh] items-center justify-center text-gray-400">Publisher not found.</div>
  }

  const p = publisher.profile

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      <div className="flex flex-col gap-6 rounded-card border border-gray-200 bg-white p-6 sm:flex-row sm:items-start">
        <Avatar src={p.logo} name={p.display_name} size="xl" />
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="font-heading text-2xl font-bold text-gray-900">{p.display_name}</h1>
            {p.is_verified && <Badge variant="success">Verified</Badge>}
          </div>
          {p.bio && <p className="mt-2 text-gray-600">{p.bio}</p>}
          <div className="mt-3 flex flex-wrap gap-4 text-sm text-gray-500">
            <span>{p.total_books} books</span>
            <span>Joined {formatDate(p.joined_date)}</span>
            {p.website && (
              <a href={p.website} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                Website ↗
              </a>
            )}
          </div>
          {p.social_links && (
            <div className="mt-3 flex gap-3">
              {p.social_links.twitter && (
                <a href={p.social_links.twitter} target="_blank" rel="noopener noreferrer" className="text-sm text-primary hover:underline">Twitter</a>
              )}
              {p.social_links.linkedin && (
                <a href={p.social_links.linkedin} target="_blank" rel="noopener noreferrer" className="text-sm text-primary hover:underline">LinkedIn</a>
              )}
            </div>
          )}
        </div>
      </div>

      <section className="mt-8">
        <h2 className="mb-4 font-heading text-xl font-bold text-gray-900">Books by {p.display_name}</h2>
        <BookGrid books={books?.items} isLoading={loadingBooks} />
      </section>
    </div>
  )
}
