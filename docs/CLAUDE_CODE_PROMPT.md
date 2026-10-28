# Claude Code — Digital Library Frontend

Paste this entire prompt into Claude Code to start the frontend implementation.

---

## Your task

You are implementing the React frontend for the Digital Library platform.

Before writing any code, read these files in this exact order:

1. `FRONTEND_CLAUDE.md`   — frontend architecture, API integration, auth flow, all patterns
2. `../CLAUDE.md`         — backend API endpoints, request/response shapes, business rules

Do not write a single line of code until you have read both files fully.

---

## Design reference

The completed UI design is here:
```
https://claude.ai/artifact/EpuKeBbsvr2SbgWvbrJCJR
```

It contains 8 screens on a canvas:
- Landing page
- Book listing page (filters + grid)
- Book detail page (cover, rating, reviews, download)
- Login page
- Register page (role selector)
- Publisher dashboard (stats, book table, status tabs)
- Admin dashboard (KPIs, pending actions, activity feed)
- Publisher KYC page (document upload cards, progress steps)

Match every screen pixel-for-pixel:
colors, typography, spacing, component layout, empty states, badge styles.

---

## Design tokens (add to tailwind.config.ts before anything else)

```typescript
colors: {
  primary:         '#1B6B6B',
  'primary-dark':  '#145858',
  'primary-light': '#1B6B6B15',
  accent:          '#E8A838',
  'accent-dark':   '#B8820A',
  'accent-light':  '#E8A83820',
  background:      '#F8F6F2',
  surface:         '#FFFFFF',
  'surface-muted': '#F0EDE8',
  text:            '#1C1C1E',
  'text-secondary':'#3D3D3F',
  muted:           '#6B7280',
  'muted-light':   '#9CA3AF',
  border:          '#E5E0D8',
  success:         '#16A34A',
  'success-light': '#16A34A15',
  danger:          '#DC2626',
  'danger-light':  '#DC262615',
  warning:         '#B8820A',
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
```

Add this Google Fonts link to index.html:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600&display=swap">
```

---

## Backend

FastAPI backend running at:
```
http://localhost:8000/api/v1
```

All 118 endpoints, request shapes, response shapes and business rules
are documented in `../CLAUDE.md`. Read it before wiring any API call.

---

## Execution order

Execute these steps in strict order. Do not skip ahead.

### Step 1 — Scaffold the project

```bash
npm create vite@latest digital-library-fe -- --template react-ts
cd digital-library-fe
npm install
npm install react-router-dom @tanstack/react-query zustand axios \
  react-hook-form @hookform/resolvers zod react-hot-toast \
  lucide-react date-fns react-pdf
npm install -D tailwindcss autoprefixer postcss @types/node
npx tailwindcss init -p
```

### Step 2 — Configure foundations (in this order)

1. `tailwind.config.ts`            — design tokens above + content paths
2. `src/index.css`                 — Tailwind directives only
3. `index.html`                    — Google Fonts link
4. `.env`                          — VITE_API_URL=http://localhost:8000/api/v1
5. `src/api/client.ts`             — Axios instance + interceptors (see FRONTEND_CLAUDE.md)
6. `src/store/authStore.ts`        — Zustand auth store (see FRONTEND_CLAUDE.md)
7. `src/main.tsx`                  — QueryClient + providers
8. `src/types/`                    — TypeScript types (mirror backend schemas exactly)
9. `src/utils/validators.ts`       — Zod schemas for all forms
10. `src/utils/formatters.ts`      — date, number, file size helpers

### Step 3 — Shared components

Build these before any page — pages depend on them:

11. `src/components/ui/Skeleton.tsx`
12. `src/components/ui/Button.tsx`
13. `src/components/ui/Input.tsx`
14. `src/components/ui/Select.tsx`
15. `src/components/ui/Badge.tsx`
16. `src/components/ui/Modal.tsx`
17. `src/components/ui/Avatar.tsx`
18. `src/components/ui/StarRating.tsx`
19. `src/components/ui/OTPInput.tsx`       — 6 digit boxes, auto-advance, paste support
20. `src/components/ui/FileUpload.tsx`     — drag-drop, validation, progress bar
21. `src/components/layout/Navbar.tsx`     — public nav + logged-in nav variants
22. `src/components/layout/PublisherSidebar.tsx`
23. `src/components/layout/AdminSidebar.tsx`
24. `src/components/layout/Footer.tsx`
25. `src/components/guards/AuthGuard.tsx`
26. `src/components/guards/RoleGuard.tsx`
27. `src/components/guards/KYCGuard.tsx`
28. `src/components/books/BookCard.tsx`
29. `src/components/books/BookGrid.tsx`
30. `src/components/books/BookFilters.tsx`
31. `src/components/notifications/NotificationBell.tsx`

### Step 4 — API hooks (read ../CLAUDE.md for each module)

32. `src/api/auth.ts`              + `src/hooks/useAuth.ts`
33. `src/api/books.ts`             + `src/hooks/useBooks.ts`
34. `src/api/users.ts`             + `src/hooks/useUsers.ts`
35. `src/api/kyc.ts`               + `src/hooks/useKYC.ts`
36. `src/api/reviews.ts`           + `src/hooks/useReviews.ts`
37. `src/api/downloads.ts`         + `src/hooks/useDownloads.ts`
38. `src/api/notifications.ts`     + `src/hooks/useNotifications.ts`
39. `src/api/publishers.ts`        + `src/hooks/usePublishers.ts`
40. `src/api/utils.ts`             + `src/hooks/useUtils.ts`
41. `src/api/admin/dashboard.ts`   + `src/hooks/admin/useAdminDashboard.ts`
42. `src/api/admin/books.ts`       + `src/hooks/admin/useAdminBooks.ts`
43. `src/api/admin/kyc.ts`         + `src/hooks/admin/useAdminKYC.ts`
44. `src/api/admin/users.ts`       + `src/hooks/admin/useAdminUsers.ts`
45. `src/api/admin/analytics.ts`   + `src/hooks/admin/useAdminAnalytics.ts`

### Step 5 — Pages (match design exactly)

Public pages:
46. `src/pages/Landing.tsx`
47. `src/pages/BookListing.tsx`
48. `src/pages/BookDetail.tsx`
49. `src/pages/AuthorPage.tsx`
50. `src/pages/PublisherPage.tsx`

Auth pages:
51. `src/pages/auth/Login.tsx`
52. `src/pages/auth/Register.tsx`
53. `src/pages/auth/VerifyEmail.tsx`      — 6-digit OTP flow
54. `src/pages/auth/ForgotPassword.tsx`
55. `src/pages/auth/VerifyResetOTP.tsx`
56. `src/pages/auth/ResetPassword.tsx`

Reader pages:
57. `src/pages/reader/Profile.tsx`        — profile completion progress bar
58. `src/pages/reader/Downloads.tsx`      — download history, archived book notices

Publisher pages:
59. `src/pages/publisher/KYC.tsx`         — document upload cards, step progress
60. `src/pages/publisher/Dashboard.tsx`   — stats, status tabs, book table
61. `src/pages/publisher/UploadBook.tsx`  — two-column form, file upload
62. `src/pages/publisher/EditBook.tsx`
63. `src/pages/publisher/Analytics.tsx`   — line chart, date picker

Admin pages:
64. `src/pages/admin/Dashboard.tsx`       — KPIs, pending actions, activity feed
65. `src/pages/admin/Users.tsx`
66. `src/pages/admin/KYCList.tsx`
67. `src/pages/admin/KYCDetail.tsx`       — document viewer, approve/reject per doc
68. `src/pages/admin/BookApprovals.tsx`
69. `src/pages/admin/Tags.tsx`
70. `src/pages/admin/Categories.tsx`
71. `src/pages/admin/Analytics.tsx`
72. `src/pages/admin/AuditLog.tsx`
73. `src/pages/admin/ActivityFeed.tsx`

Error pages:
74. `src/pages/NotFound.tsx`
75. `src/pages/Forbidden.tsx`

### Step 6 — Router

76. `src/App.tsx`                  — full route tree with guards (see FRONTEND_CLAUDE.md)

### Step 7 — Verify

```bash
npm run dev
```

Check:
- Landing page loads at http://localhost:5173
- Login works and stores token in Zustand
- Book listing fetches from API with filters
- Download button works for logged-in reader
- Publisher cannot access dashboard without KYC approval
- Admin dashboard loads with real data

---

## Absolute rules — never break these

1. Read `FRONTEND_CLAUDE.md` and `../CLAUDE.md` before writing any file
2. Every API call goes through `src/api/client.ts` — never raw axios or fetch
3. Access token lives in Zustand memory only — never localStorage, never sessionStorage
4. Refresh token is HttpOnly cookie only — never touch it in JavaScript
5. Every endpoint path must match `../CLAUDE.md` exactly — never invent endpoints
6. Every request/response field must match backend schemas — never rename fields
7. Every list page needs skeleton loading state — never show blank or spinner
8. Every mutation needs onError with toast — never silently swallow errors
9. Every form uses React Hook Form + Zod — never uncontrolled inputs
10. Every file upload validates type and size client-side before sending
11. Role checks use helper functions from authStore — never compare role strings inline
12. All Tailwind classes use tokens from tailwind.config.ts — no arbitrary values for brand colors
13. No inline styles anywhere — Tailwind only
14. Download URL is used immediately and discarded — never stored anywhere
15. If anything is unclear, write a // QUESTION: comment and stop — never guess

---

## Key business rules (quick reference)

```
Anonymous users    → can browse and view books, cannot download or review
Readers            → can download (max 5/day, 15/month per book) and review
Publishers         → same as reader + can upload books (KYC must be APPROVED first)
Staff / Admin      → cannot download books, manage platform only
Download URL       → pre-signed S3, expires in 10 minutes
OTP                → 6 digits, expires in 10 minutes, max 5 attempts
Refresh token      → 7 days, HttpOnly cookie, path=/api/v1/auth/refresh
Access token       → 15 minutes, Bearer header
Publisher on own book → can comment but CANNOT rate
Archived books     → hidden from all except users who previously downloaded them
```

