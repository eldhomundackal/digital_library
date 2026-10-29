import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { usePublisherKYC } from '@/hooks/useKYC'

interface KYCGuardProps {
  children: React.ReactNode
}

export function KYCGuard({ children }: KYCGuardProps) {
  const { user } = useAuthStore()
  const { data: kyc, isLoading } = usePublisherKYC()

  if (!user || user.role !== 'publisher') {
    return <Navigate to="/" replace />
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <span className="text-gray-500">Loading…</span>
      </div>
    )
  }

  if (!kyc || kyc.status !== 'APPROVED') {
    return <Navigate to="/publisher/kyc" replace />
  }

  return <>{children}</>
}
