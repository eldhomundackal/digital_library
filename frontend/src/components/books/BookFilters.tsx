import { useEffect, useState } from 'react'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import type { BookFilters } from '@/types/book'
import type { CategorySummary, LanguageSummary } from '@/types/common'

interface BookFiltersProps {
  filters: BookFilters
  onChange: (filters: BookFilters) => void
  categories?: CategorySummary[]
  languages?: LanguageSummary[]
}

const sortOptions = [
  { value: '', label: 'Default' },
  { value: 'latest', label: 'Newest' },
  { value: 'popular', label: 'Most Downloaded' },
  { value: 'rating', label: 'Highest Rated' },
]

export function BookFiltersPanel({ filters, onChange, categories = [], languages = [] }: BookFiltersProps) {
  const [search, setSearch] = useState(filters.search ?? '')

  useEffect(() => {
    const t = setTimeout(() => {
      if (search !== filters.search) {
        onChange({ ...filters, search, page: 1 })
      }
    }, 400)
    return () => clearTimeout(t)
  }, [search, filters, onChange])

  return (
    <div className="flex flex-wrap gap-3">
      <Input
        placeholder="Search books…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-48"
      />
      <Select
        options={[{ value: '', label: 'All Categories' }, ...categories.map((c) => ({ value: c.id, label: c.name }))]}
        value={filters.category_id ?? ''}
        onChange={(e) => onChange({ ...filters, category_id: e.target.value ? Number(e.target.value) : undefined, page: 1 })}
        className="w-44"
      />
      <Select
        options={[{ value: '', label: 'All Languages' }, ...languages.map((l) => ({ value: l.id, label: l.name }))]}
        value={filters.language_id ?? ''}
        onChange={(e) => onChange({ ...filters, language_id: e.target.value ? Number(e.target.value) : undefined, page: 1 })}
        className="w-40"
      />
      <Select
        options={sortOptions}
        value={filters.sort_by ?? ''}
        onChange={(e) => onChange({ ...filters, sort_by: (e.target.value as BookFilters['sort_by']) || undefined, page: 1 })}
        className="w-44"
      />
      {(filters.search || filters.category_id || filters.language_id || filters.sort_by) && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => { setSearch(''); onChange({ page: 1, limit: filters.limit }) }}
        >
          Clear
        </Button>
      )}
    </div>
  )
}
