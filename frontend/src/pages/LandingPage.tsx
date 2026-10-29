import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { BookGrid } from '@/components/books/BookGrid'
import { useBooks } from '@/hooks/useBooks'
import { useCategories } from '@/hooks/useUtils'

export default function LandingPage() {
  const { data: popular, isLoading: loadingPopular } = useBooks({ sort_by: 'popular', limit: 8 })
  const { data: latest, isLoading: loadingLatest } = useBooks({ sort_by: 'latest', limit: 8 })
  const { data: categories } = useCategories()

  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-br from-primary to-primary-dark py-20 text-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <div className="max-w-2xl">
            <h1 className="font-heading text-5xl font-bold leading-tight">
              Discover Your Next Great Read
            </h1>
            <p className="mt-4 text-lg text-white/80">
              Thousands of quality digital books — free to download, curated by publishers worldwide.
            </p>
            <div className="mt-8 flex gap-4">
              <Link to="/books">
                <Button size="lg" variant="secondary">Browse Books</Button>
              </Link>
              <Link to="/register">
                <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/10">
                  Get Started
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Categories */}
      {categories && categories.length > 0 && (
        <section className="bg-background py-10">
          <div className="mx-auto max-w-7xl px-4 sm:px-6">
            <h2 className="mb-5 font-heading text-2xl font-bold text-gray-900">Browse by Category</h2>
            <div className="flex flex-wrap gap-2">
              {categories.map((cat) => (
                <Link
                  key={cat.id}
                  to={`/books?category_id=${cat.id}`}
                  className="rounded-pill border border-primary/20 bg-white px-4 py-2 text-sm font-medium text-primary hover:bg-primary hover:text-white transition-colors"
                >
                  {cat.name}
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Popular books */}
      <section className="py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="font-heading text-2xl font-bold text-gray-900">Most Downloaded</h2>
            <Link to="/books?sort_by=popular" className="text-sm font-medium text-primary hover:underline">
              View all →
            </Link>
          </div>
          <BookGrid books={popular?.items} isLoading={loadingPopular} skeletonCount={8} />
        </div>
      </section>

      {/* Latest books */}
      <section className="bg-background py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="font-heading text-2xl font-bold text-gray-900">New Arrivals</h2>
            <Link to="/books?sort_by=latest" className="text-sm font-medium text-primary hover:underline">
              View all →
            </Link>
          </div>
          <BookGrid books={latest?.items} isLoading={loadingLatest} skeletonCount={8} />
        </div>
      </section>
    </div>
  )
}
