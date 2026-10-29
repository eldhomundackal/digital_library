import { useState } from 'react'
import { useAuditLog } from '@/hooks/admin/useAdminDashboard'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatDateTime } from '@/utils/formatters'

export default function AdminAuditPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useAuditLog(page, 25)

  return (
    <div>
      <h1 className="mb-6 font-heading text-2xl font-bold text-gray-900">Audit Log</h1>

      {isLoading ? (
        <div className="space-y-2">{Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-14 w-full rounded-card" />)}</div>
      ) : (
        <div className="overflow-hidden rounded-card border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                {['Action', 'Entity', 'Performed by', 'IP', 'Time'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data?.items.map((log) => (
                <tr key={log.audit_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{log.action}</td>
                  <td className="px-4 py-3 text-gray-600">{log.entity_type}</td>
                  <td className="px-4 py-3 text-gray-600">{log.performed_by}</td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{log.ip_address}</td>
                  <td className="px-4 py-3 text-gray-500 whitespace-nowrap">{formatDateTime(log.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {data && data.pages > 1 && (
            <div className="flex items-center justify-between border-t px-4 py-3">
              <span className="text-xs text-gray-500">{data.total} entries</span>
              <div className="flex gap-2">
                <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="rounded border px-2 py-1 text-xs disabled:opacity-40">Prev</button>
                <span className="text-xs text-gray-600">{page}/{data.pages}</span>
                <button disabled={page >= data.pages} onClick={() => setPage(p => p + 1)} className="rounded border px-2 py-1 text-xs disabled:opacity-40">Next</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
