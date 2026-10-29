import { cn } from '@/utils/cn'

type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'muted'

interface BadgeProps {
  variant?: BadgeVariant
  children: React.ReactNode
  className?: string
}

const variantClasses: Record<BadgeVariant, string> = {
  default: 'bg-primary/10 text-primary',
  success: 'bg-green-100 text-green-800',
  warning: 'bg-amber-100 text-amber-800',
  danger: 'bg-red-100 text-red-700',
  info: 'bg-blue-100 text-blue-800',
  muted: 'bg-gray-100 text-gray-600',
}

export function Badge({ variant = 'default', children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-pill px-2.5 py-0.5 text-xs font-medium',
        variantClasses[variant],
        className,
      )}
    >
      {children}
    </span>
  )
}

export function KYCStatusBadge({ status }: { status: string }) {
  const map: Record<string, BadgeVariant> = {
    APPROVED: 'success',
    PENDING: 'warning',
    REJECTED: 'danger',
    RESUBMITTED: 'info',
    INCOMPLETE: 'muted',
  }
  return <Badge variant={map[status] ?? 'muted'}>{status}</Badge>
}

export function BookStatusBadge({ status }: { status: string }) {
  const map: Record<string, BadgeVariant> = {
    APPROVED: 'success',
    PENDING: 'warning',
    REJECTED: 'danger',
    DRAFT: 'muted',
  }
  return <Badge variant={map[status] ?? 'muted'}>{status}</Badge>
}
