import { useState } from 'react'
import { useAdminCategories, useCreateCategory, useDeleteCategory } from '@/hooks/admin/useAdminUtils'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'

export default function AdminCategoriesPage() {
  const { data, isLoading } = useAdminCategories()
  const create = useCreateCategory()
  const del = useDeleteCategory()
  const [name, setName] = useState('')

  function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    create.mutate(name.trim(), { onSuccess: () => setName('') })
  }

  return (
    <div className="max-w-xl">
      <h1 className="mb-6 font-heading text-2xl font-bold text-gray-900">Categories</h1>

      <form onSubmit={handleCreate} className="mb-6 flex gap-3">
        <Input
          placeholder="New category name…"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="flex-1"
        />
        <Button type="submit" loading={create.isPending} disabled={!name.trim()}>Add</Button>
      </form>

      {isLoading ? (
        <div className="space-y-2">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10 w-full rounded-card" />)}</div>
      ) : (
        <ul className="divide-y rounded-card border border-gray-200 bg-white">
          {data?.map((cat) => (
            <li key={cat.id} className="flex items-center justify-between px-4 py-3">
              <span className="font-medium text-gray-900">{cat.name}</span>
              <Button size="sm" variant="danger" loading={del.isPending} onClick={() => del.mutate(cat.id)}>
                Delete
              </Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
