import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { Avatar } from '@/components/ui/Avatar'
import { Button } from '@/components/ui/Button'
import { NotificationBell } from '@/components/notifications/NotificationBell'

export function Navbar() {
  const { user, isAuthenticated, logout, isAdmin, isStaff, isPublisher } = useAuthStore()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  async function handleLogout() {
    await fetch('/api/v1/auth/logout', { method: 'POST', credentials: 'include' }).catch(() => null)
    logout()
    navigate('/')
  }

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `text-sm font-medium transition-colors ${isActive ? 'text-primary' : 'text-gray-700 hover:text-primary'}`

  return (
    <nav className="sticky top-0 z-40 border-b border-gray-200 bg-white shadow-sm">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2">
          <span className="font-heading text-xl font-bold text-primary">Libraflow</span>
        </Link>

        {/* Center links */}
        <div className="hidden items-center gap-6 md:flex">
          <NavLink to="/books" className={navLinkClass}>Browse</NavLink>
          {(isAdmin() || isStaff()) && (
            <NavLink to="/admin" className={navLinkClass}>Admin</NavLink>
          )}
          {isPublisher() && (
            <NavLink to="/publisher" className={navLinkClass}>Publisher</NavLink>
          )}
        </div>

        {/* Right actions */}
        <div className="flex items-center gap-3">
          {isAuthenticated && user ? (
            <>
              <NotificationBell />
              <div className="relative">
                <button
                  onClick={() => setMenuOpen((o) => !o)}
                  className="flex items-center gap-2 rounded-pill px-2 py-1 hover:bg-gray-100"
                >
                  <Avatar name={user.email} size="sm" />
                  <span className="hidden text-sm font-medium text-gray-700 md:block">
                    {user.email.split('@')[0]}
                  </span>
                </button>
                {menuOpen && (
                  <div
                    className="absolute right-0 mt-2 w-48 rounded-card border border-gray-200 bg-white py-1 shadow-lg"
                    onBlur={() => setMenuOpen(false)}
                  >
                    <Link
                      to="/reader/profile"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                      onClick={() => setMenuOpen(false)}
                    >
                      My Profile
                    </Link>
                    <Link
                      to="/reader/library"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                      onClick={() => setMenuOpen(false)}
                    >
                      My Library
                    </Link>
                    <hr className="my-1" />
                    <button
                      onClick={handleLogout}
                      className="block w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-gray-50"
                    >
                      Sign out
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <Button variant="ghost" size="sm" onClick={() => navigate('/login')}>
                Sign in
              </Button>
              <Button size="sm" onClick={() => navigate('/register')}>
                Sign up
              </Button>
            </>
          )}

          {/* Mobile hamburger */}
          <button
            className="rounded p-1 text-gray-600 hover:bg-gray-100 md:hidden"
            onClick={() => setMenuOpen((o) => !o)}
            aria-label="Menu"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile nav */}
      {menuOpen && (
        <div className="border-t border-gray-200 bg-white px-4 py-3 md:hidden">
          <NavLink to="/books" className="block py-2 text-sm text-gray-700" onClick={() => setMenuOpen(false)}>Browse</NavLink>
          {(isAdmin() || isStaff()) && (
            <NavLink to="/admin" className="block py-2 text-sm text-gray-700" onClick={() => setMenuOpen(false)}>Admin</NavLink>
          )}
          {isPublisher() && (
            <NavLink to="/publisher" className="block py-2 text-sm text-gray-700" onClick={() => setMenuOpen(false)}>Publisher</NavLink>
          )}
        </div>
      )}
    </nav>
  )
}
