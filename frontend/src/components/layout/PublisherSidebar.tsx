import { NavLink } from 'react-router-dom'
import { cn } from '@/utils/cn'

const links = [
  { to: '/publisher', label: 'Dashboard', end: true },
  { to: '/publisher/books', label: 'My Books' },
  { to: '/publisher/books/upload', label: 'Upload Book' },
  { to: '/publisher/kyc', label: 'KYC Verification' },
  { to: '/publisher/profile', label: 'Profile' },
]

export function PublisherSidebar() {
  return (
    <aside className="w-56 shrink-0">
      <nav className="sticky top-20 rounded-card border border-gray-200 bg-white p-2">
        <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-gray-400">
          Publisher
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
