# Digital Library — Frontend Claude Code Instructions

You are implementing the React frontend for the Digital Library platform.
Read this file fully before writing a single line of code.
Also read `../CLAUDE.md` (backend plan) for API endpoint shapes before wiring any API call.

---

## Tech stack

| Concern | Library |
|---|---|
| Framework | React 18 + TypeScript (Vite) |
| Styling | Tailwind CSS (utility only — no CSS files, no inline styles) |
| Routing | React Router v6 |
| Server state | TanStack React Query v5 |
| Client state | Zustand |
| Forms | React Hook Form + Zod validation |
| HTTP client | Axios (configured instance, never raw fetch) |
| File uploads | Axios multipart/form-data |
| PDF preview | react-pdf (PDF.js wrapper) |
| Notifications | react-hot-toast |
| Icons | Lucide React |
| Date formatting | date-fns |
| Testing | Vitest + React Testing Library |

---

## Project structure

```
src/
├── api/                    # All API calls — never call axios directly in components
│   ├── client.ts           # Axios instance, interceptors, token refresh
│   ├── auth.ts             # Auth endpoints
│   ├── books.ts            # Book endpoints
│   ├── kyc.ts              # KYC endpoints
│   ├── users.ts            # User profile endpoints
│   ├── reviews.ts          # Review endpoints
│   ├── downloads.ts        # Download endpoints
│   ├── notifications.ts    # Notification endpoints
│   ├── publishers.ts       # Publisher public endpoints
│   ├── admin/
│   │   ├── users.ts
│   │   ├── books.ts
│   │   ├── kyc.ts
│   │   ├── reviews.ts
│   │   ├── analytics.ts
│   │   └── dashboard.ts
│   └── utils.ts            # Countries, cities, languages
│
├── hooks/                  # React Query hooks — one file per API module
│   ├── useAuth.ts
│   ├── useBooks.ts
│   ├── useKYC.ts
│   ├── useUsers.ts
│   ├── useReviews.ts
│   ├── useDownloads.ts
│   ├── useNotifications.ts
│   ├── usePublishers.ts
│   ├── useUtils.ts
│   └── admin/
│       ├── useAdminBooks.ts
│       ├── useAdminKYC.ts
│       ├── useAdminUsers.ts
│       └── useAdminDashboard.ts
│
├── store/                  # Zustand stores
│   ├── authStore.ts        # Current user, tokens, login/logout
│   └── uiStore.ts          # Sidebar open, modals, toasts
│
├── components/             # Reusable UI components
│   ├── ui/                 # Generic primitives
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Select.tsx
│   │   ├── Badge.tsx
│   │   ├── Modal.tsx
│   │   ├── Skeleton.tsx
│   │   ├── Avatar.tsx
│   │   ├── StarRating.tsx
│   │   ├── OTPInput.tsx
│   │   └── FileUpload.tsx
│   ├── books/
│   │   ├── BookCard.tsx
│   │   ├── BookGrid.tsx
│   │   ├── BookFilters.tsx
│   │   └── VersionSelector.tsx
│   ├── reviews/
│   │   ├── ReviewList.tsx
│   │   ├── ReviewItem.tsx
│   │   └── ReviewForm.tsx
│   ├── notifications/
│   │   └── NotificationBell.tsx
│   ├── layout/
│   │   ├── Navbar.tsx
│   │   ├── PublisherSidebar.tsx
│   │   ├── AdminSidebar.tsx
│   │   └── Footer.tsx
│   └── guards/
│       ├── AuthGuard.tsx
│       ├── RoleGuard.tsx
│       └── KYCGuard.tsx
│
├── pages/
│   ├── Landing.tsx
│   ├── BookListing.tsx
│   ├── BookDetail.tsx
│   ├── AuthorPage.tsx
│   ├── PublisherPage.tsx
│   ├── auth/
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── VerifyEmail.tsx
│   │   ├── ForgotPassword.tsx
│   │   ├── VerifyResetOTP.tsx
│   │   └── ResetPassword.tsx
│   ├── reader/
│   │   ├── Profile.tsx
│   │   └── Downloads.tsx
│   ├── publisher/
│   │   ├── Dashboard.tsx
│   │   ├── KYC.tsx
│   │   ├── UploadBook.tsx
│   │   ├── EditBook.tsx
│   │   └── Analytics.tsx
│   └── admin/
│       ├── Dashboard.tsx
│       ├── Users.tsx
│       ├── KYCList.tsx
│       ├── KYCDetail.tsx
│       ├── BookApprovals.tsx
│       ├── Tags.tsx
│       ├── Categories.tsx
│       ├── Analytics.tsx
│       ├── AuditLog.tsx
│       └── ActivityFeed.tsx
│
├── types/                  # TypeScript types — mirror backend schemas exactly
│   ├── auth.ts
│   ├── book.ts
│   ├── user.ts
│   ├── kyc.ts
│   ├── review.ts
│   ├── download.ts
│   ├── notification.ts
│   └── admin.ts
│
├── utils/
│   ├── formatters.ts       # Date, number, file size formatters
│   └── validators.ts       # Zod schemas for all forms
│
├── App.tsx                 # Router setup
├── main.tsx                # React root, QueryClient, providers
└── tailwind.config.ts      # Design tokens
```

---

## Design tokens — add to tailwind.config.ts FIRST

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary:    '#1B6B6B',
        'primary-dark': '#145858',
        'primary-light': '#1B6B6B15',
        accent:     '#E8A838',
        'accent-dark': '#B8820A',
        'accent-light': '#E8A83820',
        background: '#F8F6F2',
        surface:    '#FFFFFF',
        'surface-muted': '#F0EDE8',
        text:       '#1C1C1E',
        'text-secondary': '#3D3D3F',
        muted:      '#6B7280',
        'muted-light': '#9CA3AF',
        border:     '#E5E0D8',
        success:    '#16A34A',
        'success-light': '#16A34A15',
        danger:     '#DC2626',
        'danger-light': '#DC262615',
        warning:    '#B8820A',
        'warning-light': '#E8A83820',
      },
      fontFamily: {
        heading: ['"Playfair Display"', 'Georgia', 'serif'],
        body:    ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card: '12px',
        btn:  '8px',
        pill: '20px',
      },
    },
  },
  plugins: [],
}

export default config
```

Import Google Fonts in `index.html`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600&display=swap">
```

---

## Axios client setup — `src/api/client.ts`

This is the most critical file. All API calls go through this instance.

```typescript
import axios from 'axios'
import { useAuthStore } from '@/store/authStore'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1',
  withCredentials: true,   // CRITICAL: sends HttpOnly refresh_token cookie
  headers: { 'Content-Type': 'application/json' },
})

// REQUEST interceptor — attach access token
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// RESPONSE interceptor — handle 401, refresh token, retry
let isRefreshing = false
let refreshQueue: Array<(token: string) => void> = []

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true

      if (isRefreshing) {
        // Queue this request until refresh completes
        return new Promise((resolve) => {
          refreshQueue.push((token) => {
            original.headers.Authorization = `Bearer ${token}`
            resolve(apiClient(original))
          })
        })
      }

      isRefreshing = true

      try {
        // Refresh token is in HttpOnly cookie — browser sends it automatically
        const { data } = await apiClient.post('/auth/refresh')
        const newToken = data.data.access_token
        useAuthStore.getState().setAccessToken(newToken)

        // Replay all queued requests
        refreshQueue.forEach((cb) => cb(newToken))
        refreshQueue = []

        original.headers.Authorization = `Bearer ${newToken}`
        return apiClient(original)
      } catch {
        // Refresh failed — log user out
        useAuthStore.getState().logout()
        window.location.href = '/login'
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

// Helper: extract error message from backend ErrorResponse shape
export function getApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.message ?? 'Something went wrong.'
  }
  return 'Something went wrong.'
}
```

---

## Auth store — `src/store/authStore.ts`

```typescript
import { create } from 'zustand'
import type { UserSummary } from '@/types/auth'

interface AuthState {
  accessToken: string | null
  user: UserSummary | null
  isAuthenticated: boolean
  setAccessToken: (token: string) => void
  setUser: (user: UserSummary) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  isAuthenticated: false,

  setAccessToken: (token) =>
    set({ accessToken: token, isAuthenticated: true }),

  setUser: (user) => set({ user }),

  logout: () =>
    set({ accessToken: null, user: null, isAuthenticated: false }),
}))

// Role helpers — use these in components, never compare role strings directly
export const isReader    = (u: UserSummary | null) => u?.role === 'reader'
export const isPublisher = (u: UserSummary | null) => u?.role === 'publisher'
export const isStaff     = (u: UserSummary | null) => u?.role === 'staff'
export const isAdmin     = (u: UserSummary | null) => ['admin','superadmin'].includes(u?.role ?? '')
export const isAdminOrStaff = (u: UserSummary | null) =>
  ['staff','admin','superadmin'].includes(u?.role ?? '')
```

---

## React Query setup — `src/main.tsx`

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,   // 5 minutes
      retry: (failureCount, error) => {
        // Never retry 401/403/404 — they are not transient
        if (axios.isAxiosError(error)) {
          const status = error.response?.status
          if (status === 401 || status === 403 || status === 404) return false
        }
        return failureCount < 2
      },
    },
    mutations: {
      onError: (error) => {
        toast.error(getApiError(error))
      },
    },
  },
})
```

---

## API integration patterns

### Standard GET hook pattern

```typescript
// src/hooks/useBooks.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import type { BookListItem, BookDetailResponse } from '@/types/book'

// Query keys — centralise here, never inline
export const bookKeys = {
  all:    () => ['books'] as const,
  list:   (filters: BookFilters) => ['books', 'list', filters] as const,
  detail: (id: string) => ['books', 'detail', id] as const,
}

export function useBooks(filters: BookFilters) {
  return useQuery({
    queryKey: bookKeys.list(filters),
    queryFn: async () => {
      const { data } = await apiClient.get('/books', { params: filters })
      return data.data as PaginatedResponse<BookListItem>
    },
  })
}

export function useBook(id: string) {
  return useQuery({
    queryKey: bookKeys.detail(id),
    queryFn: async () => {
      const { data } = await apiClient.get(`/books/${id}`)
      return data.data as BookDetailResponse
    },
    enabled: !!id,
  })
}
```

### Mutation pattern (with optimistic update)

```typescript
export function useSubmitReview(bookId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: SubmitReviewRequest) => {
      const { data } = await apiClient.post(`/books/${bookId}/reviews`, payload)
      return data.data
    },
    onSuccess: () => {
      // Invalidate to refetch updated reviews + rating
      queryClient.invalidateQueries({ queryKey: bookKeys.detail(bookId) })
      toast.success('Review submitted.')
    },
  })
}
```

---

## File upload handling

### Book PDF + thumbnail upload

```typescript
// src/api/books.ts
export async function createBook(payload: CreateBookPayload) {
  const form = new FormData()

  // Text fields
  form.append('title',            payload.title)
  form.append('description',      payload.description)
  form.append('category_id',      String(payload.category_id))
  form.append('language_id',      String(payload.language_id))
  form.append('version_label',    payload.version_label)
  if (payload.isbn)            form.append('isbn', payload.isbn)
  if (payload.page_count)      form.append('page_count', String(payload.page_count))
  if (payload.publication_year) form.append('publication_year', String(payload.publication_year))

  // Arrays — append each item individually
  payload.tag_ids.forEach((id) => form.append('tag_ids', String(id)))
  payload.new_tags.forEach((t) => form.append('new_tags', t))

  // Authors — JSON string per item
  payload.authors.forEach((a) => form.append('authors', JSON.stringify(a)))

  // Files
  form.append('thumbnail', payload.thumbnail)
  form.append('pdf_file',  payload.pdf_file)

  const { data } = await apiClient.post('/publisher/books', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: payload.onProgress,  // optional progress callback
  })
  return data.data
}
```

### FileUpload component usage

```typescript
// Always validate before uploading — match backend limits exactly
const LIMITS = {
  book_pdf:   50 * 1024 * 1024,   // 50 MB
  thumbnail:  2  * 1024 * 1024,   // 2 MB
  kyc_doc:    10 * 1024 * 1024,   // 10 MB
  avatar:     2  * 1024 * 1024,   // 2 MB
}

const ALLOWED_TYPES = {
  book_pdf:   ['application/pdf'],
  thumbnail:  ['image/jpeg', 'image/png', 'image/webp'],
  kyc_doc:    ['application/pdf'],
  avatar:     ['image/jpeg', 'image/png', 'image/webp'],
}

export function validateFile(file: File, type: keyof typeof LIMITS): string | null {
  if (!ALLOWED_TYPES[type].includes(file.type)) {
    return `Invalid file type. Accepted: ${ALLOWED_TYPES[type].join(', ')}`
  }
  if (file.size > LIMITS[type]) {
    return `File too large. Max: ${LIMITS[type] / 1024 / 1024} MB`
  }
  return null
}
```

---

## Download flow — the tricky part

Downloads require login, have rate limits and use pre-signed S3 URLs.
Never open the URL directly in a new tab — use the anchor download pattern.

```typescript
// src/hooks/useDownloads.ts
export function useDownloadBook() {
  return useMutation({
    mutationFn: async ({
      bookId,
      versionId,
    }: {
      bookId: string
      versionId?: string
    }) => {
      // Step 1: request the pre-signed URL from backend
      const params = versionId ? { version_id: versionId } : {}
      const { data } = await apiClient.get(`/books/${bookId}/download`, { params })
      return data.data as DownloadResponse
    },

    onSuccess: (data) => {
      // Step 2: trigger browser download via hidden anchor
      const anchor = document.createElement('a')
      anchor.href = data.download_url
      anchor.download = data.book.file_name
      document.body.appendChild(anchor)
      anchor.click()
      document.body.removeChild(anchor)

      toast.success(`Downloading ${data.book.title}`)

      // Step 3: warn if approaching limits
      const { daily_remaining, monthly_remaining } = data.download_limits
      if (daily_remaining <= 1) {
        toast(`${daily_remaining} download remaining today for this book.`, {
          icon: '⚠️',
        })
      } else if (monthly_remaining <= 3) {
        toast(`${monthly_remaining} downloads remaining this month.`, {
          icon: '⚠️',
        })
      }
    },

    onError: (error) => {
      if (axios.isAxiosError(error)) {
        const status = error.response?.status
        const detail = error.response?.data?.errors?.download_limit

        if (status === 429 && detail) {
          if (detail.daily_remaining === 0) {
            toast.error(
              `Daily limit reached. Resets at ${formatTime(detail.daily_resets_at)}.`
            )
          } else if (detail.monthly_remaining === 0) {
            toast.error(
              `Monthly limit reached. Resets ${formatDate(detail.monthly_resets_at)}.`
            )
          } else {
            // Concurrent download lock
            toast.error('An active download session exists. Try again in a few minutes.')
          }
        }
      }
    },
  })
}
```

---

## Auth flow — step by step

### Login

```typescript
// src/hooks/useAuth.ts
export function useLogin() {
  const { setAccessToken, setUser } = useAuthStore()

  return useMutation({
    mutationFn: async (payload: LoginRequest) => {
      // refresh_token is set as HttpOnly cookie by server — not in response body
      const { data } = await apiClient.post('/auth/login', payload)
      return data.data as LoginResponse
    },
    onSuccess: (data) => {
      setAccessToken(data.access_token)
      setUser(data.user)

      // Route based on role + state
      if (data.user.role === 'publisher' && data.user.kyc_status !== 'APPROVED') {
        navigate('/publisher/kyc')
      } else if (data.user.is_first_login && data.user.role === 'reader') {
        navigate('/profile?complete=true')  // show profile completion prompt
      } else if (isAdminOrStaff(data.user)) {
        navigate('/admin')
      } else if (data.user.role === 'publisher') {
        navigate('/publisher/dashboard')
      } else {
        navigate('/')
      }
    },
  })
}
```

### OTP input component — `src/components/ui/OTPInput.tsx`

```typescript
// 6 individual digit boxes with auto-advance and paste support
// Props: length (default 6), onComplete(otp: string)
// Key behaviours:
// - Typing a digit moves focus to next box automatically
// - Backspace clears current box and moves focus to previous
// - Pasting a 6-digit string fills all boxes at once
// - All boxes show error state when parent sets error=true
// - Submit fires onComplete when all 6 digits are filled
```

### Logout

```typescript
export function useLogout() {
  const { logout } = useAuthStore()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      // Server clears the HttpOnly cookie
      await apiClient.post('/auth/logout')
    },
    onSettled: () => {
      // Always clear local state even if server call fails
      logout()
      queryClient.clear()
      navigate('/login')
    },
  })
}
```

---

## Route guards — `src/components/guards/`

### AuthGuard — redirects to login if not authenticated

```typescript
export function AuthGuard({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  return <>{children}</>
}
```

### RoleGuard — shows 403 if wrong role

```typescript
export function RoleGuard({
  roles,
  children,
}: {
  roles: string[]
  children: ReactNode
}) {
  const { user } = useAuthStore()

  if (!user || !roles.includes(user.role)) {
    return <Navigate to="/403" replace />
  }
  return <>{children}</>
}
```

### KYCGuard — redirects publisher to KYC if not approved

```typescript
export function KYCGuard({ children }: { children: ReactNode }) {
  const { user } = useAuthStore()

  if (user?.role === 'publisher' && user.kyc_status !== 'APPROVED') {
    return <Navigate to="/publisher/kyc" replace />
  }
  return <>{children}</>
}
```

### Router setup — `src/App.tsx`

```typescript
<Routes>
  {/* Public */}
  <Route path="/"           element={<Landing />} />
  <Route path="/books"      element={<BookListing />} />
  <Route path="/books/:id"  element={<BookDetail />} />
  <Route path="/authors/:id"    element={<AuthorPage />} />
  <Route path="/publishers/:id" element={<PublisherPage />} />

  {/* Auth */}
  <Route path="/login"           element={<Login />} />
  <Route path="/register"        element={<Register />} />
  <Route path="/verify-email"    element={<VerifyEmail />} />
  <Route path="/forgot-password" element={<ForgotPassword />} />
  <Route path="/reset-password"  element={<ResetPassword />} />

  {/* Reader */}
  <Route element={<AuthGuard><RoleGuard roles={['reader']} /></AuthGuard>}>
    <Route path="/profile"   element={<ReaderProfile />} />
    <Route path="/downloads" element={<Downloads />} />
  </Route>

  {/* Publisher */}
  <Route element={<AuthGuard><RoleGuard roles={['publisher']} /></AuthGuard>}>
    <Route path="/publisher/kyc"         element={<KYC />} />
    <Route element={<KYCGuard />}>
      <Route path="/publisher/dashboard"   element={<PublisherDashboard />} />
      <Route path="/publisher/books/new"   element={<UploadBook />} />
      <Route path="/publisher/books/:id"   element={<EditBook />} />
      <Route path="/publisher/analytics"   element={<Analytics />} />
    </Route>
  </Route>

  {/* Admin / Staff */}
  <Route element={<AuthGuard><RoleGuard roles={['staff','admin','superadmin']} /></AuthGuard>}>
    <Route path="/admin"                 element={<AdminDashboard />} />
    <Route path="/admin/users"           element={<AdminUsers />} />
    <Route path="/admin/kyc"             element={<AdminKYCList />} />
    <Route path="/admin/kyc/:id"         element={<AdminKYCDetail />} />
    <Route path="/admin/books"           element={<AdminBookApprovals />} />
    <Route path="/admin/tags"            element={<AdminTags />} />
    <Route path="/admin/categories"      element={<AdminCategories />} />
    <Route path="/admin/analytics"       element={<AdminAnalytics />} />
    <Route path="/admin/audit-log"       element={<AuditLog />} />
    <Route path="/admin/activity-feed"   element={<ActivityFeed />} />
  </Route>

  {/* Errors */}
  <Route path="/403" element={<Forbidden />} />
  <Route path="*"    element={<NotFound />} />
</Routes>
```

---

## Error handling — per HTTP status code

Handle these in components, never silently swallow errors:

| Status | Meaning | UI behaviour |
|---|---|---|
| 400 | Validation error | Show field-level errors from `errors` object |
| 401 | Unauthenticated | Auto-refresh token; if that fails → redirect to login |
| 403 | Forbidden | Show inline 403 message or redirect to /403 |
| 404 | Not found | Show 404 state inline (not a page redirect) |
| 422 | Unprocessable | Show field errors (same as 400) |
| 429 | Rate limited | Show specific message (download limits, OTP attempts) |
| 500 | Server error | Show generic error toast; log to console |

```typescript
// Helper — extract field errors from backend ErrorResponse
export function getFieldErrors(error: unknown): Record<string, string> {
  if (axios.isAxiosError(error)) {
    const errors = error.response?.data?.errors
    if (errors && typeof errors === 'object') {
      return Object.fromEntries(
        Object.entries(errors).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v])
      )
    }
  }
  return {}
}

// Usage in a form mutation onError:
onError: (error) => {
  const fieldErrors = getFieldErrors(error)
  Object.entries(fieldErrors).forEach(([field, message]) => {
    form.setError(field as keyof FormValues, { message })
  })
}
```

---

## Pagination pattern

```typescript
// All list pages use this pattern
const [page, setPage] = useState(1)
const LIMIT = 20

const { data, isLoading } = useBooks({ page, limit: LIMIT, ...filters })

// data.pages = total pages from backend
// data.total = total records
// data.items = current page records
```

---

## Skeleton loading pattern

Every list and detail page must show skeletons while loading.
Never show a blank page or spinner. Use the `Skeleton` component:

```typescript
// BookGrid skeleton
if (isLoading) {
  return (
    <div className="grid grid-cols-3 gap-6">
      {Array.from({ length: 9 }).map((_, i) => (
        <div key={i} className="rounded-card border border-border overflow-hidden">
          <Skeleton className="h-44 w-full" />
          <div className="p-4 flex flex-col gap-3">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
            <Skeleton className="h-3 w-full" />
          </div>
        </div>
      ))}
    </div>
  )
}
```

---

## Notification bell — `src/components/notifications/NotificationBell.tsx`

```typescript
// Poll for unread count every 30 seconds
// On click: open dropdown showing latest 5 notifications
// Each notification navigates to the relevant page on click
// Mark as read when dropdown item is clicked
// "Mark all as read" button at top of dropdown
// Badge shows unread count (capped at 99+)
// useNotifications() hook fetches from GET /users/me/notifications
```

---

## Protected download button pattern

The download button has three states depending on auth + limits:

```typescript
function DownloadButton({ book }: { book: BookDetailResponse }) {
  const { user } = useAuthStore()
  const { mutate: download, isPending } = useDownloadBook()
  const navigate = useNavigate()

  // Anonymous — prompt login
  if (!user) {
    return (
      <button
        onClick={() => navigate('/login', { state: { from: location } })}
        className="w-full bg-primary text-background py-4 rounded-btn font-semibold flex items-center justify-center gap-2"
      >
        <LogIn size={18} /> Log in to download
      </button>
    )
  }

  // Staff/Admin — cannot download
  if (isAdminOrStaff(user)) {
    return (
      <div className="w-full text-center text-muted text-sm py-4">
        Staff accounts cannot download books.
      </div>
    )
  }

  // Logged-in reader or publisher
  return (
    <button
      onClick={() => download({ bookId: book.book_id })}
      disabled={isPending}
      className="w-full bg-primary text-background py-4 rounded-btn font-semibold flex items-center justify-center gap-2 disabled:opacity-60"
    >
      {isPending ? <Loader2 size={18} className="animate-spin" /> : <Download size={18} />}
      {isPending ? 'Preparing download…' : 'Download PDF'}
    </button>
  )
}
```

---

## Form validation — Zod schemas in `src/utils/validators.ts`

```typescript
import { z } from 'zod'

export const loginSchema = z.object({
  email:    z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
})

export const registerSchema = z.object({
  email:            z.string().email('Enter a valid email'),
  password:         z.string().min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string(),
  first_name:       z.string().min(1, 'First name is required'),
  last_name:        z.string().min(1, 'Last name is required'),
  role:             z.enum(['reader', 'publisher']),
}).refine((d) => d.password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
})

export const reviewSchema = z.object({
  rating:  z.number().min(1).max(5),
  comment: z.string().max(2000).optional(),
})

export const uploadBookSchema = z.object({
  title:            z.string().min(1, 'Title is required'),
  description:      z.string().min(1, 'Description is required'),
  category_id:      z.number({ required_error: 'Select a category' }),
  language_id:      z.number({ required_error: 'Select a language' }),
  version_label:    z.string().min(1, 'Version label is required (e.g. 1.0)'),
  isbn:             z.string().optional(),
  page_count:       z.number().positive().optional(),
  publication_year: z.number().min(1000).max(2100).optional(),
})
```

---

## Environment variables — `.env`

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_APP_NAME=Libraflow
```

---

## Package.json dependencies

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.26.0",
    "@tanstack/react-query": "^5.56.0",
    "zustand": "^4.5.0",
    "axios": "^1.7.0",
    "react-hook-form": "^7.53.0",
    "@hookform/resolvers": "^3.9.0",
    "zod": "^3.23.0",
    "react-hot-toast": "^2.4.0",
    "lucide-react": "^0.439.0",
    "date-fns": "^3.6.0",
    "react-pdf": "^9.1.0"
  },
  "devDependencies": {
    "typescript": "^5.5.0",
    "vite": "^5.4.0",
    "@vitejs/plugin-react": "^4.3.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "vitest": "^2.1.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.5.0"
  }
}
```

---

## Anti-hallucination rules — same as backend

1. **Every API endpoint path must match `../CLAUDE.md` exactly** — do not invent endpoints
2. **Every request/response field must match the backend schemas** — do not rename fields
3. **Never hardcode API URLs** — always use `import.meta.env.VITE_API_URL`
4. **Never store the access token in localStorage** — keep it in Zustand memory only
5. **Never store the refresh token anywhere in JS** — it is HttpOnly cookie only
6. **Never call `axios` directly** — always use the `apiClient` instance
7. **Never skip loading and error states** — every query needs both
8. **Role checks must use the helper functions** from `authStore.ts` — never compare role strings inline
9. **File validation must happen client-side first** before sending to server
10. **Download URL must never be stored** — use it immediately and discard

---

## Self-check before submitting any file

```
✓ Does every API call use apiClient, not raw axios or fetch?
✓ Does every protected page have AuthGuard?
✓ Does every role-restricted page have RoleGuard?
✓ Does every publisher page (except KYC) have KYCGuard?
✓ Does every list page have skeleton loading state?
✓ Does every form have Zod validation via React Hook Form?
✓ Does every mutation handle onError and show a toast?
✓ Does the download flow handle all 429 variants?
✓ Are all Tailwind classes using tokens from tailwind.config.ts?
✓ Are there no inline styles anywhere?
✓ Are there no hardcoded strings that should come from the API?
✓ Does every file upload validate type and size client-side first?
```
