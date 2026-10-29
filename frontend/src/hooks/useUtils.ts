import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import type { CategorySummary, CountrySummary, LanguageSummary, TagSummary } from '@/types/common'

export function useCategories() {
  return useQuery({
    queryKey: ['categories'],
    queryFn: async () => {
      const { data } = await apiClient.get<CategorySummary[]>('/utils/categories/')
      return data
    },
    staleTime: 30 * 60 * 1000,
  })
}

export function useLanguages() {
  return useQuery({
    queryKey: ['languages'],
    queryFn: async () => {
      const { data } = await apiClient.get<LanguageSummary[]>('/utils/languages/')
      return data
    },
    staleTime: 30 * 60 * 1000,
  })
}

export function useCountries() {
  return useQuery({
    queryKey: ['countries'],
    queryFn: async () => {
      const { data } = await apiClient.get<CountrySummary[]>('/utils/countries/')
      return data
    },
    staleTime: 30 * 60 * 1000,
  })
}

export function useTags(search?: string) {
  return useQuery({
    queryKey: ['tags', search],
    queryFn: async () => {
      const { data } = await apiClient.get<TagSummary[]>('/utils/tags/', {
        params: search ? { search } : undefined,
      })
      return data
    },
    staleTime: 10 * 60 * 1000,
  })
}
