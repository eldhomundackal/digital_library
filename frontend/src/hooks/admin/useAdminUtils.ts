import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { apiClient, getApiError } from '@/api/client'
import type { CategorySummary, TagSummary } from '@/types/common'

export function useAdminCategories() {
  return useQuery({
    queryKey: ['admin', 'categories'],
    queryFn: async () => {
      const { data } = await apiClient.get<CategorySummary[]>('/admin/categories/')
      return data
    },
  })
}

export function useCreateCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (name: string) => {
      const { data } = await apiClient.post<CategorySummary>('/admin/categories/', { name })
      return data
    },
    onSuccess: () => {
      toast.success('Category created.')
      void qc.invalidateQueries({ queryKey: ['admin', 'categories'] })
      void qc.invalidateQueries({ queryKey: ['categories'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useDeleteCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (categoryId: number) => {
      await apiClient.delete(`/admin/categories/${categoryId}/`)
    },
    onSuccess: () => {
      toast.success('Category deleted.')
      void qc.invalidateQueries({ queryKey: ['admin', 'categories'] })
      void qc.invalidateQueries({ queryKey: ['categories'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useAdminTags() {
  return useQuery({
    queryKey: ['admin', 'tags'],
    queryFn: async () => {
      const { data } = await apiClient.get<TagSummary[]>('/admin/tags/')
      return data
    },
  })
}

export function useCreateTag() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (name: string) => {
      const { data } = await apiClient.post<TagSummary>('/admin/tags/', { name })
      return data
    },
    onSuccess: () => {
      toast.success('Tag created.')
      void qc.invalidateQueries({ queryKey: ['admin', 'tags'] })
      void qc.invalidateQueries({ queryKey: ['tags'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useDeleteTag() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (tagId: number) => {
      await apiClient.delete(`/admin/tags/${tagId}/`)
    },
    onSuccess: () => {
      toast.success('Tag deleted.')
      void qc.invalidateQueries({ queryKey: ['admin', 'tags'] })
      void qc.invalidateQueries({ queryKey: ['tags'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}
