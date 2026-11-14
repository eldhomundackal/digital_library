import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api, getApiError } from '@/api/client'
import type { CategorySummary, TagSummary } from '@/types/common'

export function useAdminCategories() {
  return useQuery({
    queryKey: ['admin', 'categories'],
    queryFn: () => api.get<CategorySummary[]>('/admin/categories/'),
  })
}

export function useCreateCategory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => api.post<CategorySummary>('/admin/categories/', { name }),
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
    mutationFn: (categoryId: string) => api.delete(`/admin/categories/${categoryId}/`),
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
    queryFn: () => api.get<TagSummary[]>('/admin/tags/'),
  })
}

export function useCreateTag() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => api.post<TagSummary>('/admin/tags/', { name }),
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
    mutationFn: (tagId: string) => api.delete(`/admin/tags/${tagId}/`),
    onSuccess: () => {
      toast.success('Tag deleted.')
      void qc.invalidateQueries({ queryKey: ['admin', 'tags'] })
      void qc.invalidateQueries({ queryKey: ['tags'] })
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}
