import { useState } from 'react'
import { useAdminKYCList, useApproveKYC, useRejectKYC } from '@/hooks/admin/useAdminKYC'
import { KYCStatusBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatDate } from '@/utils/formatters'

export default function AdminKYCPage() {
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const { data, isLoading } = useAdminKYCList({ status: status || undefined, page, limit: 20 })
  const approve = useApproveKYC()
  const reject = useRejectKYC()
  const [rejectModal, setRejectModal] = useState<{ kycId: string } | null>(null)
  const [reason, setReason] = useState('')

  return (
    <div>
      <h1 className="mb-6 font-heading text-2xl font-bold text-gray-900">KYC Requests</h1>

      <div className="mb-4 flex gap-2">
        {['', 'PENDING', 'APPROVED', 'REJECTED', 'RESUBMITTED'].map((s) => (
          <button
            key={s}
            onClick={() => { setStatus(s); setPage(1) }}
            className={`rounded-pill px-3 py-1 text-sm font-medium transition-colors ${status === s ? 'bg-primary text-white' : 'bg-white border border-gray-300 text-gray-600 hover:border-primary hover:text-primary'}`}
          >
            {s || 'All'}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-2">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-14 w-full rounded-card" />)}</div>
      ) : (
        <div className="overflow-hidden rounded-card border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                {['KYC ID', 'Status', 'Submitted', 'Actions'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data?.items.map((kyc) => (
                <tr key={kyc.kyc_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs text-gray-600">{kyc.kyc_id.slice(0, 8)}…</td>
                  <td className="px-4 py-3"><KYCStatusBadge status={kyc.status} /></td>
                  <td className="px-4 py-3 text-gray-500">{kyc.submitted_at ? formatDate(kyc.submitted_at) : '—'}</td>
                  <td className="px-4 py-3">
                    {(kyc.status === 'PENDING' || kyc.status === 'RESUBMITTED') && (
                      <div className="flex gap-2">
                        <Button size="sm" variant="secondary" loading={approve.isPending} onClick={() => approve.mutate(kyc.kyc_id)}>
                          Approve
                        </Button>
                        <Button size="sm" variant="danger" onClick={() => { setRejectModal({ kycId: kyc.kyc_id }); setReason('') }}>
                          Reject
                        </Button>
                      </div>
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
                <span className="text-xs text-gray-600">{page}/{data.pages}</span>
                <button disabled={page >= data.pages} onClick={() => setPage(p => p + 1)} className="rounded border px-2 py-1 text-xs disabled:opacity-40">Next</button>
              </div>
            </div>
          )}
        </div>
      )}

      <Modal open={!!rejectModal} onClose={() => setRejectModal(null)} title="Reject KYC" size="sm">
        <Input
          label="Rejection reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Explain why the KYC is rejected…"
        />
        <div className="mt-4 flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setRejectModal(null)}>Cancel</Button>
          <Button
            variant="danger"
            disabled={!reason}
            loading={reject.isPending}
            onClick={() => {
              if (rejectModal)
                reject.mutate({ kycId: rejectModal.kycId, reason }, { onSuccess: () => setRejectModal(null) })
            }}
          >
            Reject
          </Button>
        </div>
      </Modal>
    </div>
  )
}
