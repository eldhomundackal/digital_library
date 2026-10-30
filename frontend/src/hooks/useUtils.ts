import { useQuery } from '@tanstack/react-query'
import { api } from '@/api/client'
import type { CategorySummary, CountrySummary, LanguageSummary, TagSummary } from '@/types/common'

export function useCategories() {
  return useQuery({
    queryKey: ['categories'],
    queryFn: () => api.get<CategorySummary[]>('/categories'),
    staleTime: 30 * 60 * 1000,
  })
}

export function useLanguages() {
  return useQuery({
    queryKey: ['languages'],
    queryFn: () => api.get<LanguageSummary[]>('/utils/languages'),
    staleTime: 30 * 60 * 1000,
  })
}

export function useCountries() {
  return useQuery({
    queryKey: ['countries'],
    queryFn: () => api.get<CountrySummary[]>('/utils/countries'),
    staleTime: 30 * 60 * 1000,
  })
}

export function useTags(search?: string) {
  return useQuery({
    queryKey: ['tags', search],
    queryFn: () => api.get<TagSummary[]>('/tags', { params: search ? { search } : undefined }),
    staleTime: 10 * 60 * 1000,
  })
}
