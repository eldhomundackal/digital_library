import { NavLink } from 'react-router-dom'
import { cn } from '@/utils/cn'
import { useAuthStore } from '@/store/authStore'

const links = [
  { to: '/admin', label: 'Dashboard', end: true },
  { to: '/admin/users', label: 'Users' },
  { to: '/admin/books', label: 'Books' },
  { to: '/admin/kyc', label: 'KYC Requests' },
  { to: '/admin/reviews', label: 'Reviews' },
  { to: '/admin/categories', label: 'Categories' },
  { to: '/admin/tags', label: 'Tags' },
  { to: '/admin/authors', label: 'Authors' },
  { to: '/admin/analytics', label: 'Analytics' },
  { to: '/admin/audit', label: 'Audit Log' },
  { to: '/admin/notifications', label: 'Notifications' },
]

export function AdminSidebar() {
  const { isAdmin } = useAuthStore()

  return (
    <aside className="w-56 shrink-0">
      <nav className="sticky top-20 rounded-card border border-gray-200 bg-white p-2">
        <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-gray-400">
          {isAdmin() ? 'Admin' : 'Staff'}
        </p>
        <ul className="space-y-0.5">
          {links.map(({ to, label, end }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={end}
                className={({ isActive }) =>
                  cn(
                    'block rounded-btn px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary text-white'
                      : 'text-gray-700 hover:bg-gray-100',
                  )
                }
              >
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  )
}
