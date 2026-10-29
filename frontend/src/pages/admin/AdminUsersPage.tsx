import { useState } from 'react'
import { useAdminUsers, useDeactivateUser, useReactivateUser } from '@/hooks/admin/useAdminUsers'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatDate } from '@/utils/formatters'

export default function AdminUsersPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const { data, isLoading } = useAdminUsers({ search, page, limit: 20 })
  const deactivate = useDeactivateUser()
  const reactivate = useReactivateUser()

  return (
    <div>
      <h1 className="mb-6 font-heading text-2xl font-bold text-gray-900">Users</h1>

      <div className="mb-4">
        <Input
          placeholder="Search by email…"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          className="max-w-xs"
        />
      </div>

      {isLoading ? (
        <div className="space-y-2">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-14 w-full rounded-card" />)}</div>
      ) : (
        <div className="overflow-hidden rounded-card border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                {['Email', 'Role', 'Status', 'Joined', 'Actions'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data?.items.map((user) => (
                <tr key={user.user_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{user.email}</td>
                  <td className="px-4 py-3"><Badge variant="muted">{user.role}</Badge></td>
                  <td className="px-4 py-3">
                    <Badge variant={user.is_active ? 'success' : 'danger'}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{formatDate(user.created_at)}</td>
                  <td className="px-4 py-3">
                    {user.is_active ? (
                      <Button
                        size="sm"
                        variant="danger"
                        loading={deactivate.isPending}
                        onClick={() => deactivate.mutate(user.user_id)}
                      >
                        Deactivate
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        loading={reactivate.isPending}
                        onClick={() => reactivate.mutate(user.user_id)}
                      >
                        Reactivate
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data && data.pages > 1 && (
            <div className="flex items-center justify-between border-t px-4 py-3">
              <span className="text-xs text-gray-500">{data.total} total</span>
              <div className="flex gap-2">
                <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="rounded border px-2 py-1 text-xs disabled:opacity-40">Prev</button>
                <span className="text-xs text-gray-600">Page {page}/{data.pages}</span>
                <button disabled={page >= data.pages} onClick={() => setPage(p => p + 1)} className="rounded border px-2 py-1 text-xs disabled:opacity-40">Next</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
