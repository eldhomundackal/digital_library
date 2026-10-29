import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

type Role = 'reader' | 'publisher' | 'staff' | 'admin' | 'superadmin'

interface RoleGuardProps {
  children: React.ReactNode
  roles: Role[]
  fallback?: string
}

export function RoleGuard({ children, roles, fallback = '/' }: RoleGuardProps) {
  const { user } = useAuthStore()

  if (!user || !roles.includes(user.role as Role)) {
    return <Navigate to={fallback} replace />
  }

  return <>{children}</>
}
