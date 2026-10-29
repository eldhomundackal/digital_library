import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { BookGrid } from '@/components/books/BookGrid'
import { BookFiltersPanel } from '@/components/books/BookFilters'
import { useBooks } from '@/hooks/useBooks'
import { useCategories, useLanguages } from '@/hooks/useUtils'
import type { BookFilters } from '@/types/book'

export default function BookListingPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [filters, setFilters] = useState<BookFilters>({
    search: searchParams.get('search') ?? undefined,
    category_id: searchParams.get('category_id') ? Number(searchParams.get('category_id')) : undefined,
    language_id: searchParams.get('language_id') ? Number(searchParams.get('language_id')) : undefined,
    sort_by: (searchParams.get('sort_by') as BookFilters['sort_by']) ?? undefined,
    page: 1,
    limit: 20,
  })

  const { data, isLoading } = useBooks(filters)
  const { data: categories } = useCategories()
  const { data: languages } = useLanguages()

  function handleFilterChange(next: BookFilters) {
    setFilters(next)
    const params: Record<string, string> = {}
    if (next.search) params.search = next.search
    if (next.category_id) params.category_id = String(next.category_id)
    if (next.language_id) params.language_id = String(next.language_id)
    if (next.sort_by) params.sort_by = next.sort_by
    setSearchParams(params)
  }

  const totalPages = data?.pages ?? 1
  const currentPage = filters.page ?? 1

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      <h1 className="mb-6 font-heading text-3xl font-bold text-gray-900">Browse Books</h1>

      <div className="mb-6">
        <BookFiltersPanel
          filters={filters}
          onChange={handleFilterChange}
          categories={categories}
          languages={languages}
        />
      </div>

      {data && (
        <p className="mb-4 text-sm text-gray-500">
          {data.total} book{data.total !== 1 ? 's' : ''} found
        </p>
      )}

      <BookGrid books={data?.items} isLoading={isLoading} />

      {totalPages > 1 && (
        <div className="mt-8 flex items-center justify-center gap-2">
          <button
            disabled={currentPage <= 1}
            onClick={() => handleFilterChange({ ...filters, page: currentPage - 1 })}
            className="rounded-btn border px-3 py-1.5 text-sm disabled:opacity-40"
          >
            Previous
          </button>
          <span className="text-sm text-gray-600">
            Page {currentPage} of {totalPages}
          </span>
          <button
            disabled={currentPage >= totalPages}
            onClick={() => handleFilterChange({ ...filters, page: currentPage + 1 })}
            className="rounded-btn border px-3 py-1.5 text-sm disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
