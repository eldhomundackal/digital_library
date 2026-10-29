import { create } from 'zustand'
import type { UserSummary } from '@/types/auth'

interface AuthState {
  accessToken: string | null
  user: UserSummary | null
  isAuthenticated: boolean
  setAccessToken: (token: string) => void
  setUser: (user: UserSummary) => void
  logout: () => void
  isReader: () => boolean
  isPublisher: () => boolean
  isStaff: () => boolean
  isAdmin: () => boolean
  isAdminOrStaff: () => boolean
}

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: null,
  user: null,
  isAuthenticated: false,

  setAccessToken: (token) =>
    set({ accessToken: token, isAuthenticated: true }),

  setUser: (user) => set({ user }),

  logout: () =>
    set({ accessToken: null, user: null, isAuthenticated: false }),

  isReader: () => get().user?.role === 'reader',
  isPublisher: () => get().user?.role === 'publisher',
  isStaff: () => get().user?.role === 'staff',
  isAdmin: () => ['admin', 'superadmin'].includes(get().user?.role ?? ''),
  isAdminOrStaff: () =>
    ['staff', 'admin', 'superadmin'].includes(get().user?.role ?? ''),
}))
