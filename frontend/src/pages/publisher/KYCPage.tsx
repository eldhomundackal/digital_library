import { useState } from 'react'
import { usePublisherKYC, useSubmitKYC, useResubmitKYC } from '@/hooks/useKYC'
import { KYCStatusBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { FileUpload } from '@/components/ui/FileUpload'
import { Skeleton } from '@/components/ui/Skeleton'
import { formatDate } from '@/utils/formatters'

export default function KYCPage() {
  const { data: kyc, isLoading } = usePublisherKYC()
  const submit = useSubmitKYC()
  const resubmit = useResubmitKYC()
  const [doc, setDoc] = useState<File | null>(null)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!doc) return
    const form = new FormData()
    form.append('document', doc)
    const fn = kyc?.status === 'REJECTED' ? resubmit : submit
    fn.mutate(form, { onSuccess: () => setDoc(null) })
  }

  if (isLoading) {
    return <Skeleton className="h-48 w-full rounded-card" />
  }

  const canSubmit = !kyc || kyc.status === 'INCOMPLETE' || kyc.status === 'REJECTED'
  const isPending = submit.isPending || resubmit.isPending

  return (
    <div className="max-w-xl">
      <h1 className="mb-6 font-heading text-2xl font-bold text-gray-900">KYC Verification</h1>

      {kyc && (
        <div className="mb-6 rounded-card border border-gray-200 bg-white p-5">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-gray-700">Status:</span>
            <KYCStatusBadge status={kyc.status} />
          </div>
          {kyc.submitted_at && (
            <p className="mt-2 text-sm text-gray-500">Submitted {formatDate(kyc.submitted_at)}</p>
          )}
          {kyc.rejection_reason && (
            <div className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              <strong>Rejection reason:</strong> {kyc.rejection_reason}
            </div>
          )}
          {kyc.status === 'APPROVED' && (
            <p className="mt-3 text-sm text-green-700">
              Your KYC has been approved. You can now upload books.
            </p>
          )}
        </div>
      )}

      {canSubmit && (
        <form onSubmit={handleSubmit} className="rounded-card border border-gray-200 bg-white p-5">
          <h2 className="mb-4 font-heading text-lg font-semibold text-gray-900">
            {kyc?.status === 'REJECTED' ? 'Resubmit Documents' : 'Submit KYC Documents'}
          </h2>
          <p className="mb-4 text-sm text-gray-500">
            Upload a government-issued ID, business registration, or other identity proof.
          </p>
          <FileUpload
            type="kyc_doc"
            label="KYC Document"
            hint="PDF — max 10MB"
            value={doc}
            onChange={setDoc}
          />
          <div className="mt-4 flex justify-end">
            <Button type="submit" loading={isPending} disabled={!doc}>
              {kyc?.status === 'REJECTED' ? 'Resubmit' : 'Submit for Review'}
            </Button>
          </div>
        </form>
      )}

      {kyc?.status === 'PENDING' && (
        <div className="rounded-card border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          Your documents are under review. We'll notify you once the review is complete.
        </div>
      )}
    </div>
  )
}
